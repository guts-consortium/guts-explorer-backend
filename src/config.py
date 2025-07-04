import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration for the Flask Application"""
    FLASK_ENV = os.getenv('FLASK_ENV')
    FRONTEND_URL = os.getenv('FRONTEND_URL')
    # Signing sessions
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    # SRAM OIDC interaction
    OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID')
    OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET')
    OIDC_AUTHORIZATION_ENDPOINT = os.getenv('OIDC_AUTHORIZATION_ENDPOINT')
    OIDC_TOKEN_ENDPOINT = os.getenv('OIDC_TOKEN_ENDPOINT')
    OIDC_USERINFO_ENDPOINT = os.getenv('OIDC_USERINFO_ENDPOINT')
    OIDC_REVOKE_ENDPOINT = os.getenv('OIDC_REVOKE_ENDPOINT')
    OIDC_REDIRECT_URI = os.getenv('OIDC_REDIRECT_URI')
    # SRAM collaboration user management
    SRAM_USER_ENDPOINT = os.getenv('SRAM_USER_ENDPOINT')
    # Neptune API interaction
    NEPTUNE_BASE_URL = os.getenv('NEPTUNE_BASE_URL')
    NEPTUNE_USERNAME = os.getenv('NEPTUNE_USERNAME')
    NEPTUNE_PASSWORD = os.getenv('NEPTUNE_PASSWORD')
    NEPTUNE_CERT_PATH = os.getenv('NEPTUNE_CERT_PATH')
    # Flask session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'  # True in production
    MSGRAPH_TENANT_ID = os.getenv('MSGRAPH_TENANT_ID')
    MSGRAPH_CLIENT_ID = os.getenv('MSGRAPH_CLIENT_ID')
    MSGRAPH_CLIENT_SECRET = os.getenv('MSGRAPH_CLIENT_SECRET')
