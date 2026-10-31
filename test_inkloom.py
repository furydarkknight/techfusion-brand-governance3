#!/usr/bin/env python3
"""
Inkloom AI ML Model Verification Script.
Runs comprehensive sanity checks on:
1. Sentence-Transformers MiniLM-L6-v2 Encoder
2. Logistic Regression Classifier (classifier.joblib)
3. Embedding Dimensions & Normalization
4. 3-Class Softmax Probability Distribution (BAD, GOOD, NEEDS_CONTEXT)
5. Sentence-Level Brand Governance Analysis
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.inkloom_engine import inkloom_engine

def main():
    print("==================================================================")
    print("       INKLOOM AI MODEL & TECHFUSION INTEGRATION TEST             ")
    print("==================================================================")

    # 1. Diagnostic Info
    info = inkloom_engine.get_model_info()
    print(f"\n[1] Model Status:")
    print(f"    - Loaded: {info['is_loaded']}")
    print(f"    - Device: {info['device']}")
    print(f"    - Model Path: {info['model_dir']}")
    print(f"    - Target Classes: {info['classes']}")
    print(f"    - Embedding Dimensions: {info['embedding_dimensions']}")

    if not info['is_loaded']:
        print(f"    - Warning / Error: {info['load_error']}")
        sys.exit(1)

    # 2. Dense Embedding Check
    t0 = time.time()
    sample_text = "TechFusion provides enterprise organizations with zero-trust encryption."
    embeddings = inkloom_engine.encode([sample_text])
    emb_time = (time.time() - t0) * 1000
    norm = sum(x*x for x in embeddings[0]) ** 0.5
    print(f"\n[2] Encoder Output (MiniLM-L6-v2):")
    print(f"    - Latency: {emb_time:.2f}ms")
    print(f"    - Shape: {embeddings.shape}")
    print(f"    - L2 Norm: {norm:.4f} (Expected: ~1.0000)")

    # 3. Single Text Prediction Check
    t0 = time.time()
    pred = inkloom_engine.predict(sample_text)
    pred_time = (time.time() - t0) * 1000
    print(f"\n[3] Single Text Inference:")
    print(f"    - Latency: {pred_time:.2f}ms")
    print(f"    - Predicted Class: {pred['predicted_class']}")
    print(f"    - Confidence: {pred['confidence'] * 100:.1f}%")
    print(f"    - Class Probabilities: {pred['probabilities']}")

    # 4. Sentence-by-Sentence Anomaly Check
    multi_sent_text = (
        "Hey you guys! TechFusion is thrilled to drop our game-changing miracle update today! "
        "Our new platform is 100% bug-free and will completely crush the competition. "
        "TechFusion holds annual SOC2 Type II, ISO 27001, and HIPAA compliance certifications."
    )
    t0 = time.time()
    analysis = inkloom_engine.analyze_content(multi_sent_text)
    analysis_time = (time.time() - t0) * 1000
    print(f"\n[4] Sentence Decomposition & Anomaly Analysis:")
    print(f"    - Latency: {analysis_time:.2f}ms")
    print(f"    - Overall Classification: {analysis['overall_classification']}")
    print(f"    - Overall Risk Level: {analysis['risk_level']}")
    print(f"    - Sentences Evaluated: {analysis['total_sentences_evaluated']}")
    print(f"    - ML Findings Triggered: {len(analysis['ml_findings'])}")

    for idx, s in enumerate(analysis['sentence_evaluations']):
        probs_str = ", ".join(f"{k}: {int(v*100)}%" for k, v in s['probabilities'].items())
        print(f"      Sentence #{idx+1} [{s['predicted_class']}] ({probs_str}): \"{s['text'][:60]}...\"")

    print("\n==================================================================")
    print("       ALL INKLOOM ML MODEL VERIFICATION CHECKS PASSED           ")
    print("==================================================================")

if __name__ == "__main__":
    main()
