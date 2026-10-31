import os
import io
import datetime
from fastapi import FastAPI, HTTPException, Body, Response, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.database import db
from app.engine import engine
from app.inkloom_engine import inkloom_engine
from app.pdf_generator import generate_round2_submission_pdf, generate_audit_certificate_pdf
from app.pdf_generator_r3 import generate_round3_submission_pdf
from app.vision_inspector import vision_inspector
from app.rag_engine import rag_engine
from app.cms_simulator import cms_simulator
from app.test_suite import reliability_test_suite

app = FastAPI(
    title="TechFusion — Intelligent Brand Governance API (Round 3 Finish)",
    description="Multi-Modal Vision Inspection, Vector Semantic RAG, In-Context CMS Guardrails, and Editorial Approvals.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class AuditRequest(BaseModel):
    title: Optional[str] = "Untitled Content"
    content: str
    metadata: Optional[Dict[str, Any]] = None

class GuidelineModel(BaseModel):
    id: str
    category: str
    name: str
    description: str
    rules: List[str]
    severity: str = "warning"
    version: str = "v1.0"
    status: str = "active"

class FactModel(BaseModel):
    id: str
    topic: str
    verified_claim: str
    keywords: List[str]
    approved_by: str
    last_verified: str
    evidence_doc: str

class WorkflowActionModel(BaseModel):
    action: str  # APPROVE, REQUEST_CHANGES, OVERRIDE
    role: str
    user_name: str
    note: Optional[str] = ""
    override_reason: Optional[str] = None

class CommentModel(BaseModel):
    author: str
    role: str
    text: str

class RAGSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class RAGIngestRequest(BaseModel):
    title: str
    category: str
    content: str
    source: str

class CMSCheckRequest(BaseModel):
    text: str
    platform: Optional[str] = "google_docs"
    element_type: Optional[str] = "body"

class InkloomPredictRequest(BaseModel):
    text: str

class InkloomBatchRequest(BaseModel):
    texts: List[str]

# ==================== Core Review & Guidelines ====================

@app.post("/api/audit")
def audit_content(req: AuditRequest):
    if not req.content or not req.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty.")
    result = engine.review_content(req.content, req.title, req.metadata)
    
    # Grounding check via RAG: retrieve matching verified facts/guidelines
    try:
        rag_hits = rag_engine.search(req.content[:300], top_k=2)
        result["semantic_rag_context"] = rag_hits
    except Exception:
        result["semantic_rag_context"] = []

    # Inkloom AI Neural Model Evaluation
    try:
        inkloom_res = inkloom_engine.analyze_content(req.content)
        result["inkloom_ai_analysis"] = inkloom_res
        
        # Merge sentence-level ML findings if high-risk drift detected
        if inkloom_res.get("ml_findings"):
            for ml_f in inkloom_res["ml_findings"]:
                # Ensure no duplicate overlap with lexical findings
                if not any(f.get("flagged_text", "").lower() in ml_f["flagged_text"].lower() or 
                           ml_f["flagged_text"].lower() in f.get("flagged_text", "").lower() 
                           for f in result["findings"]):
                    result["findings"].append(ml_f)
            result["findings_count"] = len(result["findings"])
    except Exception as e:
        result["inkloom_ai_analysis"] = {
            "overall_classification": "GOOD",
            "overall_confidence": 1.0,
            "status": f"Fallback/Warning: {e}"
        }
        
    return result

@app.get("/api/guidelines")
def get_guidelines():
    return db.get_guidelines()

@app.post("/api/guidelines")
def create_guideline(gl: GuidelineModel):
    created = db.add_guideline(gl.dict())
    return {"status": "success", "guideline": created}

@app.get("/api/facts")
def get_facts():
    return db.get_facts()

@app.post("/api/facts")
def create_fact(fact: FactModel):
    created = db.add_fact(fact.dict())
    return {"status": "success", "fact": created}

@app.get("/api/drafts")
def list_drafts():
    return db.get_drafts()

@app.get("/api/drafts/{draft_id}")
def get_draft(draft_id: str):
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@app.post("/api/drafts")
def save_draft(payload: Dict[str, Any] = Body(...)):
    draft_id = payload.get("id") or f"DRAFT-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    title = payload.get("title", "Untitled Draft")
    content = payload.get("content", "")
    author = payload.get("author", "Yash Singhla")
    
    audit_res = engine.review_content(content, title)
    draft = db.get_draft(draft_id)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if draft:
        draft["title"] = title
        draft["content"] = content
        draft["score"] = audit_res["overall_score"]
        draft["findings_count"] = audit_res["findings_count"]
        draft["history"].append({
            "timestamp": now_str,
            "user": author,
            "action": f"Updated Draft (Score: {audit_res['overall_score']}/100)"
        })
        saved = db.save_draft(draft)
    else:
        new_draft = {
            "id": draft_id,
            "title": title,
            "content": content,
            "author": author,
            "created_at": now_str,
            "status": "DRAFT",
            "score": audit_res["overall_score"],
            "findings_count": audit_res["findings_count"],
            "history": [
                {"timestamp": now_str, "user": author, "action": f"Created Draft (Score: {audit_res['overall_score']}/100)"}
            ],
            "comments": []
        }
        saved = db.save_draft(new_draft)

    db.log_action(author, f"Saved document draft {draft_id} ('{title}')")
    return {"status": "success", "draft": saved, "audit": audit_res}

@app.post("/api/drafts/{draft_id}/action")
def update_draft_status(draft_id: str, action_data: WorkflowActionModel):
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action_type = action_data.action.upper()

    if action_type == "APPROVE":
        draft["status"] = "APPROVED"
        log_msg = f"{action_data.user_name} ({action_data.role}) Approved content for publication."
        if action_data.note:
            log_msg += f" Note: {action_data.note}"
    elif action_type == "REQUEST_CHANGES":
        draft["status"] = "CHANGES_REQUESTED"
        log_msg = f"{action_data.user_name} ({action_data.role}) Requested Revisions."
        if action_data.note:
            log_msg += f" Reason: {action_data.note}"
    elif action_type == "OVERRIDE":
        if not action_data.override_reason:
            raise HTTPException(status_code=400, detail="Override reason is mandatory for governance exceptions.")
        draft["status"] = "APPROVED_WITH_OVERRIDE"
        log_msg = f"OVERRIDE APPROVED by {action_data.user_name} ({action_data.role}). Rationale: {action_data.override_reason}"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action {action_data.action}")

    draft["history"].append({
        "timestamp": now_str,
        "user": action_data.user_name,
        "action": log_msg
    })

    db.log_action(action_data.user_name, f"Workflow Action on {draft_id}: {action_type}")
    return {"status": "success", "draft": draft}

@app.post("/api/drafts/{draft_id}/comments")
def add_comment(draft_id: str, comment: CommentModel):
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_c = {
        "id": f"c-{len(draft['comments']) + 1}",
        "author": comment.author,
        "role": comment.role,
        "timestamp": now_str,
        "text": comment.text
    }
    draft["comments"].append(new_c)
    db.log_action(comment.author, f"Added comment on {draft_id}")
    return {"status": "success", "comment": new_c, "all_comments": draft["comments"]}

@app.get("/api/insights")
def get_insights():
    return db.get_insights()

@app.get("/api/audit-log")
def get_audit_log():
    return db.get_audit_log()

# ==================== Round 3 Delivered Improvement 1: Vision Inspector ====================

@app.post("/api/vision/inspect")
async def inspect_banner(file: Optional[UploadFile] = File(None), preset: Optional[str] = Body(None)):
    """Inspects an uploaded image banner or pre-generated preset."""
    if file:
        content = await file.read()
        filename = file.filename
    else:
        preset_type = preset or "compliant"
        content, filename = vision_inspector.generate_demo_banner(preset_type)

    analysis = vision_inspector.analyze_image_bytes(content, filename=filename)
    return analysis

@app.get("/api/vision/demo/{banner_type}")
def get_demo_banner_image(banner_type: str):
    """Returns demo banner image directly for UI rendering."""
    bytes_data, filename = vision_inspector.generate_demo_banner(banner_type)
    return Response(content=bytes_data, media_type="image/png", headers={"Content-Disposition": f"inline; filename={filename}"})

# ==================== Round 3 Delivered Improvement 2: Vector Semantic RAG ====================

@app.post("/api/rag/search")
def search_rag(req: RAGSearchRequest):
    results = rag_engine.search(req.query, top_k=req.top_k)
    return {"query": req.query, "results": results, "count": len(results)}

@app.post("/api/rag/ask")
def ask_rag(req: RAGSearchRequest):
    answer_obj = rag_engine.ask_brand_knowledge(req.query)
    return answer_obj

@app.post("/api/rag/ingest")
def ingest_rag_document(req: RAGIngestRequest):
    doc = rag_engine.ingest_document(req.title, req.category, req.content, req.source)
    db.log_action("Admin", f"Ingested document into Semantic RAG: '{req.title}'")
    return {"status": "success", "document": doc}

@app.get("/api/rag/documents")
def list_rag_documents():
    return {"documents": rag_engine.get_all_documents(), "total_chunks": len(rag_engine.chunks)}

# ==================== Round 3 Delivered Improvement 3: CMS Simulator ====================

@app.post("/api/cms/check")
def check_cms_context(req: CMSCheckRequest):
    result = cms_simulator.check_in_context(req.text, req.platform, req.element_type)
    return result

# ==================== Inkloom AI Machine Learning Model Integration ====================

@app.post("/api/inkloom/predict")
def predict_inkloom(req: InkloomPredictRequest):
    """Classifies text with Inkloom AI sentence-transformers encoder and logistic regression classifier."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    return inkloom_engine.predict(req.text)

@app.post("/api/inkloom/analyze")
def analyze_inkloom(req: InkloomPredictRequest):
    """Decomposes text into sentences and evaluates risk, drift, and class probabilities per sentence."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    return inkloom_engine.analyze_content(req.text)

@app.post("/api/inkloom/batch")
def batch_predict_inkloom(req: InkloomBatchRequest):
    """Batch classifies an array of text snippets."""
    if not req.texts:
        raise HTTPException(status_code=400, detail="Texts list cannot be empty.")
    return {"results": inkloom_engine.predict_batch(req.texts), "count": len(req.texts)}

@app.get("/api/inkloom/model-info")
def get_inkloom_info():
    """Returns technical metadata, classes, embedding dimensions, and runtime status of the Inkloom ML model."""
    return inkloom_engine.get_model_info()

# ==================== Round 3 Reliability Testing Suite ====================

@app.post("/api/tests/run")
def run_tests():
    report = reliability_test_suite.run_all_tests()
    return report

# ==================== PDF Reports ====================

@app.get("/api/download/submission-pdf-r3")
def download_round3_pdf():
    pdf_bytes = generate_round3_submission_pdf()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=TechFusion_Round3_Submission_Report.pdf"}
    )

@app.get("/api/download/submission-pdf")
def download_submission_pdf():
    # Defaults to the latest Round 3 Finish report
    pdf_bytes = generate_round3_submission_pdf()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=TechFusion_Round3_Submission_Report.pdf"}
    )

@app.post("/api/download/certificate")
def download_certificate(payload: Dict[str, Any] = Body(...)):
    draft_data = payload.get("draft", {"id": "DOC-EXPORT", "title": "Brand Audit Report", "author": "Reviewer"})
    audit_data = payload.get("audit") or engine.review_content(draft_data.get("content", ""), draft_data.get("title", ""))
    pdf_bytes = generate_audit_certificate_pdf(draft_data, audit_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=TechFusion_Brand_Certificate_{draft_data.get('id', 'DOC')}.pdf"}
    )

# Static files mounting
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    return FileResponse(index_file)
