#!/usr/bin/env python3
"""Tiny synthetic semantic-similarity proof; not a viral predictor or benchmark.

Downloads only two pinned public model files to the runner's temporary directory.
No private video information or credentials are sent to the model provider.
"""
import json
import os
import tempfile
import urllib.request

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

REV = "751bff37182d3f1213fa05d7196b954e230abad9"
BASE = f"https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/{REV}/"
TEXTS = [
    "How did clay preserve the skin of a dinosaur mummy?",
    "Fossilized duck-billed dinosaur skin turned out to be a clay mask",
    "A young tyrannosaur fossil reveals the dinosaur's last meal",
    "A recipe for baking chocolate cake at home",
]


def download(name, path):
    request = urllib.request.Request(BASE + name, headers={"User-Agent": "ExtinctLifeResearchProbe/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response, open(path, "wb") as target:
        total = 0
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > 60 * 1024 * 1024:
                raise ValueError("Model file exceeds probe download cap")
            target.write(chunk)


def main():
    with tempfile.TemporaryDirectory(prefix="extinct-life-model-") as tmp:
        model = os.path.join(tmp, "model.onnx")
        tokenizer_file = os.path.join(tmp, "tokenizer.json")
        download("onnx/model_quantized.onnx", model)
        download("tokenizer.json", tokenizer_file)
        tokenizer = Tokenizer.from_file(tokenizer_file)
        tokenizer.enable_truncation(max_length=256)
        tokenizer.enable_padding()
        encoded = tokenizer.encode_batch(TEXTS)
        input_ids = np.asarray([item.ids for item in encoded], dtype=np.int64)
        attention = np.asarray([item.attention_mask for item in encoded], dtype=np.int64)
        feeds = {"input_ids": input_ids, "attention_mask": attention,
                 "token_type_ids": np.zeros_like(input_ids)}
        session = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
        inputs = {item.name: feeds[item.name] for item in session.get_inputs()}
        states = session.run(None, inputs)[0]
        mask = attention[..., None]
        vectors = (states * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1)
        vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
        scores = vectors[1:] @ vectors[0]
        results = [{"text": text, "cosine": round(float(score), 4)}
                   for text, score in zip(TEXTS[1:], scores)]
        print(json.dumps({"source": "Hugging Face ONNX inference", "status": "OK",
                          "revision": REV, "query": TEXTS[0], "results": results}))
        print("Similarity is a relevance hint, not a topic-demand or viral score; synthetic examples only.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Do not print exception details or remote URLs to publicly visible logs.
        print(json.dumps({"source": "Hugging Face ONNX inference", "status": "FAILED",
                          "error_type": type(exc).__name__}))
        raise SystemExit(1)
