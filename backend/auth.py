"""
API Authentication and Security
"""

from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
from config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Verify API key from request header

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    # In development mode, API key is optional
    if settings.debug and not settings.api_key:
        return "development"

    # In production, API key is required
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate API key
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


# Optional API key (for endpoints that work both with and without auth)
async def optional_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
) -> Optional[str]:
    """
    Optional API key verification

    Returns None if no key is provided, validates if provided
    """
    if not api_key:
        return None

    # If key is provided, validate it
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


# Dependency for protected endpoints
def require_auth():
    """Dependency that requires authentication"""
    return Depends(verify_api_key)


# Dependency for optional auth
def optional_auth():
    """Dependency for optional authentication"""
    return Depends(optional_api_key)
