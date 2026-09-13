"""Cloudflare R2 helpers for MusicAdPromo artifacts."""

import os

import boto3
from botocore.config import Config


def _get_client():
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_image(local_path: str, job_id: str) -> str:
    bucket = os.environ["R2_BUCKET_NAME"]
    key = f"storyboards/{job_id}.png"
    _get_client().upload_file(local_path, bucket, key, ExtraArgs={"ContentType": "image/png"})
    return key


def upload_audio(local_path: str, job_id: str, content_type: str = "audio/mpeg") -> str:
    bucket = os.environ["R2_BUCKET_NAME"]
    ext = os.path.splitext(local_path)[1] or ".audio"
    key = f"audio/{job_id}{ext}"
    _get_client().upload_file(local_path, bucket, key, ExtraArgs={"ContentType": content_type})
    return key


def upload_video(local_path: str, job_id: str) -> str:
    bucket = os.environ["R2_BUCKET_NAME"]
    key = f"videos/{job_id}.mp4"
    _get_client().upload_file(local_path, bucket, key, ExtraArgs={"ContentType": "video/mp4"})
    return key


def download_object(key: str, local_path: str) -> str:
    bucket = os.environ["R2_BUCKET_NAME"]
    _get_client().download_file(bucket, key, local_path)
    return local_path


def get_download_url(key: str, expires_in: int = 3600) -> str:
    bucket = os.environ["R2_BUCKET_NAME"]
    return _get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )
