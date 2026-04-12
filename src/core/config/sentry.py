import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


def _read_secret(name: str, default: str = "") -> str:
    val = os.getenv(name)
    if val:
        return val
    secret_path = f"/run/secrets/{name.lower()}"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    return default


_raw_traces_rate = os.getenv("SENTRY_TRACES_SAMPLE_RATE")
try:
    traces_sample_rate: float = float(_raw_traces_rate) if _raw_traces_rate is not None else 1.0
except ValueError:
    traces_sample_rate = 1.0

sentry_sdk.init(
    dsn=_read_secret("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=traces_sample_rate,
    profile_session_sample_rate=traces_sample_rate,
    profile_lifecycle="trace",
    send_default_pii=True,
    enable_logs=True,
    environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
)
