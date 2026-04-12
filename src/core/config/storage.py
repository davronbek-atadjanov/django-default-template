import os


def _read_secret(name: str, default: str = "") -> str:
    val = os.getenv(name)
    if val:
        return val
    secret_path = f"/run/secrets/{name.lower()}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return default


_s3_enabled = os.getenv("S3_ENABLED", "False").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

if _s3_enabled:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": _read_secret("S3_ACCESS_KEY", "minioadmin"),
                "secret_key": _read_secret("S3_SECRET_KEY", "minioadmin"),
                "bucket_name": os.getenv("S3_BUCKET_NAME", "novda-media"),
                "endpoint_url": os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"),
                "custom_domain": os.getenv("S3_CUSTOM_DOMAIN") or None,
                "region_name": os.getenv("S3_REGION_NAME", "us-east-1"),
                "use_ssl": os.getenv("S3_USE_SSL", "False").strip().lower() in {"1", "true", "yes", "on"},
                "querystring_auth": os.getenv("S3_QUERYSTRING_AUTH", "False").strip().lower()
                in {"1", "true", "yes", "on"},
                "file_overwrite": False,
                "default_acl": "public-read",
                "object_parameters": {
                    "CacheControl": "max-age=86400",
                },
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
