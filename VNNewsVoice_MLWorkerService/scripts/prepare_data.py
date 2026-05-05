import argparse
import json
import logging
import random
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT_DIR / "data" / "processed" / "pairs.jsonl"
SPLIT_DIR = ROOT_DIR / "data" / "splits"


def load_local_pairs(path: Path) -> list[dict]:
    pairs = []
    if not path.exists():
        logger.warning("File not found: %s", path)
        return pairs
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            source = (obj.get("input") or "").strip()
            target = (obj.get("target") or "").strip()
            if len(source) > 100 and len(target) > 20:
                pairs.append({"input": source[:3000], "target": target})
    logger.info("Loaded local pairs: %d", len(pairs))
    return pairs


def load_hf_pairs(sample_count: int) -> list[dict]:
    from datasets import load_dataset

    dataset = load_dataset("VietAI/vietnews", split="train", streaming=True)
    pairs = []
    for row in dataset:
        if len(pairs) >= sample_count:
            break
        article = (row.get("article") or "").strip()
        abstract = (row.get("abstract") or "").strip()
        if len(article) > 100 and len(abstract) > 20:
            pairs.append({"input": article[:3000], "target": abstract})
    logger.info("Loaded HF pairs: %d", len(pairs))
    return pairs


def write_jsonl(items: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info("Wrote %d rows -> %s", len(items), output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--add_hf_dataset", action="store_true")
    parser.add_argument("--hf_samples", type=int, default=20000)
    args = parser.parse_args()

    rows = load_local_pairs(INPUT_FILE)
    if args.add_hf_dataset:
        rows.extend(load_hf_pairs(args.hf_samples))
    if not rows:
        logger.error("No training rows found")
        return

    random.seed(args.seed)
    random.shuffle(rows)

    split_idx = int(len(rows) * 0.8)
    train_rows = rows[:split_idx]
    val_rows = rows[split_idx:]
    write_jsonl(train_rows, SPLIT_DIR / "train.jsonl")
    write_jsonl(val_rows, SPLIT_DIR / "val.jsonl")
    logger.info("Done")


if __name__ == "__main__":
    main()
