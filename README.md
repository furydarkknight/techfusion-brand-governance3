# TechFusion × Inkloom AI — Brand Trust, Before Publish
> **Unified Intelligent Brand-Governance & Machine Learning Platform**  
> *Seamlessly combining TechFusion Brand Governance Core with the Inkloom AI Trained Neural Classifier*

---

## 👥 Team TechFusion & Inkloom AI Track
- **Yash Singhla** — Team Leader · Product Vision, System Architecture & ML Integration
- **Rishit Negi** — Review-Engine Logic · Heuristic Tokenizer & Flesch NLP Analyzer
- **Ramandeep Singh** — Platform & Workflow · Role-Based Approvals, Audit Logging & PDF Engine
- **Aditya Sharma** — UX, Testing & Demo Readiness · UI Design, Charts & Validation

---

## 🚀 Live Demo & Quick Start

### 🌐 Live Application
- **Live URL:** [https://techfusion-brand-governance3.onrender.com/](https://techfusion-brand-governance3.onrender.com/)

> [!NOTE]
> **First Load Notice (Render Cold Start):**  
> Since the application is deployed on Render's free tier, the instance automatically spins down during inactivity. Please allow approximately **50 seconds** for the server to wake up on the initial load. Once warmed up, all interactions and API calls will respond immediately.

### 1. Installation
Clone repository and install dependencies:
```bash
git clone https://github.com/furydarkknight/techfusion-brand-governance3.git
cd techfusion-brand-governance3
pip install -r requirements.txt
```

### 2. Verify Inkloom AI ML Model
Run the standalone model diagnostic script to verify PyTorch/Transformers inference and weights:
```bash
python test_inkloom.py
```

### 3. Run Locally
```bash
python run_server.py
# or:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

### 4. Deploy on Render
This repository includes a `render.yaml` blueprint and dynamic port binding:
1. Go to **[Render Dashboard](https://dashboard.render.com/)** → **New** → **Web Service**.
2. Connect this GitHub repository.
3. Configure settings:
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click **Deploy Web Service**.

---

## 🧠 Machine Learning Model — Provenance & Accuracy

> [!IMPORTANT]
> **Who trained this model?** Team TechFusion trained the LogisticRegression classifier.
> It is **not** an Inkloom AI product or export.
> The encoder (`all-MiniLM-L6-v2`) weights are the **unmodified** public sentence-transformers checkpoint — no fine-tuning was performed.

### Model Components

| Component | Details |
| :--- | :--- |
| **Encoder** | `sentence-transformers/all-MiniLM-L6-v2` — unmodified public weights, exported to ONNX |
| **Runtime** | `onnxruntime` + `tokenizers` — **no PyTorch, no Transformers** (safe on Render free tier) |
| **Classifier** | `scikit-learn LogisticRegression`, trained by Team TechFusion |
| **Training data** | `inkloom_marketing_quality_dataset.csv` — 1 500 labelled sentences (500 / class), internal dataset |
| **Convergence** | 18 LBFGS iterations (C=1.0, max_iter=2000) |

### Measured Accuracy (held-out set, never seen during training)

Evaluated on **150 samples (50 / class), random_seed=42**:

| Class | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: |
| BAD | 1.000 | 0.980 | **0.990** |
| GOOD | 0.923 | 0.960 | **0.941** |
| NEEDS_CONTEXT | 0.939 | 0.920 | **0.929** |
| **Macro avg** | **0.954** | **0.953** | **0.954** |

Confusion matrix (rows = true, cols = predicted, order: BAD / GOOD / NEEDS_CONTEXT):

```
[[49,  0,  1],
 [ 0, 48,  2],
 [ 0,  4, 46]]
```

Decision threshold for BAD class: **0.40** (tuned on held-out set, F1 = 0.980).

> [!NOTE]
> The fallback path (triggered only when the ONNX model fails to load) uses a keyword list.
> Every fallback finding is explicitly labelled **`INK-KW-01 — Keyword Fallback`** and never claims neural origin.

### Engine Summary

| Component | Technical Specification | Function |
| :--- | :--- | :--- |
| **Dense Transformer Encoder** | `all-MiniLM-L6-v2` (ONNX) | 384-d unit-normalised embeddings via mean-pooling |
| **Learned Brand Classifier** | `scikit-learn LogisticRegression` | Classifies into **`BAD`**, **`GOOD`**, **`NEEDS_CONTEXT`** |
| **Sentence Decomposition** | `inkloom_engine.analyze_content` | Per-sentence risk scoring and finding generation |
| **Semantic RAG** | `rag_engine.search` | TF-IDF/BM25 + dense cosine similarity over brand knowledge |
| **Fallback** | Keyword heuristic | Activates only when ONNX model is unavailable; clearly labelled |

### Dedicated Inkloom AI API Endpoints

- `POST /api/inkloom/predict`: Classifies input text and returns predicted class (`BAD` / `GOOD` / `NEEDS_CONTEXT`), confidence %, and 3-class probability distribution.
- `POST /api/inkloom/analyze`: Sentence-level breakdown with risk level assessment and structured governance findings.
- `POST /api/inkloom/batch`: High-throughput batch classification across an array of texts.
- `GET /api/inkloom/model-info`: Inspects model loading status, runtime (ONNX), classes, dimensions, and provenance.

> [!NOTE]
> The ONNX model file (`models/inkloom/encoder/model.onnx`) is included in the repository.
> **PyTorch and Transformers are not required** — the runtime stack is `onnxruntime` + `tokenizers` (~30 MB total), well within Render's free tier (512 MB RAM).

---

## 🎯 Round 3 Capabilities — All Operational ✅

### 1. 🔬 Multi-Modal Computer Vision Brand Inspector
Automated visual governance directly on uploaded image assets.
- **Color Palette Extraction**: K-means dominant color swatches from any PNG/JPG.
- **Prohibited Hex Detection**: Flags retired/off-brand colors (e.g., `#EF4444` warning red).
- **WCAG 2.1 AA Contrast**: Luminance-based foreground/background contrast ratio (min 4.5:1).
- **Logo Safe-Zone Check**: Verifies 24px minimum padding from all canvas edges.
- **Compliance Score**: 0–100 score with COMPLIANT / AT_RISK / NON_COMPLIANT grading.

**Endpoint:** `POST /api/vision/inspect` · `GET /api/vision/demo/{type}`

### 2. 🧠 Vector-Grounded Semantic RAG (Hybrid Dense + Sparse)
Cosine-similarity retrieval powered by Inkloom 384-d dense embeddings + pure-Python BM25/TF-IDF.
- **Semantic Search**: Natural language query matching against certified brand knowledge.
- **Grounded Answers**: Responses cite specific document source, excerpt, and relevance %.
- **Dynamic Ingestion**: Upload new brand books / SEC filings in real-time with instant re-indexing.

**Endpoints:** `POST /api/rag/ask` · `POST /api/rag/search` · `POST /api/rag/ingest` · `GET /api/rag/documents`

### 3. 🖥️ In-Context CMS & Browser Extension Simulator
Inline guardrail prompts simulating native integrations with Google Docs, Figma, and WordPress.

**Endpoint:** `POST /api/cms/check`

---

## 🧪 Automated Reliability Test Suite — 28/28 PASS (100%)

```
Total Tests: 28 | Passed: 28 | Failed: 0 | Success Rate: 100.0%
Status:      ALL_SYSTEMS_OPERATIONAL
```

| ID | Test Case | Category | Result | SLA / Duration |
| :--- | :--- | :--- | :---: | :---: |
| **TC-01** | Terminology Filter: Deprecated 'cheap' | Lexical Heuristics | ✅ PASS | < 2ms |
| **TC-02** | Terminology Filter: Overpromise 'foolproof' | Lexical Heuristics | ✅ PASS | < 2ms |
| **TC-03** | Inclusion Filter: 'blacklist' -> 'denylist' | Diversity & Inclusion | ✅ PASS | < 2ms |
| **TC-04** | Gender-Neutral Standard: 'man-hours' | Diversity & Inclusion | ✅ PASS | < 2ms |
| **TC-05** | Voice & Tone: Sensational Hype Detection | Tone Governance | ✅ PASS | < 2ms |
| **TC-06** | Voice & Tone: Combative Rival Attacks | Tone Governance | ✅ PASS | < 2ms |
| **TC-07** | Fact Grounding: Customer Metric Verification | Claims & SLA | ✅ PASS | < 2ms |
| **TC-08** | Fact Grounding: Uninsurable SLA Intercept | Claims & SLA | ✅ PASS | < 2ms |
| **TC-09** | Fact Grounding: Absolute Defect-Free Claim | Claims & SLA | ✅ PASS | < 2ms |
| **TC-10** | WCAG 2.1 AA Readability: Simple Prose | Accessibility | ✅ PASS | < 2ms |
| **TC-11** | WCAG 2.1 AA: Run-on Cognitive Load Detection | Accessibility | ✅ PASS | < 2ms |
| **TC-12** | Boundary Safety: Clean Input Resiliency | System Reliability | ✅ PASS | < 2ms |
| **TC-13** | Stress Test: 2,500-Word Document Ingestion | Stress & Performance | ✅ PASS | < 80ms SLA |
| **TC-14** | Security: Code & Script Injection Resistance | Security & Privacy | ✅ PASS | < 2ms |
| **TC-15** | Purpose-Aware Diff: Surgical Replacement Integrity | Core Workflow | ✅ PASS | < 2ms |
| **TC-16** | Vision Inspector: WCAG Contrast Calculation | Multi-Modal Vision | ✅ PASS | < 5ms |
| **TC-17** | Vision Inspector: Deprecated Hex Code Intercept | Multi-Modal Vision | ✅ PASS | < 10ms |
| **TC-18** | Vision Inspector: 24px Safe-Padding Verification | Multi-Modal Vision | ✅ PASS | < 10ms |
| **TC-19** | Semantic RAG: Customer Metric Vector Recall | Vector RAG | ✅ PASS | < 5ms |
| **TC-20** | Semantic RAG: Availability SLA Vector Recall | Vector RAG | ✅ PASS | < 5ms |
| **TC-21** | Semantic RAG: Dynamic Ingestion & Live Re-indexing | Vector RAG | ✅ PASS | < 15ms |
| **TC-22** | CMS Integration: Google Docs Inline Pill Generation | In-Context CMS | ✅ PASS | < 5ms |
| **TC-23** | Reliability: Zero-Hallucination Determinism | System Reliability | ✅ PASS | < 2ms |
| **TC-24** | Stress Benchmark: 50 Concurrent Audit Loops | Stress & Performance | ✅ PASS | < 10ms SLA (avg 4.3ms) |
| **TC-25** | **Inkloom AI Model: BAD Classification & Probability Integrity** | **Machine Learning Model** | ✅ **PASS** | **~33ms** |
| **TC-26** | **Inkloom AI Model: 384-d Embedding Non-zero & Unit-normalised** | **Machine Learning Model** | ✅ **PASS** | **~14ms** |
| **TC-27** | **Inkloom AI Model: Sentence Drift — At Least 1 Finding on 'cheap'** | **Machine Learning Model** | ✅ **PASS** | **~32ms** |
| **TC-28** | **Hybrid Pipeline: Clean Enterprise Text → GOOD, 0 Findings** | **Hybrid Architecture** | ✅ **PASS** | **~18ms** |

Run live test suite anytime:
```bash
curl -X POST http://127.0.0.1:8000/api/tests/run
```

---

## 🛠️ Unified System Architecture

```
+-----------------------------------------------------------------------------------+
|                        TechFusion SPA (9 Interactive Tabs)                        |
|  Studio · Vision Inspector · Semantic RAG · CMS Sim · Editorial Workflow ·        |
|  Governance Insights · Test Suite (28/28) · Round 3 Report · Inkloom AI Model     |
|  Tailwind CSS · Phosphor Icons · Chart.js · Vanilla JS                            |
+-----------------------------------------+-----------------------------------------+
                                          | JSON REST API
                                          v
+-----------------------------------------------------------------------------------+
|                            FastAPI Application Layer                              |
|           Routing · CORS · Pydantic Validation · Static File Serving              |
+-------+------------+------------+------------+------------+-----------+-----------+
        |            |            |            |            |           |
        v            v            v            v            v           v
+---------------+ +--------+ +----------+ +---------+ +-----------+ +---------------+
| Heuristic     | | Vision | | Semantic | | CMS Sim | | Test      | | Inkloom AI    |
| Governance    | | Brand  | | RAG      | | Docs /  | | Suite     | | ML Engine     |
| Core v2.4     | | Inspect| | Engine   | | Figma / | | 28 Cases  | | all-MiniLM    |
| (Lexical/     | | (PIL / | | (Dense + | | WP      | | 100% Pass | | L6-v2 Encoder |
|  Claims/Tone/ | |  K-    | |  BM25)   | |         | |           | | + Logistic    |
|  Readability) | |  Means)| |          | |         | |           | | Regression    |
+---------------+ +--------+ +----------+ +---------+ +-----------+ +---------------+
        |                                                                   |
        +---------------------------------+---------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           Hybrid Convergence Engine                               |
|        Merged Explainable Audit · ML Probabilities · Real-Time Auto-Correction    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     Database & In-Memory Knowledge Layer                          |
|       Versioned Guidelines · SEC Verified Facts · Immutable Audit Log · History   |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           ReportLab PDF Generator                                 |
|          Brand Audit Certificates · Round 2 & Round 3 Submission Reports          |
+-----------------------------------------------------------------------------------+
```

---

## 📁 Repository Directory Structure

```
.
├── app/
│   ├── cms_simulator.py         # CMS extension guardrail simulator
│   ├── database.py              # In-memory guidelines, certified facts & audit log
│   ├── engine.py                # Core explainable brand governance engine
│   ├── inkloom_engine.py        # Inkloom ML model inference engine (ONNX + onnxruntime, no PyTorch)
│   ├── main.py                  # FastAPI server with all endpoints
│   ├── pdf_generator.py         # ReportLab PDF certificate & Round 2 report
│   ├── pdf_generator_r3.py      # ReportLab Round 3 finish submission report
│   ├── rag_engine.py            # Hybrid semantic RAG (Inkloom 384-d dense + BM25)
│   ├── test_suite.py            # 28-test automated reliability benchmark suite
│   └── vision_inspector.py      # Multi-modal Pillow CV banner inspector
├── models/
│   └── inkloom/                 # Preserved Inkloom ML model package
│       ├── classifier.joblib    # Trained LogisticRegression classifier weights
│       ├── metadata.json        # Model specs (all-MiniLM-L6-v2, 384 dim, 3 classes)
│       └── encoder/             # sentence-transformers weights + ONNX model (model.onnx)
│           ├── 1_Pooling/
│           ├── 2_Normalize/
│           ├── config.json
│           ├── model.onnx           ← ONNX runtime export (no PyTorch needed)
│           ├── model.safetensors    ← kept for reference / re-export only
│           ├── modules.json
│           ├── tokenizer.json
│           └── tokenizer_config.json
├── static/                      # Single-page web application
│   ├── app.js                   # UI logic, chart rendering & Inkloom sandbox
│   ├── index.html               # Comprehensive responsive interface (9 tabs)
│   └── style.css                # Visual polish & animations
├── requirements.txt             # Runtime dependencies (FastAPI, onnxruntime, tokenizers, scikit-learn — no PyTorch)
├── render.yaml                  # Render cloud blueprint
├── run_server.py                # Entry point with dynamic $PORT binding
├── test_inkloom.py              # Standalone Inkloom model sanity check
├── TechFusion_Round2_Submission_Report.pdf
├── TechFusion_Round3_Submission_Report.pdf
└── README.md
```
