import os, hmac, hashlib, time, uuid
from io import BytesIO
from typing import Tuple
from sqlalchemy.orm import Session
from ..models.media import Media

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

class MediaService:
    SIGNING_KEY = os.getenv("MEDIA_SIGNING_KEY", "dev-media-signing-key")
    BASE_URL = os.getenv("MEDIA_BASE_URL", "http://localhost:8000/media/files")
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
    S3_ENDPOINT = os.getenv("S3_ENDPOINT")
    MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", str(10 * 1024 * 1024)))
    MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", "25000000"))

    @classmethod
    def _require_storage_config(cls):
        if not cls.SIGNING_KEY or not cls.BASE_URL:
            raise RuntimeError("MEDIA_SIGNING_KEY and MEDIA_BASE_URL must be configured")
        if not BOTO3_AVAILABLE and os.getenv("APP_ENV", "development") == "production":
            raise RuntimeError("boto3 is required for production media storage")

    @classmethod
    def sign_path(cls, path: str, expiration_seconds: int = 3600) -> str:
        cls._require_storage_config()
        expires = int(time.time()) + expiration_seconds
        signature = hmac.new(cls.SIGNING_KEY.encode(), f"{path}:{expires}".encode(), hashlib.sha256).hexdigest()
        return f"{cls.BASE_URL.rstrip('/')}/{path}?expires={expires}&signature={signature}"

    @classmethod
    def generate_signed_url(cls, media: Media, expiration_seconds: int = 3600) -> str:
        return cls.sign_path(media.file_path, expiration_seconds)

    @classmethod
    def verify_url_signature(cls, file_path: str, expires: str, signature: str) -> bool:
        try:
            exp = int(expires)
            if time.time() > exp or not cls.SIGNING_KEY:
                return False
            expected = hmac.new(cls.SIGNING_KEY.encode(), f"{file_path}:{exp}".encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except (ValueError, TypeError):
            return False

    @classmethod
    def validate_image(cls, content: bytes, declared_mime: str) -> str:
        if len(content) > cls.MAX_IMAGE_BYTES:
            raise ValueError("File size exceeds the configured limit")
        if not declared_mime or not declared_mime.startswith("image/"):
            raise ValueError("Only image files are allowed")
        from PIL import Image, ImageOps, UnidentifiedImageError
        try:
            with Image.open(BytesIO(content)) as image:
                if image.width * image.height > cls.MAX_IMAGE_PIXELS:
                    raise ValueError("Image dimensions are too large")
                image.verify()
            with Image.open(BytesIO(content)) as image:
                actual = ImageOps.exif_transpose(image)
                fmt = (actual.format or "").upper()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError("Invalid image content") from exc
        allowed = {"JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif", "WEBP": "image/webp"}
        detected_mime = allowed.get(fmt)
        if not detected_mime or detected_mime != declared_mime.lower():
            raise ValueError("File content does not match its declared image type")
        return detected_mime

    @classmethod
    def upload_file(cls, file_content: bytes, mime_type: str, couple_id: str, owner_id: str) -> Tuple[str, str]:
        if len(file_content) > cls.MAX_IMAGE_BYTES:
            raise ValueError("File too large")
        extension = {"image/jpeg":"jpg","image/png":"png","image/gif":"gif","image/webp":"webp"}.get(mime_type, "bin")
        name = f"{uuid.uuid4()}.{extension}"
        if not BOTO3_AVAILABLE:
            storage_dir = "storage/media"; os.makedirs(storage_dir, exist_ok=True)
            path = os.path.join(storage_dir, name)
            with open(path, "wb") as f: f.write(file_content)
            return path, "local-etag"
        if not cls.S3_BUCKET or not cls.S3_ACCESS_KEY or not cls.S3_SECRET_KEY:
            raise RuntimeError("S3 storage credentials are not configured")
        key = f"couples/{couple_id}/{name}"
        s3 = boto3.client("s3", aws_access_key_id=cls.S3_ACCESS_KEY, aws_secret_access_key=cls.S3_SECRET_KEY, endpoint_url=cls.S3_ENDPOINT)
        try:
            result = s3.put_object(Bucket=cls.S3_BUCKET, Key=key, Body=file_content, ContentType=mime_type)
            return key, result.get("ETag", "").strip('"')
        except ClientError as exc:
            raise RuntimeError("S3 upload failed") from exc

    @classmethod
    def generate_thumbnail(cls, file_content: bytes, mime_type: str, couple_id: str, media_id: str) -> str:
        from PIL import Image, ImageOps, UnidentifiedImageError
        try:
            with Image.open(BytesIO(file_content)) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail((512, 512))
                out = BytesIO(); image.save(out, format="JPEG", quality=85, optimize=True)
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError("Invalid image content") from exc
        data = out.getvalue(); key = f"couples/{couple_id}/thumbnails/{media_id}.jpg"
        if not BOTO3_AVAILABLE:
            path = os.path.join("storage/media", "thumbnails", f"{media_id}.jpg")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f: f.write(data)
            return path
        s3 = boto3.client("s3", aws_access_key_id=cls.S3_ACCESS_KEY, aws_secret_access_key=cls.S3_SECRET_KEY, endpoint_url=cls.S3_ENDPOINT)
        s3.put_object(Bucket=cls.S3_BUCKET, Key=key, Body=data, ContentType="image/jpeg")
        return key

    @classmethod
    def download_file(cls, file_path: str) -> bytes:
        if not BOTO3_AVAILABLE or file_path.startswith("storage/"):
            with open(file_path, "rb") as f: return f.read()
        s3 = boto3.client("s3", aws_access_key_id=cls.S3_ACCESS_KEY, aws_secret_access_key=cls.S3_SECRET_KEY, endpoint_url=cls.S3_ENDPOINT)
        return s3.get_object(Bucket=cls.S3_BUCKET, Key=file_path)["Body"].read()
