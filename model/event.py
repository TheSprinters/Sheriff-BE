"""Event and RSVP models for DSA events calendar."""
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date
import json

from __init__ import app, db


class Event(db.Model):
    """DSA event entry."""
    __tablename__ = 'dsa_events'

    id = db.Column(db.Integer, primary_key=True)
    _title = db.Column(db.String(255), nullable=False)
    _type = db.Column(db.String(50), default='meeting', nullable=False)
    _date = db.Column(db.Date, nullable=False)
    _time = db.Column(db.String(10), nullable=False)
    _location = db.Column(db.String(255), nullable=False)
    _description = db.Column(db.Text, nullable=True)
    _created_by = db.Column(db.Integer, db.ForeignKey('sheriff_users.id'), nullable=True)
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rsvps = db.relationship('EventRSVP', backref='event', lazy=True, cascade='all, delete-orphan')

    def __init__(self, title, event_type, event_date, time, location, description='', created_by=None):
        self._title = title
        self._type = event_type
        self._date = event_date if isinstance(event_date, date) else date.fromisoformat(event_date)
        self._time = time
        self._location = location
        self._description = description
        self._created_by = created_by

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        yes_count = sum(1 for r in self.rsvps if r._response == 'yes')
        no_count = sum(1 for r in self.rsvps if r._response == 'no')
        return {
            'id': self.id,
            'title': self._title,
            'type': self._type,
            'date': self._date.isoformat(),
            'time': self._time,
            'location': self._location,
            'description': self._description or '',
            'created_by': self._created_by,
            'created_at': self._created_at.isoformat() if self._created_at else None,
            'rsvp': {
                'yes': yes_count,
                'no': no_count,
                'total': yes_count + no_count,
            }
        }

    def update(self, inputs):
        if not isinstance(inputs, dict):
            return self
        if inputs.get('title'):
            self._title = inputs['title']
        if inputs.get('type'):
            self._type = inputs['type']
        if inputs.get('date'):
            self._date = date.fromisoformat(inputs['date'])
        if inputs.get('time'):
            self._time = inputs['time']
        if inputs.get('location'):
            self._location = inputs['location']
        if 'description' in inputs:
            self._description = inputs['description']
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return None
        return self

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return None


class EventRSVP(db.Model):
    """Tracks per-user RSVP responses to events."""
    __tablename__ = 'dsa_event_rsvps'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('dsa_events.id'), nullable=False)
    sheriff_id = db.Column(db.Integer, db.ForeignKey('sheriff_users.id'), nullable=False)
    _response = db.Column(db.String(10), nullable=False)  # 'yes' or 'no'
    _responded_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('event_id', 'sheriff_id', name='uq_event_rsvp'),)

    def __init__(self, event_id, sheriff_id, response):
        self.event_id = event_id
        self.sheriff_id = sheriff_id
        self._response = response

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        from model.sheriff import Sheriff
        sheriff = Sheriff.query.get(self.sheriff_id)
        return {
            'id': self.id,
            'event_id': self.event_id,
            'sheriff_id': self.sheriff_id,
            'sheriff_name': sheriff.name if sheriff else 'Unknown',
            'sheriff_uid': sheriff.uid if sheriff else '',
            'sheriff_rank': sheriff.rank if sheriff else '',
            'response': self._response,
            'responded_at': self._responded_at.isoformat() if self._responded_at else None,
        }


def initEvents():
    """Create tables and seed sample events."""
    with app.app_context():
        db.create_all()
