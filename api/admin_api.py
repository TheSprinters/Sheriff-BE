"""Admin API — full user-management endpoints (Admin role required)."""
import jwt
from flask import Blueprint, request, jsonify, current_app
from flask_restful import Api, Resource
from __init__ import db
from api.authorize import auth_required
from model.sheriff import Sheriff

admin_api = Blueprint('admin_api', __name__, url_prefix='/api/admin')
api = Api(admin_api)


class AdminUsers(Resource):
    """List all users or create a new one."""

    @auth_required(roles="Admin")
    def get(self):
        users = Sheriff.query.order_by(Sheriff._name).all()
        return jsonify([u.read() for u in users])

    @auth_required(roles="Admin")
    def post(self):
        body = request.get_json()
        if not body:
            return {'message': 'No body provided'}, 400

        required = ['name', 'uid', 'sheriff_id', 'password']
        for field in required:
            if not body.get(field):
                return {'message': f'{field} is required'}, 400

        sheriff = Sheriff(
            name=body['name'],
            uid=body['uid'],
            sheriff_id=body['sheriff_id'],
            password=body['password'],
            email=body.get('email', ''),
            rank=body.get('rank', 'Deputy'),
            station=body.get('station', 'San Diego Central'),
            phone=body.get('phone', ''),
            role=body.get('role', 'Member'),
            status=body.get('status', 'Active'),
        )
        result = sheriff.create()
        if result is None:
            return {'message': 'Username or Sheriff ID already exists'}, 409
        return result.read(), 201


class AdminUser(Resource):
    """Update or delete a specific user by id."""

    @auth_required(roles="Admin")
    def get(self, user_id):
        sheriff = Sheriff.query.get(user_id)
        if not sheriff:
            return {'message': 'User not found'}, 404
        return sheriff.read()

    @auth_required(roles="Admin")
    def put(self, user_id):
        sheriff = Sheriff.query.get(user_id)
        if not sheriff:
            return {'message': 'User not found'}, 404

        body = request.get_json() or {}
        allowed = ['name', 'email', 'rank', 'station', 'phone', 'role',
                   'status', 'specialization', 'bio', 'years_of_service']
        updates = {k: v for k, v in body.items() if k in allowed}
        result = sheriff.update(updates)
        if result is None:
            return {'message': 'Update failed'}, 500
        return result.read()

    @auth_required(roles="Admin")
    def delete(self, user_id):
        from flask import g
        sheriff = Sheriff.query.get(user_id)
        if not sheriff:
            return {'message': 'User not found'}, 404
        if sheriff.id == g.current_user.id:
            return {'message': 'Cannot delete your own account'}, 400
        sheriff.delete()
        return {'message': f'User {sheriff.uid} deleted'}, 200


class AdminUserPassword(Resource):
    """Change a user's password."""

    @auth_required(roles="Admin")
    def put(self, user_id):
        sheriff = Sheriff.query.get(user_id)
        if not sheriff:
            return {'message': 'User not found'}, 404

        body = request.get_json() or {}
        new_password = body.get('password', '')
        if len(new_password) < 6:
            return {'message': 'Password must be at least 6 characters'}, 400

        sheriff.set_password(new_password)
        db.session.commit()
        return {'message': 'Password updated successfully'}, 200


api.add_resource(AdminUsers, '/users')
api.add_resource(AdminUser, '/users/<int:user_id>')
api.add_resource(AdminUserPassword, '/users/<int:user_id>/password')
