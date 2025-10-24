"""Utility functions for client operations."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any


def image_to_data_url(image_path: str | Path) -> str:
    """Convert image file to base64 data URL.

    Args:
        image_path: Path to the image file

    Returns:
        Base64-encoded data URL

    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If file extension is not supported
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with open(path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Determine mime type from extension
    ext = path.suffix.lower().lstrip(".")
    mime_type = {
        "jpg": "jpeg",
        "jpeg": "jpeg",
        "png": "png",
        "webp": "webp",
        "gif": "gif",
    }.get(ext, "jpeg")  # Default to jpeg

    return f"data:image/{mime_type};base64,{encoded_image}"


def generate_ai_filename(model_name: str, extension: str = "png") -> str:
    """Generate standardized filename for AI-generated images.

    Format: YYYY-MM-DD-{model-name}-UUID.{ext}

    Args:
        model_name: Name of the AI model (e.g., "seedream-v4", "google:4@1")
        extension: File extension (default: "png")

    Returns:
        Standardized filename with timestamp, model name, and UUID
    """
    import uuid
    from datetime import datetime

    date_str = datetime.now().strftime("%Y-%m-%d")
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID

    # Make model name filename-safe: replace special chars with hyphens
    safe_model_name = model_name.replace(":", "-").replace("@", "at").replace("_", "-")

    # Remove any consecutive hyphens
    while "--" in safe_model_name:
        safe_model_name = safe_model_name.replace("--", "-")

    return f"{date_str}-{safe_model_name}-{unique_id}.{extension}"


def sanitize_model_name(model_name: str) -> str:
    """Sanitize model name for use in filenames.

    Args:
        model_name: Raw model name

    Returns:
        Sanitized model name safe for filenames
    """
    # Replace special characters with hyphens
    safe_name = model_name.replace(":", "-").replace("@", "at").replace("_", "-")

    # Remove any consecutive hyphens
    while "--" in safe_name:
        safe_name = safe_name.replace("--", "-")

    return safe_name


def truncate_data_url(data_url: str, max_length: int = 100) -> str:
    """Truncate data URL for logging purposes.

    Args:
        data_url: Full data URL
        max_length: Maximum length to keep

    Returns:
        Truncated data URL with preview
    """
    if len(data_url) <= max_length:
        return data_url
    return data_url[:max_length] + "..."


def calculate_payload_size(payload: dict[str, Any]) -> int:
    """Calculate approximate payload size in KB.

    Args:
        payload: Dictionary payload

    Returns:
        Size in KB
    """
    import json

    return len(json.dumps(payload)) // 1024
