import requests
import secrets
import hashlib
import base64
from urllib.parse import urlencode
from flask import session


def generate_code_verifier():
    """Generates a code verifier string of between 43-128 characters."""
    return secrets.token_urlsafe(96)


def calculate_code_challenge(code_verifier):
    """Generates the code challenge from the code verifier using SHA256 and Base64 URL encoding."""
    code_verifier_bytes = code_verifier.encode('utf-8')
    code_challenge_sha256 = hashlib.sha256(code_verifier_bytes).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge_sha256).rstrip(b'=').decode('utf-8')
    return code_challenge


def get_auth_url(config):
    """Generate the OIDC authorization URL for user login."""
    code_verifier = generate_code_verifier()
    pkce_challenge = calculate_code_challenge(code_verifier)
    session['code_verifier'] = code_verifier
    params = {
        'client_id': config['OIDC_CLIENT_ID'],
        'response_type': 'code',
        'redirect_uri': config['OIDC_REDIRECT_URI'],
        'scope': 'openid profile email',
        'code_challenge_method': 'S256',
        'code_challenge': pkce_challenge
    }
    return f"{config['OIDC_AUTHORIZATION_ENDPOINT']}?{urlencode(params)}"


def get_oidc_token(config, code):
    """Exchange the authorization code for an access token and ID token."""
    # First retrieve the stored code verifier from the session
    code_verifier = session.get('code_verifier')
    data = {
        'client_id': config['OIDC_CLIENT_ID'],
        'client_secret': config['OIDC_CLIENT_SECRET'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': config['OIDC_REDIRECT_URI'],
        'code_verifier': code_verifier 
    }
    response = requests.post(
        config['OIDC_TOKEN_ENDPOINT'],
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    if response.status_code == 200:
        return response.json()  # Contains access_token and id_token
    return None


def get_user_info(config, access_token):
    """Fetch the user info from the OIDC userinfo endpoint using the access token."""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        config['OIDC_USERINFO_ENDPOINT'],
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None


def revoke_oidc_token(config, access_token):
    """Revoke the OIDC access token when logging out."""
    data = {
        'token': access_token,
        'client_id': config['OIDC_CLIENT_ID'],
        'client_secret': config['OIDC_CLIENT_SECRET']
    }
    response = requests.post(
        config['OIDC_REVOKE_ENDPOINT'],
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    return response.status_code == 200
