"""Events API — public read + authenticated RSVP + admin create/delete."""
from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from __init__ import db
from api.authorize import auth_required
from model.event import Event, EventRSVP
from api.email_service import send_rsvp_confirmation
from datetime import date

event_api = Blueprint('event_api', __name__, url_prefix='/api/events')
api = Api(event_api)


class Events(Resource):
    def get(self):
        """Public: list all upcoming events sorted by date."""
        events = Event.query.order_by(Event._date.asc()).all()
        return jsonify([e.read() for e in events])

    @auth_required(roles="Admin")
    def post(self):
        """Admin only: create a new event."""
        from flask import g
        body = request.get_json() or {}
        required = ['title', 'type', 'date', 'time', 'location']
        for field in required:
            if not body.get(field):
                return {'message': f'{field} is required'}, 400

        event = Event(
            title=body['title'],
            event_type=body['type'],
            event_date=body['date'],
            time=body['time'],
            location=body['location'],
            description=body.get('description', ''),
            created_by=g.current_user.id,
        )
        result = event.create()
        if result is None:
            return {'message': 'Failed to create event'}, 500
        return result.read(), 201


class EventItem(Resource):
    def get(self, event_id):
        """Public: get a single event by id."""
        event = Event.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404
        return event.read()

    @auth_required(roles="Admin")
    def put(self, event_id):
        """Admin only: update an event."""
        event = Event.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404
        body = request.get_json() or {}
        result = event.update(body)
        if result is None:
            return {'message': 'Update failed'}, 500
        return result.read()

    @auth_required(roles="Admin")
    def delete(self, event_id):
        """Admin only: delete an event."""
        event = Event.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404
        event.delete()
        return {'message': 'Event deleted'}, 200


class EventRSVPs(Resource):
    @auth_required(roles="Admin")
    def get(self, event_id):
        """Admin only: list all RSVPs for an event."""
        event = Event.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404
        return jsonify([r.read() for r in event.rsvps])


class EventUserRSVP(Resource):
    @auth_required()
    def post(self, event_id):
        """Authenticated: submit or update RSVP for an event."""
        from flask import g
        body = request.get_json() or {}
        response = body.get('response', '').lower()
        if response not in ('yes', 'no'):
            return {'message': 'response must be "yes" or "no"'}, 400

        event = Event.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404

        existing = EventRSVP.query.filter_by(
            event_id=event_id, sheriff_id=g.current_user.id
        ).first()

        if existing:
            prev = existing._response
            existing._response = response
            db.session.commit()
            # Send confirmation if user just switched to attending
            if response == 'yes' and prev != 'yes':
                _send_confirmation(g.current_user, event)
            return {'message': 'RSVP updated', 'response': response}, 200

        rsvp = EventRSVP(event_id=event_id, sheriff_id=g.current_user.id, response=response)
        result = rsvp.create()
        if result is None:
            return {'message': 'Failed to save RSVP'}, 500

        if response == 'yes':
            _send_confirmation(g.current_user, event)

        return {'message': 'RSVP recorded', 'response': response}, 201


def _send_confirmation(user, event):
    """Fire-and-forget RSVP email; never raises."""
    try:
        email = getattr(user, '_email', None) or getattr(user, 'email', '')
        name  = getattr(user, '_name',  None) or getattr(user, 'name',  '')
        if email:
            send_rsvp_confirmation(email, name, event)
    except Exception as exc:
        print(f'[event_api] Email send error: {exc}')


api.add_resource(Events, '')
api.add_resource(EventItem, '/<int:event_id>')
api.add_resource(EventRSVPs, '/<int:event_id>/rsvps')
api.add_resource(EventUserRSVP, '/<int:event_id>/rsvp')
