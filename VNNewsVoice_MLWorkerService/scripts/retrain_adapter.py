import argparse
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
ADAPTER_DIR = ROOT_DIR / "models" / "vit5-qlora-adapter"
OUTPUT_DIR = ROOT_DIR / "models" / "vit5-qlora-adapter-new"
TRAIN_FILE = ROOT_DIR / "data" / "splits" / "train.jsonl"
VAL_FILE = ROOT_DIR / "data" / "splits" / "pairs.jsonl"
BASE_MODEL = "VietAI/vit5-base-vietnews-summarization"
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT_NAME", "mlworker-summarization")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def compute_rouge(predictions: list[str], references: list[str]) -> dict[str, float]:
    from rouge_score import rouge_scorer

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=False)
    r1, r2, rl = [], [], []
    for pred, ref in zip(predictions, references):
        score = scorer.score(ref, pred)
        r1.append(score["rouge1"].fmeasure)
        r2.append(score["rouge2"].fmeasure)
        rl.append(score["rougeL"].fmeasure)
    return {
        "rouge1": sum(r1) / len(r1) if r1 else 0.0,
        "rouge2": sum(r2) / len(r2) if r2 else 0.0,
        "rougeL": sum(rl) / len(rl) if rl else 0.0,
    }


def evaluate(
    model, tokenizer, val_rows: list[dict], device, batch_size: int = 4
) -> dict[str, float]:
    import torch

    model.eval()
    predictions, references = [], []
    for i in range(0, min(len(val_rows), 500), batch_size):
        batch = val_rows[i : i + batch_size]
        inputs = ["vietnews: " + row["input"] for row in batch]
        refs = [row["target"] for row in batch]
        encoded = tokenizer(
            inputs,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True,
        ).to(device)
        with torch.no_grad():
            output_ids = model.generate(
                encoded["input_ids"],
                attention_mask=encoded["attention_mask"],
                max_length=128,
                num_beams=2,
                early_stopping=True,
            )
        decoded = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        predictions.extend(decoded)
        references.extend(refs)
    return compute_rouge(predictions, references)


def prepare_dataset(rows: list[dict], tokenizer):
    from datasets import Dataset

    dataset = Dataset.from_list(rows)

    def preprocess(examples):
        model_inputs = tokenizer(
            ["vietnews: " + text for text in examples["input"]],
            max_length=512,
            truncation=True,
        )
        labels = tokenizer(examples["target"], max_length=128, truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    return dataset.map(preprocess, batched=True, remove_columns=dataset.column_names)


def train_model(model, tokenizer, train_dataset, epochs: int, output_dir: Path) -> None:
    import torch
    from transformers import (
        DataCollatorForSeq2Seq,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
    )

    args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        gradient_checkpointing=True,
        learning_rate=2e-4,
        num_train_epochs=epochs,
        warmup_steps=100,
        optim="paged_adamw_8bit",
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported() and torch.cuda.is_available(),
        eval_strategy="no",
        save_strategy="no",
        logging_steps=10,
        report_to="none",
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, padding=True),
    )
    trainer.train()


def maybe_dvc_push() -> None:
    subprocess.run(
        ["dvc", "add", "models/vit5-qlora-adapter/"], cwd=ROOT_DIR, check=True
    )
    subprocess.run(
        ["git", "add", "models/vit5-qlora-adapter.dvc"], cwd=ROOT_DIR, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "mlops(worker): promote retrained adapter"],
        cwd=ROOT_DIR,
        check=True,
    )
    subprocess.run(["dvc", "push"], cwd=ROOT_DIR, check=True)


def main() -> None:
    import mlflow
    import torch
    from peft import (
        LoraConfig,
        PeftModel,
        get_peft_model,
        prepare_model_for_kbit_training,
    )
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, BitsAndBytesConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--eval_only", action="store_true")
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()

    if not VAL_FILE.exists():
        logger.error("Missing validation split: %s", VAL_FILE)
        return
    if not args.eval_only and not TRAIN_FILE.exists():
        logger.error("Missing training split: %s", TRAIN_FILE)
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    if device.type == "cuda":
        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
            if torch.cuda.is_bf16_supported()
            else torch.float16,
        )
        base = AutoModelForSeq2SeqLM.from_pretrained(
            BASE_MODEL, quantization_config=bnb, device_map="auto"
        )
        base = prepare_model_for_kbit_training(base)
        base.gradient_checkpointing_enable()
    else:
        base = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL).to(device)

    if ADAPTER_DIR.exists():
        model = PeftModel.from_pretrained(
            base, str(ADAPTER_DIR), is_trainable=not args.eval_only
        )
    else:
        lora_cfg = LoraConfig(
            r=32,
            lora_alpha=64,
            target_modules=["q", "v"],
            lora_dropout=0.05,
            bias="none",
            task_type="SEQ_2_SEQ_LM",
        )
        model = get_peft_model(base, lora_cfg)

    val_rows = load_jsonl(VAL_FILE)

    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(
        run_name="worker_retrain" if not args.eval_only else "worker_eval"
    ):
        mlflow.log_params(
            {
                "base_model": BASE_MODEL,
                "epochs": args.epochs,
                "eval_only": args.eval_only,
                "device": device.type,
                "adapter_exists": ADAPTER_DIR.exists(),
            }
        )

        baseline = evaluate(model, tokenizer, val_rows, device)
        mlflow.log_metrics({f"baseline_{k}": v for k, v in baseline.items()})
        logger.info("Baseline ROUGE: %s", baseline)

        if args.eval_only:
            return

        train_rows = load_jsonl(TRAIN_FILE)
        train_dataset = prepare_dataset(train_rows, tokenizer)
        start = time.time()
        train_model(model, tokenizer, train_dataset, args.epochs, OUTPUT_DIR)
        mlflow.log_metric("training_minutes", (time.time() - start) / 60.0)

        updated = evaluate(model, tokenizer, val_rows, device)
        mlflow.log_metrics({f"new_{k}": v for k, v in updated.items()})
        logger.info("New ROUGE: %s", updated)

        improved = updated["rouge1"] > baseline["rouge1"]
        mlflow.log_metric("improved", 1 if improved else 0)
        if not improved:
            logger.info("Model was not improved, skipping promotion")
            return

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(OUTPUT_DIR))
        tokenizer.save_pretrained(str(OUTPUT_DIR))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = ADAPTER_DIR.parent / f"vit5-qlora-adapter-backup-{timestamp}"
        if ADAPTER_DIR.exists():
            shutil.move(str(ADAPTER_DIR), str(backup_dir))
        shutil.move(str(OUTPUT_DIR), str(ADAPTER_DIR))
        logger.info("Promoted new adapter; backup at %s", backup_dir)

        if args.promote:
            maybe_dvc_push()


if __name__ == "__main__":
    main()
