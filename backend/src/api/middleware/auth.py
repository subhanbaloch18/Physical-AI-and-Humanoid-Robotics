from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from ...config.auth import verify_api_key


# Initialize the security scheme
security = HTTPBearer()


def get_api_key_header(request: Request) -> Optional[str]:
    """
    Extract the API key from the Authorization header.

    Args:
        request: The incoming request

    Returns:
        The API key if present, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix
    return None


def verify_api_key_from_request(request: Request) -> bool:
    """
    Verify the API key from the request.

    Args:
        request: The incoming request

    Returns:
        True if the API key is valid, raises HTTPException otherwise
    """
    api_key = get_api_key_header(request)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key in Authorization header"
        )

    # Use the authentication function from the config module
    try:
        verify_api_key_from_config(api_key)
        return True
    except HTTPException:
        raise


def verify_api_key_from_config(api_key: str) -> bool:
    """
    Verify the API key using the config module.

    Args:
        api_key: The API key to verify

    Returns:
        True if the API key is valid
    """
    from ...config.auth import APIKeyValidator

    if not APIKeyValidator.is_valid_request(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return True


async def api_key_auth_middleware(request: Request, call_next):
    """
    Middleware to verify API key for protected endpoints.

    Args:
        request: The incoming request
        call_next: The next middleware in the chain

    Returns:
        The response from the next middleware or an error response
    """
    logger = logging.getLogger(__name__)

    # List of endpoints that don't require authentication
    public_endpoints = ["/", "/health", "/docs", "/redoc", "/openapi.json"]

    # Check if the request path is a public endpoint
    if request.url.path in public_endpoints:
        return await call_next(request)

    # For all other endpoints, verify the API key
    try:
        verify_api_key_from_request(request)
        response = await call_next(request)
        return response
    except HTTPException as e:
        logger.warning(f"Unauthorized access attempt to {request.url.path}")
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )


class APIKeyAuth:
    """
    A class to handle API key authentication for endpoints.
    """

    def __init__(self, auto_error: bool = True):
        """
        Initialize the API key authentication.

        Args:
            auto_error: Whether to automatically raise an HTTPException on invalid key
        """
        self.auto_error = auto_error
        self.security = HTTPBearer(auto_error=auto_error)

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> Optional[str]:
        """
        Authenticate the request using API key.

        Args:
            request: The incoming request
            credentials: The HTTP authorization credentials

        Returns:
            The API key if authentication is successful, None if auto_error is False and authentication fails
        """
        if credentials:
            api_key = credentials.credentials
        else:
            # Extract from header if not provided via FastAPI's security
            api_key = get_api_key_header(request)

        if not api_key:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing API key in Authorization header"
                )
            else:
                return None

        # Validate the API key
        if not verify_api_key_from_config(api_key):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            else:
                return None

        return api_key


# Create a reusable API key dependency
api_key_auth = APIKeyAuth()