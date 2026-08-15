#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from utils import file_hash, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", default="models/model_metadata.json")
    args = parser.parse_args()
    root = Path(args.model)
    required = ("config.json", "tokenizer_config.json", "chat_template.jinja", "model.safetensors.index.json")
    files = {}
    for name in required:
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(path)
        files[name] = file_hash(path)
    metadata = {
        "model_id": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "revision": args.revision,
        "path": str(root.resolve()),
        "files": files,
    }
    write_json(args.output, metadata, overwrite=False)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
