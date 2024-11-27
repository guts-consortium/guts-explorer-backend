# Check env file
from pathlib import Path
repo_path = Path(__file__).resolve().parent.parent

if not (repo_path / ".env" ).exists():
    raise ValueError("No '.env' file find in backend root directory; this file is required")

# Imports
from api_utils import (
    load_metadata,
)
from config import Config
from flask import (
    abort,
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_cors import CORS
from oidc_utils import (
    get_oidc_token,
    get_user_info,
    revoke_oidc_token,
    get_auth_url,
)

from neptune_utils import (
    check_user,
    delete_user,
    invite_user,
    create_neptune_data_request,
)

# Setup flask app
app = Flask(__name__)

# Load configuration from config.py
app.config.from_object(Config)

# Ensure Flask secret key is set for the app
if not app.config['FLASK_SECRET_KEY']:
    raise ValueError("No SECRET_KEY set for Flask application. Did you forget to configure it?")

app.secret_key = app.config['FLASK_SECRET_KEY']

# Add CORS to allow requests from frontend
CORS(app, origins=[app.config['FRONTEND_URL']], supports_credentials=True)


# API
@app.route('/api/user/<email>', methods=['GET', 'POST', 'DELETE'])
def user(email):
    """"""
    if request.method == 'POST':
        return jsonify(invite_user(email))
    if request.method == 'GET':
        return jsonify(check_user(email))
    if request.method == 'DELETE':
        return jsonify(delete_user(email))


@app.route('/api/login')
def login():
    """Initiate the OIDC login process by redirecting the user to the authorization URL."""
    authorization_url = get_auth_url(app.config)
    return redirect(authorization_url)


@app.route('/api/callback')
def oidc_callback():
    """Handle the OIDC callback after the user has authenticated."""
    print("Received callback via GUTS explorer app from OIDC")
    code = request.args.get('code')
    if not code:
        print("No code in callback")
        return jsonify({'error': 'No authorization code found'}), 400
    # Exchange the authorization code for access and ID tokens
    tokens = get_oidc_token(app.config, code)

    if 'access_token' in tokens:
        print("\nReceived access token!!!\n")
        # Store tokens securely in the session (server-side)
        session['access_token'] = tokens['access_token']
        session['id_token'] = tokens['id_token']
        session['is_authenticated'] = True
        
        # Fetch user profile info from the OIDC UserInfo endpoint
        user_info = get_user_info(app.config, tokens['access_token'])
        print(f"\n\nReceived user info:\n{user_info['name']}\n{user_info['email']}\n\n")
        if user_info:
            session['user_profile'] = user_info  # Store user profile in session
            # Redirect back to the frontend, include the profile info
            return render_template('redirect_user_info.html', userinfo=user_info)
        else:
            return jsonify({'error': 'Failed to fetch user information'}), 400

    return jsonify({'error': 'Failed to obtain OIDC tokens'}), 400


@app.route('/api/profile')
def profile():
    """Fetch and return the user's profile information using the OIDC access token."""
    if not session.get('is_authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    access_token = session.get('access_token')
    user_info = get_user_info(app.config, access_token)
    if user_info:
        return jsonify(user_info)
    return jsonify({'error': 'Failed to fetch user info'}), 400


@app.route('/api/logout')
def logout():
    """Log the user out by revoking the OIDC token and clearing the session."""
    access_token = session.pop('access_token', None)
    if access_token:
        revoke_oidc_token(app.config, access_token)
    session.clear()  # Clear all session data (including tokens)
    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/api/submit', methods=['POST'])
def create_data_request():
    """Handle form submissions from the frontend and forward them securely to
    to the external Neptune API."""
    print("Session contents: ", dict(session))
    if not session.get('is_authenticated'):
        print("!User is not authenticated!")
        return jsonify({'error': 'Not authenticated'}), 401

    incoming_data = request.json  # Data coming in from the frontend POST
    print("Received data request payload from frontend:")
    print(incoming_data)
    api_response = create_neptune_data_request(incoming_data)

    if api_response.status_code == 200:
        return jsonify(api_response.json()), 200
    return jsonify({'error': 'Failed to submit form data'}), api_response.status_code


@app.route('/api/<metadata>', methods=['GET'])
def get_metadata(metadata):
    """
    API endpoint that returns JSON file-level, measure-level,
    or subject-level metadata. The metadata is loaded from a file
    on the server.
    """
    if metadata not in ['files', 'measures', 'subjects']:
        abort(404, description=f"No known endpoint: {metadata}")

    return jsonify(load_metadata(metadata)), 200


if __name__ == '__main__':
    app.run(debug=True)
