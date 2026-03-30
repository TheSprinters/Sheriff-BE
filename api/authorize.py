from flask import request, current_app, g
from functools import wraps
import jwt
from model.sheriff import Sheriff


def auth_required(roles=None):
    '''
    JWT authentication decorator for sheriff API endpoints.

    Checks for valid JWT token (jwt_sheriff cookie), decodes it,
    retrieves the Sheriff user, validates role if specified,
    and sets g.current_user.

    Args:
        roles: String or list of allowed roles (e.g., "Admin" or ["Admin", "Member"])
    '''
    def decorator(func_to_guard):
        @wraps(func_to_guard)
        def decorated(*args, **kwargs):
            token = request.cookies.get("jwt_sheriff")
            if not token:
                return {
                    "message": "Authentication required. No token found.",
                    "error": "Unauthorized"
                }, 401

            try:
                data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                user = Sheriff.query.filter_by(_uid=data["_uid"]).first()

                if user is None:
                    return {
                        "message": "Invalid authentication token.",
                        "error": "Unauthorized"
                    }, 401

                g.current_user = user

            except jwt.ExpiredSignatureError:
                return {"message": "Token has expired.", "error": "Unauthorized"}, 401
            except jwt.InvalidTokenError:
                return {"message": "Invalid token.", "error": "Unauthorized"}, 401
            except Exception as e:
                return {"message": "Token decode error.", "error": str(e)}, 500

            # Check role requirements
            if roles:
                required_roles = roles if isinstance(roles, list) else [roles]
                if user.role not in required_roles:
                    return {
                        "message": f"Insufficient permissions. Required: {', '.join(required_roles)}",
                        "error": "Forbidden"
                    }, 403

            if request.method == 'OPTIONS':
                return ('', 200)

            return func_to_guard(*args, **kwargs)

        return decorated

    return decorator


def token_required(roles=None):
    '''Backward compatibility alias for auth_required.'''
    return auth_required(roles)
