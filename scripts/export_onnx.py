#!/usr/bin/env python3
"""
scripts/export_onnx.py
──────────────────────
One-time script to export the all-MiniLM-L6-v2 encoder to ONNX.
Run this once in an environment that has torch + transformers, then
the resulting model.onnx is used by inkloom_engine.py at runtime
via onnxruntime (no torch needed).

Usage:
    python scripts/export_onnx.py

Output:
    models/inkloom/encoder/model.onnx
    models/inkloom/encoder/model.onnx.data  (external weights)
"""
import os
import sys

ENCODER_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "inkloom", "encoder"
)
ONNX_PATH = os.path.join(ENCODER_DIR, "model.onnx")


def main():
    try:
        import torch
        from transformers import AutoTokenizer, AutoModel
    except ImportError:
        print("ERROR: torch and transformers required for export only.")
        print("Install: pip install torch transformers onnxscript")
        sys.exit(1)

    print(f"Loading encoder from: {ENCODER_DIR}")
    tok = AutoTokenizer.from_pretrained(ENCODER_DIR)
    model = AutoModel.from_pretrained(ENCODER_DIR)
    model.eval()

    dummy = ["Hello world, this is a test sentence."]
    inputs = tok(dummy, padding=True, truncation=True, max_length=256, return_tensors="pt")

    print("Exporting to ONNX …")
    torch.onnx.export(
        model,
        (inputs["input_ids"], inputs["attention_mask"], inputs["token_type_ids"]),
        ONNX_PATH,
        input_names=["input_ids", "attention_mask", "token_type_ids"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids":        {0: "batch_size", 1: "sequence_length"},
            "attention_mask":   {0: "batch_size", 1: "sequence_length"},
            "token_type_ids":   {0: "batch_size", 1: "sequence_length"},
            "last_hidden_state":{0: "batch_size", 1: "sequence_length"},
        },
        opset_version=18,
    )
    size_mb = os.path.getsize(ONNX_PATH) / 1024 / 1024
    print(f"Exported: {ONNX_PATH}  ({size_mb:.1f} MB header)")
    data_path = ONNX_PATH + ".data"
    if os.path.exists(data_path):
        data_mb = os.path.getsize(data_path) / 1024 / 1024
        print(f"Weights:  {data_path}  ({data_mb:.1f} MB)")
    print("Done. Delete torch/transformers from requirements.txt before deploying.")


if __name__ == "__main__":
    main()
