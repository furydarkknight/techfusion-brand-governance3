import os
import re
import json
import warnings
import numpy as np
from typing import List, Dict, Any, Optional

# Suppress harmless sklearn unpickle version warnings
warnings.filterwarnings("ignore", category=UserWarning)
try:
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
except ImportError:
    pass


class InkloomModelEngine:
    """
    Inkloom AI Backend Model Integration Engine.

    Architecture
    ────────────
    • Encoder : sentence-transformers/all-MiniLM-L6-v2 exported to ONNX.
      Produces 384-d L2-normalised embeddings via mean-pooling with attention mask.
    • Classifier : scikit-learn LogisticRegression trained by Team TechFusion on the
      inkloom_marketing_quality_dataset (1 500 labelled sentences, 500 / class).
      Held-out accuracy: 95.3 % macro-F1 on 150 unseen samples (50 / class).
    • Fallback : keyword heuristic, clearly labelled as such in every result.

    Model provenance
    ────────────────
    • Encoder weights  : unmodified all-MiniLM-L6-v2 (sentence-transformers).
    • Classifier       : trained by Team TechFusion; not an Inkloom AI product.
    • Training data    : inkloom_marketing_quality_dataset.csv (1 500 rows,
                         BAD / GOOD / NEEDS_CONTEXT; internal TechFusion dataset).
    """

    # Decision threshold tuned on held-out set (F1=0.980 for BAD @ 0.40)
    BAD_THRESHOLD: float = 0.40

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or self._find_model_directory()
        self.metadata: Dict[str, Any] = {}
        self.classes: List[str] = ["BAD", "GOOD", "NEEDS_CONTEXT"]
        self.embedding_dim: int = 384
        self.is_loaded: bool = False
        self.load_error: Optional[str] = None

        self._tokenizer = None   # tokenizers.Tokenizer (fast, no torch)
        self._session = None     # onnxruntime.InferenceSession
        self.classifier = None   # sklearn LogisticRegression

        self._load_model()

    # ── path discovery ─────────────────────────────────────────────────────────

    def _find_model_directory(self) -> str:
        env_path = os.environ.get("INKLOOM_MODEL_PATH")
        if env_path and os.path.exists(env_path):
            return env_path

        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(current_dir)

        candidates = [
            os.path.join(repo_root, "models", "inkloom"),
            os.path.join(repo_root, "Inkloom_Export"),
            os.path.join(repo_root, "inkloom"),
            os.path.join(current_dir, "models", "inkloom"),
            os.path.join(current_dir, "inkloom"),
        ]
        for cand in candidates:
            if os.path.isdir(cand) and (
                os.path.exists(os.path.join(cand, "classifier.joblib")) or
                os.path.exists(os.path.join(cand, "metadata.json")) or
                os.path.exists(os.path.join(cand, "encoder"))
            ):
                return cand

        return os.path.join(repo_root, "models", "inkloom")

    # ── model loading ──────────────────────────────────────────────────────────

    def _load_model(self):
        try:
            # 1. Metadata
            meta_path = os.path.join(self.model_dir, "metadata.json")
            if not os.path.exists(meta_path):
                for root, _, files in os.walk(self.model_dir):
                    if "metadata.json" in files:
                        meta_path = os.path.join(root, "metadata.json")
                        break
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                    self.classes = self.metadata.get("classes", self.classes)
                    self.embedding_dim = self.metadata.get("embedding_dimensions", 384)

            # 2. Classifier
            clf_path = os.path.join(self.model_dir, "classifier.joblib")
            if not os.path.exists(clf_path):
                for root, _, files in os.walk(self.model_dir):
                    if "classifier.joblib" in files:
                        clf_path = os.path.join(root, "classifier.joblib")
                        break
            if os.path.exists(clf_path):
                import joblib
                self.classifier = joblib.load(clf_path)
                if hasattr(self.classifier, "classes_"):
                    self.classes = list(self.classifier.classes_)

            # 3. Locate encoder directory
            encoder_path = os.path.join(self.model_dir, "encoder")
            if not os.path.isdir(encoder_path):
                for root, dirs, _ in os.walk(self.model_dir):
                    if "encoder" in dirs:
                        encoder_path = os.path.join(root, "encoder")
                        break

            # 4. Fast tokenizer (tokenizers library – no torch)
            from tokenizers import Tokenizer
            tokenizer_json = os.path.join(encoder_path, "tokenizer.json")
            if not os.path.exists(tokenizer_json):
                raise FileNotFoundError(f"tokenizer.json not found at {tokenizer_json}")
            self._tokenizer = Tokenizer.from_file(tokenizer_json)
            self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=None)
            self._tokenizer.enable_truncation(max_length=256)

            # 5. ONNX encoder (onnxruntime – no torch)
            import onnxruntime as ort
            onnx_path = os.path.join(encoder_path, "model.onnx")
            if not os.path.exists(onnx_path):
                raise FileNotFoundError(
                    f"ONNX model not found at {onnx_path}. "
                    "Run scripts/export_onnx.py once to generate it."
                )
            so = ort.SessionOptions()
            so.log_severity_level = 3  # suppress ORT verbose logs
            self._session = ort.InferenceSession(
                onnx_path,
                sess_options=so,
                providers=["CPUExecutionProvider"],
            )

            self.is_loaded = True
            self.load_error = None

        except Exception as exc:
            self.is_loaded = False
            self.load_error = str(exc)

    # ── encoding ───────────────────────────────────────────────────────────────

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encodes texts into 384-dim L2-normalised embeddings using the ONNX encoder.
        Implements the same mean-pooling + L2-normalise as sentence-transformers.
        Returns zeros array if the model is not loaded (allows graceful degradation).
        """
        if not self.is_loaded or self._session is None or self._tokenizer is None:
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)

        if isinstance(texts, str):
            texts = [texts]

        sanitized = [t.strip() if t.strip() else "empty" for t in texts]
        encodings = self._tokenizer.encode_batch(sanitized)

        input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
        token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

        last_hidden = self._session.run(
            ["last_hidden_state"],
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )[0]  # shape: (batch, seq, 384)

        mask = attention_mask[:, :, np.newaxis].astype(np.float32)
        sum_emb = np.sum(last_hidden * mask, axis=1)
        sum_mask = np.clip(np.sum(mask, axis=1), a_min=1e-9, a_max=None)
        mean_emb = sum_emb / sum_mask
        norms = np.linalg.norm(mean_emb, axis=1, keepdims=True)
        return (mean_emb / np.clip(norms, a_min=1e-9, a_max=None)).astype(np.float32)

    # ── single prediction ──────────────────────────────────────────────────────

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Classifies a single text.
        Returns predicted class, confidence, and 3-class probability distribution.
        Falls back to keyword heuristic (clearly labelled) if the model is unavailable.
        """
        if not text or not text.strip():
            return {
                "text": text,
                "predicted_class": "NEEDS_CONTEXT",
                "confidence": 0.5,
                "probabilities": {c: round(1.0 / len(self.classes), 4) for c in self.classes},
                "status": "empty_input",
                "inference_mode": "none",
            }

        if not self.is_loaded or self.classifier is None:
            return self._fallback_heuristic_predict(text)

        embeddings = self.encode([text])
        probs = self.classifier.predict_proba(embeddings)[0]
        pred_idx = int(np.argmax(probs))
        predicted_class = self.classes[pred_idx]
        confidence = float(probs[pred_idx])
        prob_dict = {cls: round(float(p), 4) for cls, p in zip(self.classes, probs)}

        return {
            "text": text,
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "embedding_dimensions": self.embedding_dim,
            "model_version": "all-MiniLM-L6-v2 + LogisticRegression (ONNX)",
            "status": "success",
            "inference_mode": "neural_onnx",
        }

    # ── batch prediction ───────────────────────────────────────────────────────

    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Batch inference using a single ONNX forward pass."""
        if not texts:
            return []
        if not self.is_loaded or self.classifier is None:
            return [self.predict(t) for t in texts]

        embeddings = self.encode(texts)
        all_probs = self.classifier.predict_proba(embeddings)
        results = []

        for text, probs in zip(texts, all_probs):
            pred_idx = int(np.argmax(probs))
            predicted_class = self.classes[pred_idx]
            confidence = float(probs[pred_idx])
            prob_dict = {cls: round(float(p), 4) for cls, p in zip(self.classes, probs)}
            results.append({
                "text": text,
                "predicted_class": predicted_class,
                "confidence": round(confidence, 4),
                "probabilities": prob_dict,
                "inference_mode": "neural_onnx",
            })

        return results

    # ── sentence-level analysis ────────────────────────────────────────────────

    def analyze_content(self, text: str) -> Dict[str, Any]:
        """
        Decomposes text into sentences and classifies each one.
        Generates structured brand-governance findings for high-risk sentences.
        """
        if not text or not text.strip():
            return {
                "overall_classification": "GOOD",
                "overall_confidence": 1.0,
                "probabilities": {c: 0.0 for c in self.classes},
                "sentence_evaluations": [],
                "ml_findings": [],
                "risk_summary": "No text provided.",
            }

        doc_prediction = self.predict(text[:1000])
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 3]
        if not sentences:
            sentences = [text.strip()]

        sentence_results = self.predict_batch(sentences)
        ml_findings = []
        inference_mode = doc_prediction.get("inference_mode", "neural_onnx")

        for res in sentence_results:
            s_text = res["text"]
            cls = res["predicted_class"]
            probs = res["probabilities"]
            bad_prob = probs.get("BAD", 0.0)
            ctx_prob = probs.get("NEEDS_CONTEXT", 0.0)

            start_pos = text.find(s_text)
            end_pos = start_pos + len(s_text) if start_pos != -1 else len(text)

            if inference_mode == "keyword_fallback":
                # Keyword fallback findings – never claim neural origin
                if cls == "BAD":
                    ml_findings.append({
                        "id": f"F-INKLOOM-{len(ml_findings) + 1}",
                        "category": "tone",
                        "severity": "warning",
                        "rule_id": "INK-KW-01",
                        "rule_name": "Inkloom Keyword Fallback – Tone Flag",
                        "flagged_text": s_text,
                        "start_char": max(0, start_pos),
                        "end_char": max(0, end_pos),
                        "reason": (
                            "Keyword heuristic (neural model unavailable) matched a prohibited term. "
                            "Manual brand-voice review is recommended."
                        ),
                        "suggestion": "Revise statement to adopt an empathetic, evidence-backed enterprise tone.",
                        "confidence": res["confidence"],
                        "approved_source": "Inkloom Keyword Fallback (neural unavailable)",
                        "probabilities": probs,
                    })
            else:
                # Neural findings
                if cls == "BAD" or bad_prob >= self.BAD_THRESHOLD:
                    severity = "critical" if bad_prob >= 0.65 else "warning"
                    ml_findings.append({
                        "id": f"F-INKLOOM-{len(ml_findings) + 1}",
                        "category": "tone",
                        "severity": severity,
                        "rule_id": "INK-ML-01",
                        "rule_name": "Inkloom Neural Drift Intercept",
                        "flagged_text": s_text,
                        "start_char": max(0, start_pos),
                        "end_char": max(0, end_pos),
                        "reason": (
                            f"Neural classifier (all-MiniLM-L6-v2 + LogisticRegression) classified "
                            f"this statement as '{cls}' with {round(bad_prob * 100, 1)}% BAD probability "
                            f"(threshold: {int(self.BAD_THRESHOLD * 100)}%). "
                            "Statement conflicts with certified brand voice distribution."
                        ),
                        "suggestion": "Revise statement to adopt an empathetic, evidence-backed enterprise tone.",
                        "confidence": res["confidence"],
                        "approved_source": "Inkloom Neural Classifier (ONNX)",
                        "probabilities": probs,
                    })
                elif cls == "NEEDS_CONTEXT" and ctx_prob >= 0.65 and len(s_text.split()) > 6:
                    ml_findings.append({
                        "id": f"F-INKLOOM-{len(ml_findings) + 1}",
                        "category": "claims",
                        "severity": "suggestion",
                        "rule_id": "INK-ML-02",
                        "rule_name": "Inkloom Context Verification",
                        "flagged_text": s_text,
                        "start_char": max(0, start_pos),
                        "end_char": max(0, end_pos),
                        "reason": (
                            f"Neural classifier requires contextual grounding "
                            f"({round(ctx_prob * 100, 1)}% NEEDS_CONTEXT probability)."
                        ),
                        "suggestion": "Attach corroborating metric citation or SEC verification document.",
                        "confidence": res["confidence"],
                        "approved_source": "Inkloom Neural Classifier (ONNX)",
                        "probabilities": probs,
                    })

        bad_count = sum(1 for s in sentence_results if s["predicted_class"] == "BAD")
        if bad_count >= 2 or doc_prediction["predicted_class"] == "BAD":
            risk_level = "HIGH_RISK"
        elif bad_count == 1 or doc_prediction["predicted_class"] == "NEEDS_CONTEXT":
            risk_level = "MODERATE_DRIFT"
        else:
            risk_level = "BRAND_ALIGNED"

        return {
            "overall_classification": doc_prediction["predicted_class"],
            "overall_confidence": doc_prediction["confidence"],
            "probabilities": doc_prediction["probabilities"],
            "risk_level": risk_level,
            "sentence_evaluations": sentence_results,
            "ml_findings": ml_findings,
            "total_sentences_evaluated": len(sentence_results),
            "model_metadata": {
                "encoder": "sentence-transformers/all-MiniLM-L6-v2 (ONNX)",
                "classifier": "LogisticRegression (scikit-learn)",
                "trained_by": "Team TechFusion",
                "training_samples": "1500 (500/class)",
                "held_out_accuracy": "95.3% macro-F1 (150 samples, 50/class)",
                "bad_threshold": self.BAD_THRESHOLD,
                "classes": self.classes,
                "embedding_dimensions": self.embedding_dim,
                "runtime": "onnxruntime (no PyTorch)",
                "status": "loaded" if self.is_loaded else "fallback",
            },
        }

    # ── keyword fallback ───────────────────────────────────────────────────────

    def _fallback_heuristic_predict(self, text: str) -> Dict[str, Any]:
        """
        Keyword heuristic used ONLY when the ONNX model fails to load.
        Results are clearly labelled 'keyword_fallback' and never presented
        as output from the neural classifier.
        """
        text_lower = text.lower()
        bad_indicators = ["crush", "cheap", "miracle", "100% bug-free", "zero downtime", "blacklist"]
        good_indicators = ["cost-effective", "resilient", "99.99%", "compliance", "soc2", "enterprise"]

        bad_score = sum(1 for w in bad_indicators if w in text_lower)
        good_score = sum(1 for w in good_indicators if w in text_lower)

        if bad_score > good_score:
            cls = "BAD"
            probs = {"BAD": 0.70, "GOOD": 0.10, "NEEDS_CONTEXT": 0.20}
        elif good_score > bad_score:
            cls = "GOOD"
            probs = {"BAD": 0.10, "GOOD": 0.75, "NEEDS_CONTEXT": 0.15}
        else:
            cls = "NEEDS_CONTEXT"
            probs = {"BAD": 0.25, "GOOD": 0.25, "NEEDS_CONTEXT": 0.50}

        return {
            "text": text,
            "predicted_class": cls,
            "confidence": probs[cls],
            "probabilities": probs,
            "embedding_dimensions": self.embedding_dim,
            "model_version": "Keyword Heuristic Fallback (neural model unavailable)",
            "status": "fallback",
            "inference_mode": "keyword_fallback",
        }

    # ── diagnostics ────────────────────────────────────────────────────────────

    def get_model_info(self) -> Dict[str, Any]:
        """Returns diagnostic info about the loaded Inkloom ML model."""
        return {
            "model_name": "Inkloom Brand Tone & Compliance Classifier",
            "trained_by": "Team TechFusion",
            "model_provenance": (
                "Encoder: unmodified sentence-transformers/all-MiniLM-L6-v2 (ONNX export). "
                "Classifier: LogisticRegression trained by Team TechFusion on "
                "inkloom_marketing_quality_dataset.csv (1500 labelled sentences)."
            ),
            "held_out_accuracy": "95.3% macro-F1 (150 unseen samples, 50/class)",
            "bad_threshold": self.BAD_THRESHOLD,
            "is_loaded": self.is_loaded,
            "load_error": self.load_error,
            "runtime": "onnxruntime (no PyTorch required)",
            "model_dir": self.model_dir,
            "classes": self.classes,
            "embedding_dimensions": self.embedding_dim,
            "metadata": self.metadata,
            "classifier_type": str(type(self.classifier)) if self.classifier else "None",
            "has_onnx_session": self._session is not None,
            "has_tokenizer": self._tokenizer is not None,
        }


# ── Global singleton ───────────────────────────────────────────────────────────
inkloom_engine = InkloomModelEngine()

if __name__ == "__main__":
    print("--- Inkloom Engine Diagnostic ---")
    info = inkloom_engine.get_model_info()
    print("Status:", "LOADED" if info["is_loaded"] else "FAILED")
    if info["load_error"]:
        print("Error:", info["load_error"])
    print("Runtime:", info["runtime"])
    print("Classes:", info["classes"])
    test_text = "TechFusion provides enterprise organizations with zero-trust encryption."
    res = inkloom_engine.predict(test_text)
    print("Sample Prediction:", res)
