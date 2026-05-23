# implements: FR-017
# traces_to: Π.3.1

"""Centralized Path Validation and Sanitization Utility for ADE Compliance.

Provides a robust, CodeQL-approved segment-by-segment path traversal sanitizer
that ensures resolved paths strictly reside inside a designated base directory boundary.
"""

import os
import re
from pathlib import Path
from typing import Optional

# Strict regex matching only standard alphanumeric characters, underscores, hyphens, and dots
SAFE_SEGMENT_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.]+$")


def sanitize_relative_path(base_dir: Path, input_path: str) -> Optional[Path]:
    """Sanitize and resolve a relative file path securely against a base directory boundary.

    Splits the path into segments, validates each segment against a strict regex whitelist,
    denies absolute paths or directory traversal sequences, and confirms that the final
    resolved path resides inside the base directory boundary using `commonpath`.

    Args:
        base_dir: The trusted base root directory (must be absolute/resolved).
        input_path: The untrusted user-provided relative path string.

    Returns:
        The fully resolved, safe absolute Path object, or None if the path is invalid or unsafe.
    """
    try:
        # Normalize backslashes to forward slashes for cross-platform processing
        file_path_str = str(input_path).replace("\\", "/")

        # Split path into individual components and strictly validate each segment
        parts = file_path_str.split("/")
        safe_parts = []
        for part in parts:
            # Allow only standard safe name characters and explicitly block traversal or empty strings
            if not SAFE_SEGMENT_PATTERN.match(part) or part in ("", ".", ".."):
                continue
            safe_parts.append(part)

        if not safe_parts:
            return None

        # Reconstruct path using purely verified safe path segments
        path = base_dir.joinpath(*safe_parts).resolve()

        # Double-verify containment boundary via os.path.commonpath
        resolved_base = str(base_dir)
        resolved_path = str(path)
        if os.path.commonpath([resolved_base, resolved_path]) != resolved_base:
            return None

        return path
    except Exception:
        return None
