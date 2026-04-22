"""Google OAuth2 sign-in/sign-up flow for the DSA sheriff portal."""
import os
import json
import base64
import secrets
from datetime import datetime, timedelta

import jwt
import requests as http
from flask import Blueprint, redirect, request, current_app, make_response

from model.sheriff import Sheriff

google_auth_api = Blueprint('google_auth_api', __name__, url_prefix='/api/auth')

_GOOGLE_AUTH_URL     = 'https://accounts.google.com/o/oauth2/v2/auth'
_GOOGLE_TOKEN_URL    = 'https://oauth2.googleapis.com/token'
_GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
_SCOPE = 'openid email profile'


# ── URL helpers ───────────────────────────────────────────────────────────────

def _backend_base() -> str:
    is_prod = os.environ.get('IS_PRODUCTION', 'false').lower() == 'true'
    port    = os.environ.get('FLASK_PORT', '8325')
    return ('https://sheriff.opencodingsociety.com'
            if is_prod else f'http://localhost:{port}')


def _frontend_base() -> str:
    is_prod = os.environ.get('IS_PRODUCTION', 'false').lower() == 'true'
    if is_prod:
        return 'https://sheriff.opencodingsociety.com'
    return os.environ.get('FRONTEND_URL', 'http://localhost:4100')


def _redirect_uri() -> str:
    return _backend_base() + '/api/auth/google/callback'


# ── CSRF state helpers (signed JWT, no server-side session needed) ────────────

def _make_state(secret: str) -> str:
    return jwt.encode(
        {'n': secrets.token_urlsafe(16), 'exp': datetime.utcnow() + timedelta(minutes=10)},
        secret, algorithm='HS256'
    )


def _verify_state(state: str, secret: str) -> bool:
    try:
        jwt.decode(state, secret, algorithms=['HS256'])
        return True
    except Exception:
        return False


# ── Routes ────────────────────────────────────────────────────────────────────

@google_auth_api.route('/google')
def google_login():
    """Redirect the browser to Google's OAuth consent screen."""
    client_id = current_app.config.get('GOOGLE_CLIENT_ID', '')
    if not client_id:
        return (
            '<p style="font-family:sans-serif;padding:40px;color:#ef4444;">'
            'Google OAuth is not configured on this server.<br>'
            'Add <code>GOOGLE_CLIENT_ID</code> and <code>GOOGLE_CLIENT_SECRET</code> to your .env file.'
            '</p>',
            503,
        )

    state = _make_state(current_app.config['SECRET_KEY'])
    params = {
        'client_id':     client_id,
        'redirect_uri':  _redirect_uri(),
        'response_type': 'code',
        'scope':         _SCOPE,
        'state':         state,
        'access_type':   'online',
        'prompt':        'select_account',
    }
    url = _GOOGLE_AUTH_URL + '?' + '&'.join(f'{k}={v}' for k, v in params.items())
    return redirect(url)


@google_auth_api.route('/google/callback')
def google_callback():
    """Handle Google's OAuth2 redirect. Log in existing users or send new
    users to the frontend signup completion page with their profile pre-filled."""
    from api.sheriff import set_sheriff_cookie

    frontend = _frontend_base()

    # ── error / state check ──────────────────────────────────────────────────
    if request.args.get('error'):
        return redirect(f"{frontend}/?auth_error={request.args['error']}")

    state = request.args.get('state', '')
    if not _verify_state(state, current_app.config['SECRET_KEY']):
        return redirect(f'{frontend}/?auth_error=invalid_state')

    code = request.args.get('code', '')
    if not code:
        return redirect(f'{frontend}/?auth_error=no_code')

    # ── exchange code → access token ─────────────────────────────────────────
    try:
        tok = http.post(_GOOGLE_TOKEN_URL, data={
            'code':          code,
            'client_id':     current_app.config['GOOGLE_CLIENT_ID'],
            'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
            'redirect_uri':  _redirect_uri(),
            'grant_type':    'authorization_code',
        }, timeout=10).json()
    except Exception:
        return redirect(f'{frontend}/?auth_error=token_exchange')

    access_token = tok.get('access_token')
    if not access_token:
        return redirect(f'{frontend}/?auth_error=no_access_token')

    # ── get Google profile ────────────────────────────────────────────────────
    try:
        profile = http.get(
            _GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        ).json()
    except Exception:
        return redirect(f'{frontend}/?auth_error=userinfo_failed')

    google_email = (profile.get('email') or '').lower().strip()
    google_name  = profile.get('name') or ''

    # ── existing user? ────────────────────────────────────────────────────────
    sheriff = Sheriff.query.filter_by(_email=google_email).first()
    if sheriff:
        token = jwt.encode(
            {'uid': sheriff.uid, 'exp': datetime.utcnow() + timedelta(hours=12)},
            current_app.config['SECRET_KEY'],
            algorithm='HS256',
        )
        resp = make_response(redirect(f'{frontend}/?google_login=success'))
        set_sheriff_cookie(resp, token, 43200)
        return resp

    # ── new user — send profile to frontend for signup completion ─────────────
    encoded = base64.urlsafe_b64encode(
        json.dumps({'name': google_name, 'email': google_email}).encode()
    ).decode()
    return redirect(f'{frontend}/?new_user={encoded}')
