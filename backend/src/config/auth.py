import os
from dotenv import load_dotenv

load_dotenv()


def verify_api_key(api_key: str) -> bool:
    """Verify an API key against the configured key."""
    expected_key = os.getenv("API_KEY", "")
    if not expected_key:
        return True  # No key configured, allow all
    return api_key == expected_key


class APIKeyValidator:
    """Validator for API keys."""

    @staticmethod
    def is_valid_request(api_key: str) -> bool:
        return verify_api_key(api_key)
