"""Compatibility aliases for the shared JWT implementation."""
from app.auth.jwt_handler import create_access_token, verify_token

verify_access_token = verify_token
