"""
Rate limiting for codemap API endpoints.

Uses a simple in-memory rate limiter with sliding window.
"""

import time
import logging
from collections import defaultdict
from functools import wraps
from typing import Dict, Tuple, Callable
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter with sliding window algorithm.
    """
    
    def __init__(self):
        # Dict[key, List[timestamp]]
        self._requests: Dict[str, list] = defaultdict(list)
    
    def _clean_old_requests(self, key: str, window_seconds: int):
        """Remove requests older than the window."""
        now = time.time()
        cutoff = now - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Check if a request is allowed under the rate limit.
        
        Args:
            key: Unique identifier (e.g., IP address)
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        self._clean_old_requests(key, window_seconds)
        
        if len(self._requests[key]) >= max_requests:
            # Calculate retry after
            oldest = min(self._requests[key]) if self._requests[key] else time.time()
            retry_after = int(oldest + window_seconds - time.time()) + 1
            return False, max(1, retry_after)
        
        self._requests[key].append(time.time())
        return True, 0
    
    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get remaining requests in the current window."""
        self._clean_old_requests(key, window_seconds)
        return max(0, max_requests - len(self._requests[key]))


# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limit configurations
RATE_LIMITS = {
    "generate": (5, 60),      # 5 requests per minute
    "get": (60, 60),          # 60 requests per minute
    "list": (30, 60),         # 30 requests per minute
    "share": (10, 60),        # 10 requests per minute
    "export": (20, 60),       # 20 requests per minute
}


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for X-Forwarded-For header (common with proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


def rate_limit(endpoint_name: str):
    """
    Decorator to apply rate limiting to an endpoint.
    
    Args:
        endpoint_name: Name of the endpoint for rate limit configuration
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if endpoint_name not in RATE_LIMITS:
                # No rate limit configured, allow request
                return await func(request, *args, **kwargs)
            
            max_requests, window_seconds = RATE_LIMITS[endpoint_name]
            client_ip = get_client_ip(request)
            key = f"{endpoint_name}:{client_ip}"
            
            allowed, retry_after = rate_limiter.is_allowed(key, max_requests, window_seconds)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint_name}")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "message": "Rate limit exceeded. Please try again later.",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_rate_limit(request: Request, endpoint_name: str) -> None:
    """
    Check rate limit for an endpoint (for use without decorator).
    
    Args:
        request: FastAPI request object
        endpoint_name: Name of the endpoint
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    if endpoint_name not in RATE_LIMITS:
        return
    
    max_requests, window_seconds = RATE_LIMITS[endpoint_name]
    client_ip = get_client_ip(request)
    key = f"{endpoint_name}:{client_ip}"
    
    allowed, retry_after = rate_limiter.is_allowed(key, max_requests, window_seconds)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint_name}")
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Rate limit exceeded. Please try again later.",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )
