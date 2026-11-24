#!/usr/bin/env python3
"""Semantic matching restricted to independently sourced scientific titles."""
import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

BASE = Path(__file__).resolve().parent
REV = '751bff37182d3f1213fa05d7196b954e230abad9'
MODEL = f'https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/{REV}/'

def download(name, path):
    req = urllib.request.Request(MODEL + name, headers={'User-Agent': 'ExtinctLifeResearch/0.1'})
    with urllib.request.urlopen(req, timeout=45) as response, open(path, 'wb') as target:
        total = 0
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > 60 * 1024 * 1024:
                raise ValueError('model exceeds download cap')
            target.write(chunk)

def run(config, science):
    papers, seen = [], set()
    for group in science.get('discoveries', []):
        for paper in group.get('results', []):
            title = paper.get('title')
            identity = (paper.get('doi') or title or '').lower()
            if not title or not identity or identity in seen:
                continue
            seen.add(identity)
            papers.append({'title': title, 'doi': paper.get('doi'), 'source': paper.get('source')})
    if not papers:
        raise ValueError('no scientific discovery titles available')
    candidates = config['candidates']
    texts = [c['question'] for c in candidates] + [p['title'] for p in papers]
    with tempfile.TemporaryDirectory(prefix='extinct-life-semantic-') as temp:
        model, tokenizer_file = os.path.join(temp, 'model.onnx'), os.path.join(temp, 'tokenizer.json')
        download('onnx/model_quantized.onnx', model)
        download('tokenizer.json', tokenizer_file)
        tokenizer = Tokenizer.from_file(tokenizer_file)
        tokenizer.enable_truncation(max_length=256)
        tokenizer.enable_padding()
        encoded = tokenizer.encode_batch(texts)
        ids = np.asarray([x.ids for x in encoded], dtype=np.int64)
        attention = np.asarray([x.attention_mask for x in encoded], dtype=np.int64)
        feeds = {'input_ids': ids, 'attention_mask': attention, 'token_type_ids': np.zeros_like(ids)}
        session = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
        vectors = session.run(None, {i.name: feeds[i.name] for i in session.get_inputs()})[0]
        mask = attention[..., None]
        vectors = (vectors * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1)
        vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
        result = []
        for n, candidate in enumerate(candidates):
            scores = vectors[len(candidates):] @ vectors[n]
            matches = [dict(paper, similarity=round(float(score), 4)) for paper, score in zip(papers, scores)]
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            result.append({'candidate_id': candidate['id'], 'question': candidate['question'], 'matches': matches[:3]})
    return {'source': 'Hugging Face model on Europe PMC scientific titles only', 'model_revision': REV, 'candidates': result,
            'disclaimer': 'Similarity is not a viral probability, audience demand, scientific reliability, or YouTube metric.'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--config', default=str(BASE / 'config.json'))
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    try:
        config = json.loads(Path(args.config).read_text(encoding='utf-8'))
        science = json.loads((output / 'science.json').read_text(encoding='utf-8'))
        result = run(config, science)
        (output / 'semantic.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('::notice::Scientific semantic matching: OK (not a viral score).')
        return 0
    except Exception as exc:
        (output / 'semantic.json').write_text(json.dumps({'error': type(exc).__name__}) + '\n', encoding='utf-8')
        print('Scientific semantic matching: FAILED; sanitized details are in the artifact.')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
