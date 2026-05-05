import hashlib
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
import logging

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from huggingface_hub import InferenceClient
from google import genai

try:
    from peft import PeftModel

    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    logger_tmp = logging.getLogger(__name__)
    logger_tmp.warning(
        "peft not installed — adapter loading disabled. Run: pip install peft"
    )

try:
    import mlflow

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

from app.core.config import settings
from app.models.article import Article

logger = logging.getLogger(__name__)


class ArticleSummarizationService:
    # Lazy loading - chỉ load khi cần
    _tokenizer = None
    _model = None
    _device = None
    _adapter_loaded = False  # True only when PEFT adapter was successfully loaded
    _summary_cache = {}
    _ner_cache = {}
    _ner_client = None

    @classmethod
    def _load_model(cls):
        """Lazy load ViT5 + Q-LoRA adapter. Fallback to base model if adapter missing."""
        if cls._model is not None:
            return

        logger.info("Loading ViT5 base model...")
        cls._device = torch.device("cpu")
        cls._tokenizer = AutoTokenizer.from_pretrained(
            "VietAI/vit5-base-vietnews-summarization"
        )
        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            "VietAI/vit5-base-vietnews-summarization",
            low_cpu_mem_usage=True,
            torch_dtype=torch.float32,
        )

        # Try to load Q-LoRA adapter on top of base model
        adapter_path = Path(settings.ADAPTER_PATH)
        if PEFT_AVAILABLE and adapter_path.exists():
            try:
                cls._model = PeftModel.from_pretrained(base_model, str(adapter_path))
                cls._model.eval()
                cls._adapter_loaded = True
                logger.info("Loaded ViT5 + Q-LoRA adapter from '%s'", adapter_path)
            except Exception as e:
                logger.warning("Failed to load adapter (%s) — using base model", e)
                cls._model = base_model
        else:
            if not PEFT_AVAILABLE:
                logger.warning("peft not installed — using base model without adapter")
            else:
                logger.warning(
                    "Adapter not found at '%s' — using base model", adapter_path
                )
            cls._model = base_model

        cls._model.to(cls._device)

    @classmethod
    def _get_ner_client(cls):
        """Khởi tạo client cho NER API"""
        if cls._ner_client is None:
            logger.info("Initializing NER client...")
            # Lấy API key từ settings nếu có
            api_key = getattr(settings, "HUGGINGFACE_API_KEY", "")
            cls._ner_client = InferenceClient(provider="hf-inference", api_key=api_key)
        return cls._ner_client

    @classmethod
    def chunk_text(cls, text: str, max_tokens: int = 512) -> List[str]:
        """Chia text thành chunks phù hợp với ViT5"""
        cls._load_model()

        # Cải thiện việc split sentences
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # Skip sentences quá ngắn hoặc không có nghĩa
            if len(sentence.strip()) < 10:
                continue

            test_chunk = (current_chunk + " " + sentence).strip()

            # Tokenize để check length chính xác
            token_count = len(
                cls._tokenizer.encode(test_chunk, add_special_tokens=True)
            )

            if token_count > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = test_chunk

        # Add chunk cuối
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    @classmethod
    def chunk_text_for_ner(cls, text: str, max_chars: int = 1800) -> List[str]:
        """Chia text thành chunks phù hợp với NER model (max 512 tokens)"""
        # Cắt câu theo ., !, ? và cả dấu kết thúc kiểu tiếng Việt
        parts = re.split(r"([.!?。]+)", text)
        # Ghép lại để không mất dấu chấm câu
        sentences = []
        for i in range(0, len(parts), 2):
            sent = parts[i].strip()
            punct = parts[i + 1] if i + 1 < len(parts) else ""
            if sent:
                sentences.append((sent + punct).strip())

        chunks = []
        current = ""
        for sent in sentences:
            if current and len(current) + 1 + len(sent) > max_chars:
                chunks.append(current)
                current = sent
            else:
                current = sent if not current else (current + " " + sent)
        if current:
            chunks.append(current)
        return chunks

    @classmethod
    def process_ner(cls, text: str) -> List[Dict[str, Any]]:
        """Xử lý NER cho văn bản, hỗ trợ chunking cho văn bản dài"""
        # Check cache trước
        cache_key = hashlib.md5(text[:1000].encode()).hexdigest()
        if cache_key in cls._ner_cache:
            logger.debug("Using cached NER results")
            return cls._ner_cache[cache_key]

        # Khởi tạo client nếu chưa có
        client = cls._get_ner_client()

        # Chia text thành chunks nhỏ hơn để tránh vượt quá giới hạn token
        chunks = cls.chunk_text_for_ner(text)
        all_entities = []
        offset = 0

        for i, chunk in enumerate(chunks):
            try:
                logger.debug("Processing NER for chunk %s/%s...", i + 1, len(chunks))

                # Gọi API NER
                results = client.token_classification(
                    chunk, model="NlpHUST/ner-vietnamese-electra-base"
                )

                # Điều chỉnh vị trí về theo văn bản gốc
                for entity in results:
                    entity["start"] += offset
                    entity["end"] += offset
                    all_entities.append(entity)

            except Exception:
                logger.warning(
                    "NER error for chunk %s/%s", i + 1, len(chunks), exc_info=True
                )
                continue

            # Cập nhật offset cho chunk tiếp theo
            offset += len(chunk) + 1  # +1 cho khoảng trắng

        # Sắp xếp và gộp các entity liên tiếp cùng loại
        all_entities.sort(key=lambda x: (x.get("start", 0), x.get("end", 0)))
        merged_entities = cls._merge_consecutive_entities(all_entities)

        # Lưu vào cache
        cls._ner_cache[cache_key] = merged_entities

        return merged_entities

    @classmethod
    def _merge_consecutive_entities(
        cls, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Gộp các entity liên tiếp cùng loại"""
        if not entities:
            return entities

        merged = []
        current = entities[0].copy()

        for entity in entities[1:]:
            # Nếu entity liền kề và cùng loại, gộp lại
            if entity.get("start") == current.get("end") and entity.get(
                "entity_group"
            ) == current.get("entity_group"):
                current["end"] = entity["end"]
                current["word"] = current.get("word", "") + entity.get("word", "")
                # Lấy score cao hơn
                current["score"] = max(current.get("score", 0), entity.get("score", 0))
            else:
                merged.append(current)
                current = entity.copy()

        merged.append(current)
        return merged

    @classmethod
    def extract_important_entities(
        cls, entities: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Trích xuất các entity quan trọng theo loại"""
        entity_groups = {}

        # Lọc entity có score cao và phân loại
        for entity in entities:
            if entity.get("score", 0) >= 0.7:  # Chỉ lấy entity có độ tin cậy cao
                group = entity.get("entity_group", "OTHER")
                word = entity.get("word", "").strip()

                if group not in entity_groups:
                    entity_groups[group] = []

                # Chỉ thêm nếu chưa có trong danh sách
                if word and word not in entity_groups[group]:
                    entity_groups[group].append(word)

        return entity_groups

    @classmethod
    def _collect_sapo_pair(cls, article_text: str, sapo: str) -> None:
        """Append (article_body, sapo) pair to JSONL for future Q-LoRA retraining."""
        if not sapo or len(sapo.strip()) < 30:
            return
        pair = {
            "input": article_text[:3000],
            "target": sapo.strip(),
            "source": "sapo",
            "timestamp": datetime.now().isoformat(),
        }
        output_path = Path(settings.SAPO_DATA_PATH)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(output_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            logger.debug("Collected sapo pair (%s chars input)", len(article_text))
        except Exception as e:
            logger.warning("Failed to write sapo pair: %s", e)
            return

        # Auto-push to MinIO when threshold is reached
        threshold = settings.SAPO_AUTO_PUSH_THRESHOLD
        if threshold > 0:
            try:
                line_count = sum(1 for _ in output_path.open(encoding="utf-8"))
                if line_count % threshold == 0:
                    logger.info(
                        "[sapo] Reached %d pairs — triggering auto-push to MinIO",
                        line_count,
                    )
                    cls._auto_push_training_data(output_path)
            except Exception as e:
                logger.warning("[sapo] Auto-push check failed: %s", e)

    @classmethod
    def _auto_push_training_data(cls, data_path: Path) -> None:
        """Push pairs.jsonl to MinIO asynchronously. No-op if MINIO_ENDPOINT_URL not set."""
        import os
        import boto3

        endpoint_url = os.getenv("MINIO_ENDPOINT_URL")
        if not endpoint_url:
            return

        try:
            s3 = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
            )
            bucket = os.getenv("MINIO_BUCKET", "vnnewsvoice-models")
            s3_key = "training-data/pairs.jsonl"
            s3.upload_file(str(data_path), bucket, s3_key)
            logger.info("[sapo] Auto-pushed %s → s3://%s/%s", data_path, bucket, s3_key)
        except Exception as e:
            logger.warning("[sapo] Auto-push to MinIO failed: %s", e)

    @classmethod
    def summarize_text(cls, text: str, max_length: int = 150) -> str:
        """Summarize text: ViT5+adapter PRIMARY → Gemini fallback → emergency.

        Priority order:
          1. ViT5 + Q-LoRA adapter (local, no API cost)
          2. Google Gemini API     (fallback if local model fails)
          3. Emergency             (first 3 sentences)
        """
        # ── Cache check ──────────────────────────────────────────────────────────
        cache_key = hashlib.md5(text[:1000].encode()).hexdigest()
        if cache_key in cls._summary_cache:
            logger.debug("Using cached summary")
            return cls._summary_cache[cache_key]

        cleaned_text = re.sub(r"\s+", " ", text.strip())
        if len(cleaned_text) < 50:
            return "Nội dung quá ngắn để tóm tắt"

        # ── NER extraction (best-effort, không block nếu fail) ──────────────────
        # entity_context = ""
        # important_entities: Dict[str, List[str]] = {}
        # try:
        #     entities = cls.process_ner(cleaned_text)
        #     important_entities = cls.extract_important_entities(entities)
        #     entity_context = " ".join(
        #         f"{g}: {', '.join(ws[:5])}."
        #         for g, ws in important_entities.items()
        #         if ws
        #     )
        #     logger.debug("NER entities: %s", entity_context[:200])
        # except Exception:
        #     logger.warning(
        #         "NER extraction failed — continuing without entities", exc_info=True
        #     )

        entity_context = ""
        important_entities = {}

        provider = "unknown"
        summary = ""
        start_ts = time.time()

        # ── 1. PRIMARY: ViT5 + Q-LoRA adapter ───────────────────────────────────
        try:
            logger.info("[Summarize] Using ViT5 + Q-LoRA adapter (primary)")
            cls._load_model()

            chunks = cls.chunk_text(cleaned_text, max_tokens=256)
            if not chunks:
                raise ValueError("No text chunks produced")

            chunk_summaries: List[str] = []
            for i, chunk in enumerate(chunks):
                if i == 0 and entity_context:
                    chunk = f"Thông tin quan trọng: {entity_context} {chunk}"
                inputs = cls._tokenizer(
                    chunk,
                    return_tensors="pt",
                    max_length=256,
                    truncation=True,
                    padding=True,
                ).to(cls._device)
                with torch.no_grad():
                    output_ids = cls._model.generate(
                        input_ids=inputs["input_ids"],
                        attention_mask=inputs["attention_mask"],
                        max_length=min(max_length, 100),
                        min_length=20,
                        num_beams=2,
                        length_penalty=1.0,
                        early_stopping=True,
                        no_repeat_ngram_size=2,
                        do_sample=False,
                    )
                chunk_summary = cls._tokenizer.decode(
                    output_ids[0], skip_special_tokens=True
                ).strip()
                if len(chunk_summary) > 10:
                    chunk_summaries.append(chunk_summary)

            if not chunk_summaries:
                raise ValueError("All chunks produced empty summaries")

            summary = re.sub(r"\s+", " ", " ".join(chunk_summaries)).strip()

            # Post-process: prepend missing high-importance entities
            for group, words in important_entities.items():
                if group in {"PERSON", "ORGANIZATION", "LOCATION", "MISCELLANEOUS"}:
                    for word in words[:3]:
                        if word and len(word) > 1 and word not in summary:
                            summary = f"{word} ({group}): {summary}"
                            break

            provider = "vit5_adapter" if cls._adapter_loaded else "vit5_base"
            logger.info("[Summarize] %s → %s chars", provider, len(summary))

        except Exception:
            logger.warning(
                "[Summarize] ViT5 failed — falling back to Gemini", exc_info=True
            )

            # ── 2. FALLBACK: Gemini API ──────────────────────────────────────────
            try:
                api_key = settings.GOOGLE_AI_API_KEY_TS
                if not api_key:
                    raise ValueError("GOOGLE_AI_API_KEY_TS not set")

                truncated = (
                    cleaned_text[:8000] + "..."
                    if len(cleaned_text) > 8000
                    else cleaned_text
                )
                prompt = (
                    f"Tóm tắt văn bản sau trong khoảng {max_length} từ. "
                    f"Chú ý các đối tượng: {entity_context}. "
                    "Không bịa đặt thông tin ngoài bài báo.\n\n"
                    f"{truncated}"
                )
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                summary = (response.text or "").strip()
                if not summary:
                    raise ValueError("Empty response from Gemini")
                provider = "gemini"
                logger.info("[Summarize] gemini fallback → %s chars", len(summary))

            except Exception:
                logger.error(
                    "[Summarize] Gemini failed — using emergency fallback",
                    exc_info=True,
                )

                # ── 3. EMERGENCY: first 3 sentences ─────────────────────────────
                sentences = re.split(r"(?<=[.!?])\s+", text.strip())
                valid = [s for s in sentences if len(s.strip()) > 10][:3]
                summary = (
                    (". ".join(valid) + ".") if valid else "Không thể tóm tắt nội dung"
                )
                provider = "emergency"
                logger.warning(
                    "[Summarize] emergency fallback → %s chars", len(summary)
                )

        # ── MLflow tracking (best-effort) ────────────────────────────────────────
        latency_ms = (time.time() - start_ts) * 1000
        if MLFLOW_AVAILABLE and getattr(settings, "MLFLOW_ENABLED", False):
            try:
                mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
                mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)
                with mlflow.start_run(run_name=f"inference_{provider}", nested=True):
                    mlflow.log_param("provider", provider)
                    mlflow.log_metric("latency_ms", latency_ms)
                    mlflow.log_metric("input_chars", len(cleaned_text))
                    mlflow.log_metric("output_chars", len(summary))
                    mlflow.log_metric(
                        "compression_ratio", len(summary) / max(len(cleaned_text), 1)
                    )
                    mlflow.log_metric(
                        "fallback_to_gemini", 1 if provider == "gemini" else 0
                    )
            except Exception:
                logger.debug("MLflow tracking failed (non-critical)", exc_info=True)

        # Cache and return (don't cache emergency summaries)
        if provider != "emergency" and summary:
            cls._summary_cache[cache_key] = summary
        return summary or "Không thể tóm tắt nội dung"

    # Thêm phương thức để quản lý cache
    @classmethod
    def clear_old_cache(cls, max_age_minutes=60):
        """Clear cache entries older than max_age_minutes"""
        if not hasattr(cls, "_cache_timestamps"):
            cls._cache_timestamps = {}
        if not hasattr(cls, "_ner_cache_timestamps"):
            cls._ner_cache_timestamps = {}

        current_time = datetime.now()
        expired_summary_keys = []
        expired_ner_keys = []

        # Xử lý cache tóm tắt
        for key in cls._summary_cache:
            if key not in cls._cache_timestamps:
                cls._cache_timestamps[key] = current_time
                continue

            timestamp = cls._cache_timestamps[key]
            age = current_time - timestamp

            if age > timedelta(minutes=max_age_minutes):
                expired_summary_keys.append(key)

        # Xử lý cache NER
        for key in cls._ner_cache:
            if key not in cls._ner_cache_timestamps:
                cls._ner_cache_timestamps[key] = current_time
                continue

            timestamp = cls._ner_cache_timestamps[key]
            age = current_time - timestamp

            if age > timedelta(minutes=max_age_minutes):
                expired_ner_keys.append(key)

        # Xóa các cache hết hạn
        for key in expired_summary_keys:
            if key in cls._summary_cache:
                del cls._summary_cache[key]
            if key in cls._cache_timestamps:
                del cls._cache_timestamps[key]

        for key in expired_ner_keys:
            if key in cls._ner_cache:
                del cls._ner_cache[key]
            if key in cls._ner_cache_timestamps:
                del cls._ner_cache_timestamps[key]

        logger.info("Cleared %s old summary cache entries", len(expired_summary_keys))
        logger.info("Cleared %s old NER cache entries", len(expired_ner_keys))

    @classmethod
    def summarize_article(cls, article: Article, max_length: int = 200) -> str:
        """Tóm tắt Article object với nhấn mạnh các đối tượng quan trọng"""
        if not article.blocks:
            return "Không có nội dung để tóm tắt"

        # Extract only paragraph content + filter quality
        paragraphs = []
        for block in article.blocks:
            paragraph_text = block.text or block.content
            if (
                block.type == "paragraph"
                and paragraph_text
                and len(paragraph_text.strip()) > 20
            ):  # Skip very short paragraphs
                paragraphs.append(paragraph_text.strip())

        if not paragraphs:
            return "Không có đoạn văn để tóm tắt"

        full_text = " ".join(paragraphs)

        # Add context với title
        if article.title:
            full_text = f"Tiêu đề: {article.title}. Nội dung: {full_text}"

        return cls.summarize_text(full_text, max_length)

    @classmethod
    def cleanup_model(cls):
        """Cleanup model để giải phóng memory"""
        if cls._model is not None:
            del cls._model
            cls._model = None
        if cls._tokenizer is not None:
            del cls._tokenizer
            cls._tokenizer = None
        if cls._ner_client is not None:
            cls._ner_client = None
        cls._adapter_loaded = False
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        logger.info("Model cleaned up")
