"""Sheriff API endpoints for Deputy Sheriffs' Association portal."""
import jwt
from flask import Blueprint, request, jsonify, current_app, Response, g
from flask_restful import Api, Resource
from datetime import datetime, timedelta
from flask_cors import cross_origin
from __init__ import app, db
from api.authorize import token_required
from model.sheriff import Sheriff
import os

sheriff_api = Blueprint('sheriff_api', __name__, url_prefix='/api')
api = Api(sheriff_api)


def decode_sheriff_token():
    """Decode JWT token from sheriff cookie."""
    token = request.cookies.get(app.config['JWT_TOKEN_NAME'])
    if not token:
        raise AuthError({'message': 'No token provided'}, 401)
    
    try:
        decoded = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=["HS256"]
        )
        uid = decoded.get('uid') or decoded.get('_uid')
        if not uid:
            raise AuthError({'message': 'Token missing uid'}, 401)
        return Sheriff.query.filter_by(_uid=uid).first()
    except jwt.ExpiredSignatureError:
        raise AuthError({'message': 'Token expired'}, 401)
    except jwt.InvalidTokenError:
        raise AuthError({'message': 'Invalid token'}, 401)
    except Exception as e:
        raise AuthError({'message': 'Token decode error'}, 401)


def set_sheriff_cookie(response, token, max_age):
    """Set jwt_sheriff cookie with production or dev settings."""
    is_production = os.environ.get('IS_PRODUCTION', 'false').lower() == 'true'
    cookie_name = app.config['JWT_TOKEN_NAME']
    if is_production:
        response.set_cookie(cookie_name, token, max_age=max_age,
                            secure=True, httponly=True, path='/',
                            samesite='None', domain='.opencodingsociety.com')
    else:
        response.set_cookie(cookie_name, token, max_age=max_age,
                            secure=False, httponly=False, path='/',
                            samesite='Lax')
    return response


def validate_signup_data(body):
    """Validate name, uid, sheriff_id, password from request body.

    Returns a validated dict or raises an error tuple.
    """
    if not body:
        raise AuthError({'message': 'No request body provided'}, 400)
    
    required_fields = ['name', 'uid', 'sheriff_id', 'password']
    for field in required_fields:
        if not body.get(field):
            raise AuthError({'message': f'{field} is required'}, 400)
    
    # Basic validation
    if len(body['uid']) < 3:
        raise AuthError({'message': 'Username must be at least 3 characters'}, 400)
    
    if len(body['password']) < 6:
        raise AuthError({'message': 'Password must be at least 6 characters'}, 400)
    
    return body


class AuthError(Exception):
    """Simple exception to carry an error response tuple out of helpers."""
    def __init__(self, body, status_code):
        self.body = body
        self.status_code = status_code


class SheriffAPI:

    class _Authenticate(Resource):
        """Sheriff login endpoint."""
        @cross_origin(supports_credentials=True, origins=['https://dsasd.opencodingsociety.com', 'https://sheriff.opencodingsociety.com'])
        def post(self):
            try:
                body = request.get_json()
                if not body:
                    return {'message': 'Please provide credentials'}, 400

                uid = body.get('uid')
                if not uid:
                    return {'message': 'Username is missing'}, 401
                password = body.get('password')
                if not password:
                    return {'message': 'Password is missing'}, 401

                # Query sheriff from database
                sheriff = Sheriff.query.filter_by(_uid=uid).first()
                if not sheriff:
                    return {'message': 'Invalid credentials'}, 401

                # Verify password
                if sheriff.check_password(password):
                    # Generate JWT token
                    token = jwt.encode({
                        'uid': sheriff.uid,
                        'exp': datetime.utcnow() + timedelta(hours=12)
                    }, app.config['SECRET_KEY'], algorithm="HS256")

                    response_data = {
                        "message": "Login successful",
                        "user": {
                            "id": sheriff.id,
                            "uid": sheriff.uid,
                            "name": sheriff.name,
                            "email": sheriff.email,
                            "sheriff_id": sheriff.sheriff_id,
                            "rank": sheriff.rank,
                            "station": sheriff.station,
                            "phone": sheriff.phone,
                            "role": sheriff.role,
                            "status": sheriff.status,
                        }
                    }
                    resp = jsonify(response_data)
                    set_sheriff_cookie(resp, token, 43200)
                    return resp
                else:
                    return {'message': 'Invalid credentials'}, 401

            except Exception as e:
                return {'message': 'Something went wrong', 'error': str(e)}, 500

        @cross_origin(supports_credentials=True, origins=['https://dsasd.opencodingsociety.com', 'https://sheriff.opencodingsociety.com'])
        def delete(self):
            """Logout - expire the sheriff cookie."""
            try:
                resp = Response("Sheriff token invalidated")
                set_sheriff_cookie(resp, '', 0)
                return resp
            except Exception as e:
                return {'message': 'Failed to invalidate token', 'error': str(e)}, 500

    class _ID(Resource):
        """Get current sheriff from token."""
        @cross_origin(supports_credentials=True, origins=['https://dsasd.opencodingsociety.com', 'https://sheriff.opencodingsociety.com'])
        def get(self):
            try:
                sheriff = decode_sheriff_token()
                return jsonify(sheriff.read())
            except AuthError as e:
                return e.body, e.status_code

    class _CRUD(Resource):
        """Sheriff user CRUD operations."""

        @cross_origin(supports_credentials=True, origins=['https://dsasd.opencodingsociety.com', 'https://sheriff.opencodingsociety.com'])
        def post(self):
            """Create a new sheriff user (signup)."""
            try:
                body = request.get_json()
                validated = validate_signup_data(body)
            except AuthError as e:
                return e.body, e.status_code

            from datetime import date as _date
            sheriff = Sheriff(
                name=validated['name'],
                uid=validated['uid'],
                sheriff_id=validated['sheriff_id'],
                email=validated['email'],
                password=validated['password'],
                rank=validated.get('rank', 'Deputy'),
                station=validated.get('station', 'San Diego County'),
                phone=validated.get('phone', ''),
                role=validated.get('role', 'Member'),
                status=validated.get('status', 'Active'),
                created_date=_date.today()
            )

            try:
                created = sheriff.create()
                if not created:
                    return {'message': f'Sheriff ID or username already exists'}, 400
                return jsonify(created.read())
            except Exception as e:
                return {'message': f'Error creating sheriff: {str(e)}'}, 500

        @cross_origin(supports_credentials=True, origins=['https://dsasd.opencodingsociety.com', 'https://sheriff.opencodingsociety.com'])
        def get(self):
            """Get all sheriff users (admin only)."""
            try:
                require_admin()
                sheriffs = Sheriff.query.all()
                return jsonify([s.read() for s in sheriffs])
            except AuthError as e:
                return e.body, e.status_code

        @cross_origin(supports_credentials=True, origins=['https://dsasd.opencodingsociety.com', 'https://sheriff.opencodingsociety.com'])
        def put(self):
            """Update sheriff user."""
            try:
                current_sheriff = decode_sheriff_token()
            except AuthError as e:
                return e.body, e.status_code

            body = request.get_json()
            # Admin can update anyone, members can only update themselves
            if current_sheriff.is_admin() and body.get('uid'):
                target = Sheriff.query.filter_by(_uid=body['uid']).first()
                if not target:
                    return {'message': 'Target sheriff not found'}, 404
            else:
                target = current_sheriff

            target.update(body)
            return jsonify(target.read())

        @cross_origin(supports_credentials=True, origins=['https://dsasd.opencodingsociety.com', 'https://sheriff.opencodingsociety.com'])
        def delete(self):
            """Delete sheriff user (admin only)."""
            try:
                current_sheriff = decode_sheriff_token()
                if not current_sheriff or not current_sheriff.is_admin():
                    return {'message': 'Admin access required'}, 403
            except AuthError as e:
                return e.body, e.status_code

            body = request.get_json()
            if not body.get('uid'):
                return {'message': 'User ID required for deletion'}, 400

            target = Sheriff.query.filter_by(_uid=body['uid']).first()
            if not target:
                return {'message': 'Sheriff not found'}, 404

            try:
                target.delete()
                return {'message': 'Sheriff deleted successfully'}
            except Exception as e:
                return {'message': f'Error deleting sheriff: {str(e)}'}, 500


# Register API endpoints
api.add_resource(SheriffAPI._Authenticate, '/sheriff/authenticate')
api.add_resource(SheriffAPI._ID, '/sheriff/id')
api.add_resource(SheriffAPI._CRUD, '/sheriff/user')
