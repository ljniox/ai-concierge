import os
from datetime import datetime


def get_version_info():
    app_version = os.getenv("APP_VERSION", "unknown")
    git_sha = os.getenv("GIT_SHA", app_version)
    build_time = os.getenv("BUILD_TIME", "unknown")
    tz = os.getenv("TZ", "UTC")

    return {
        "app": "ai-concierge-webhook",
        "version": app_version,
        "git_sha": git_sha,
        "build_time": build_time,
        "tz": tz,
    }

