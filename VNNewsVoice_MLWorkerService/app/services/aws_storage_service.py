import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from app.core.config import settings
from typing import Optional
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


class S3StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def upload_audio(self, audio_data: bytes, filename: str = None) -> Optional[dict]:
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"tts_{timestamp}.wav"

            # Ensure filename ends with .wav
            if not filename.endswith(".wav"):
                filename = f"{filename}.wav"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=audio_data,
                ContentType="audio/wav",
                CacheControl="max-age=86400",
                Metadata={
                    "uploaded_by": "tts-service",
                    "created_at": datetime.now().isoformat(),
                },
            )

            # Generate URL
            audio_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"

            result = {
                "status": "success",
                "audio_url": audio_url,
                "filename": filename,
                "bucket": self.bucket_name,
                "bytes": len(audio_data),
                "format": "wav",
                "created_at": datetime.now().isoformat(),
                "cloud_provider": "aws_s3",
            }

            logger.info("Audio uploaded to S3: %s", audio_url)
            return result

        except NoCredentialsError:
            logger.warning("AWS credentials not found")
            return None
        except PartialCredentialsError:
            logger.warning("Incomplete AWS credentials")
            return None
        except Exception:
            logger.exception("S3 upload error")
            return None

    def delete_audio(self, filename: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
            logger.info("Audio deleted from S3: %s", filename)
            return True

        except Exception:
            logger.exception("S3 delete error")
            return False

    def delete_audio_by_url(self, audio_url: str) -> bool:
        try:
            filename = self.extract_filename_from_url(audio_url)
            if not filename:
                logger.warning("Could not extract filename from URL")
                return False

            return self.delete_audio(filename)

        except Exception:
            logger.exception("Delete by URL error")
            return False

    def extract_filename_from_url(self, url: str) -> str:
        """Extract filename from S3 URL"""
        try:
            if "amazonaws.com" not in url:
                raise ValueError("Not an S3 URL")

            # Extract filename from URL
            filename = url.split("/")[-1]
            logger.debug("Extracted filename: %s", filename)
            return filename

        except Exception:
            logger.exception("Error extracting filename from URL '%s'", url)
            return ""

    def list_audio_files(self, prefix: str = "") -> list:
        """List all audio files in bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    if obj["Key"].endswith(".wav"):
                        files.append(
                            {
                                "filename": obj["Key"],
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"].isoformat(),
                                "url": f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{obj['Key']}",
                            }
                        )

            logger.info("Found %s audio files", len(files))
            return files

        except Exception:
            logger.exception("Error listing files")
            return []

    def search_and_delete_audio(self, filename_pattern: str) -> bool:
        """Search for audio file then delete it"""
        try:
            files = self.list_audio_files()

            for file in files:
                if filename_pattern in file["filename"]:
                    logger.info("Found match: %s", file["filename"])
                    return self.delete_audio(file["filename"])

            logger.warning("No matching files found for: %s", filename_pattern)
            return False

        except Exception:
            logger.exception("Search and delete error")
            return False
