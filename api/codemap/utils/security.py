"""
Security utilities for codemap operations.
"""

import re
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact sensitive fields from data before logging.

    Args:
        data: Dictionary that may contain sensitive fields

    Returns:
        Copy of data with sensitive fields redacted
    """
    sensitive_fields = {'token', 'access_token', 'api_key', 'password', 'secret', 'authorization'}

    def redact_value(key: str, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: redact_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [redact_value(key, v) for v in value]
        elif isinstance(value, str) and key.lower() in sensitive_fields:
            if len(value) > 8:
                return f"{value[:4]}...{value[-4:]}"
            return "***REDACTED***"
        return value

    return {k: redact_value(k, v) for k, v in data.items()}


def safe_log_request(request_data: Dict[str, Any], message: str = "Request"):
    """
    Log request data with sensitive fields redacted.
    
    Args:
        request_data: Dictionary containing request data
        message: Log message prefix
    """
    safe_data = redact_sensitive_data(request_data)
    logger.info(f"{message}: {safe_data}")


class TokenRedactingFilter(logging.Filter):
    """
    Logging filter that redacts tokens from log messages.
    """

    TOKEN_PATTERNS = [
        r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
        r'glpat-[a-zA-Z0-9-]{20}',  # GitLab PAT
        r'github_pat_[a-zA-Z0-9_]{22,}',  # GitHub Fine-grained PAT
        r'gho_[a-zA-Z0-9]{36}',  # GitHub OAuth
        r'ghu_[a-zA-Z0-9]{36}',  # GitHub User-to-server
        r'ghs_[a-zA-Z0-9]{36}',  # GitHub Server-to-server
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self.TOKEN_PATTERNS:
            message = re.sub(pattern, '***REDACTED***', message, flags=re.IGNORECASE)
        record.msg = message
        record.args = ()
        return True


def redact_token_from_url(url: str) -> str:
    """
    Redact token query parameter from URL.
    
    Args:
        url: URL that may contain token parameter
        
    Returns:
        URL with token redacted
    """
    return re.sub(r'([?&])token=[^&]+', r'\1token=***REDACTED***', url)
