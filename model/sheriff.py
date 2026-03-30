"""Sheriff User model for the Deputy Sheriffs' Association of San Diego County.

Database tables:
  - sheriff_users: Core user/authentication data
  - sheriff_training: Training and academy records
  - sheriff_certifications: Professional certifications
  - sheriff_commendations: Awards and commendations
  - sheriff_emergency_contacts: Emergency contact information
  - sheriff_assignments: Assignment and transfer history
"""
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json

from __init__ import app, db


# ── Core User Table ─────────────────────────────────────────────────────────

class Sheriff(db.Model):
    """Core sheriff user — authentication and profile data."""
    __tablename__ = 'sheriff_users'

    id = db.Column(db.Integer, primary_key=True)
    _name = db.Column(db.String(255), nullable=False)
    _uid = db.Column(db.String(255), unique=True, nullable=False)
    _sheriff_id = db.Column(db.String(50), unique=True, nullable=False)
    _email = db.Column(db.String(255), nullable=False)
    _password = db.Column(db.String(255), nullable=False)
    _rank = db.Column(db.String(100), default="Deputy", nullable=False)
    _station = db.Column(db.String(255), default="San Diego Central", nullable=False)
    _phone = db.Column(db.String(20), nullable=True)
    _role = db.Column(db.String(20), default="Member", nullable=False)
    _status = db.Column(db.String(20), default="Active", nullable=False)
    _years_of_service = db.Column(db.Integer, default=0)
    _date_of_hire = db.Column(db.Date, nullable=True)
    _date_of_birth = db.Column(db.Date, nullable=True)
    _specialization = db.Column(db.String(255), nullable=True)  # e.g. K-9, SWAT, Detective
    _bio = db.Column(db.Text, nullable=True)

    # Relationships
    training_records = db.relationship('SheriffTraining', backref='sheriff', lazy=True, cascade='all, delete-orphan')
    certifications = db.relationship('SheriffCertification', backref='sheriff', lazy=True, cascade='all, delete-orphan')
    commendations = db.relationship('SheriffCommendation', backref='sheriff', lazy=True, cascade='all, delete-orphan')
    emergency_contacts = db.relationship('SheriffEmergencyContact', backref='sheriff', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('SheriffAssignment', backref='sheriff', lazy=True, cascade='all, delete-orphan')

    def __init__(self, name, uid, sheriff_id, password="sheriff123", email="",
                 rank="Deputy", station="San Diego Central", phone="",
                 role="Member", status="Active", years_of_service=0,
                 date_of_hire=None, date_of_birth=None, specialization="",
                 bio=""):
        self._name = name
        self._uid = uid
        self._sheriff_id = sheriff_id
        self._email = email
        self.set_password(password)
        self._rank = rank
        self._station = station
        self._phone = phone
        self._role = role
        self._status = status
        self._years_of_service = years_of_service
        self._date_of_hire = date_of_hire
        self._date_of_birth = date_of_birth
        self._specialization = specialization
        self._bio = bio

    # --- Properties ---
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, uid):
        self._uid = uid

    @property
    def sheriff_id(self):
        return self._sheriff_id

    @sheriff_id.setter
    def sheriff_id(self, sheriff_id):
        self._sheriff_id = sheriff_id

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        self._email = email

    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, rank):
        self._rank = rank

    @property
    def station(self):
        return self._station

    @station.setter
    def station(self, station):
        self._station = station

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, phone):
        self._phone = phone

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        self._role = role

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    @property
    def password(self):
        return self._password[0:10] + "..."

    def set_password(self, password):
        if password and password.startswith("pbkdf2:sha256:"):
            self._password = password
        else:
            self._password = generate_password_hash(password, "pbkdf2:sha256", salt_length=10)

    def is_password(self, password):
        return check_password_hash(self._password, password)

    def is_admin(self):
        return self._role == "Admin"

    def __str__(self):
        return json.dumps(self.read())

    # --- CRUD ---
    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        return {
            "id": self.id,
            "name": self.name,
            "uid": self.uid,
            "sheriff_id": self.sheriff_id,
            "email": self.email,
            "rank": self.rank,
            "station": self.station,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
            "years_of_service": self._years_of_service,
            "date_of_hire": self._date_of_hire.isoformat() if self._date_of_hire else None,
            "date_of_birth": self._date_of_birth.isoformat() if self._date_of_birth else None,
            "specialization": self._specialization,
            "bio": self._bio,
            "training": [t.read() for t in self.training_records],
            "certifications": [c.read() for c in self.certifications],
            "commendations": [a.read() for a in self.commendations],
            "emergency_contacts": [e.read() for e in self.emergency_contacts],
            "assignments": [a.read() for a in self.assignments],
        }

    def update(self, inputs):
        if not isinstance(inputs, dict):
            return self
        if inputs.get("name"):
            self.name = inputs["name"]
        if inputs.get("email"):
            self.email = inputs["email"]
        if inputs.get("sheriff_id"):
            self.sheriff_id = inputs["sheriff_id"]
        if inputs.get("rank"):
            self.rank = inputs["rank"]
        if inputs.get("station"):
            self.station = inputs["station"]
        if inputs.get("phone"):
            self.phone = inputs["phone"]
        if inputs.get("role"):
            self.role = inputs["role"]
        if inputs.get("status"):
            self.status = inputs["status"]
        if inputs.get("password"):
            self.set_password(inputs["password"])
        if "years_of_service" in inputs:
            self._years_of_service = inputs["years_of_service"]
        if inputs.get("date_of_hire"):
            self._date_of_hire = date.fromisoformat(inputs["date_of_hire"])
        if inputs.get("date_of_birth"):
            self._date_of_birth = date.fromisoformat(inputs["date_of_birth"])
        if "specialization" in inputs:
            self._specialization = inputs["specialization"]
        if "bio" in inputs:
            self._bio = inputs["bio"]
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


# ── Training Records Table ──────────────────────────────────────────────────

class SheriffTraining(db.Model):
    """Academy and in-service training records."""
    __tablename__ = 'sheriff_training'

    id = db.Column(db.Integer, primary_key=True)
    sheriff_user_id = db.Column(db.Integer, db.ForeignKey('sheriff_users.id'), nullable=False)
    _course_name = db.Column(db.String(255), nullable=False)
    _institution = db.Column(db.String(255), nullable=True)
    _hours = db.Column(db.Integer, default=0)
    _completion_date = db.Column(db.Date, nullable=True)
    _score = db.Column(db.String(20), nullable=True)  # e.g. "Pass", "95%"
    _category = db.Column(db.String(100), nullable=True)  # e.g. Firearms, Defensive Tactics, Legal

    def __init__(self, sheriff_user_id, course_name, institution="", hours=0,
                 completion_date=None, score="", category=""):
        self.sheriff_user_id = sheriff_user_id
        self._course_name = course_name
        self._institution = institution
        self._hours = hours
        self._completion_date = completion_date
        self._score = score
        self._category = category

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        return {
            "id": self.id,
            "sheriff_user_id": self.sheriff_user_id,
            "course_name": self._course_name,
            "institution": self._institution,
            "hours": self._hours,
            "completion_date": self._completion_date.isoformat() if self._completion_date else None,
            "score": self._score,
            "category": self._category,
        }

    def update(self, inputs):
        if not isinstance(inputs, dict):
            return self
        for key in ["course_name", "institution", "hours", "score", "category"]:
            if key in inputs:
                setattr(self, f"_{key}", inputs[key])
        if inputs.get("completion_date"):
            self._completion_date = date.fromisoformat(inputs["completion_date"])
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


# ── Certifications Table ────────────────────────────────────────────────────

class SheriffCertification(db.Model):
    """Professional certifications (POST, first aid, etc.)."""
    __tablename__ = 'sheriff_certifications'

    id = db.Column(db.Integer, primary_key=True)
    sheriff_user_id = db.Column(db.Integer, db.ForeignKey('sheriff_users.id'), nullable=False)
    _cert_name = db.Column(db.String(255), nullable=False)
    _issuing_body = db.Column(db.String(255), nullable=True)
    _issue_date = db.Column(db.Date, nullable=True)
    _expiry_date = db.Column(db.Date, nullable=True)
    _cert_number = db.Column(db.String(100), nullable=True)
    _status = db.Column(db.String(20), default="Active")  # Active, Expired, Renewed

    def __init__(self, sheriff_user_id, cert_name, issuing_body="",
                 issue_date=None, expiry_date=None, cert_number="", status="Active"):
        self.sheriff_user_id = sheriff_user_id
        self._cert_name = cert_name
        self._issuing_body = issuing_body
        self._issue_date = issue_date
        self._expiry_date = expiry_date
        self._cert_number = cert_number
        self._status = status

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        return {
            "id": self.id,
            "sheriff_user_id": self.sheriff_user_id,
            "cert_name": self._cert_name,
            "issuing_body": self._issuing_body,
            "issue_date": self._issue_date.isoformat() if self._issue_date else None,
            "expiry_date": self._expiry_date.isoformat() if self._expiry_date else None,
            "cert_number": self._cert_number,
            "status": self._status,
        }

    def update(self, inputs):
        if not isinstance(inputs, dict):
            return self
        for key in ["cert_name", "issuing_body", "cert_number", "status"]:
            if key in inputs:
                setattr(self, f"_{key}", inputs[key])
        if inputs.get("issue_date"):
            self._issue_date = date.fromisoformat(inputs["issue_date"])
        if inputs.get("expiry_date"):
            self._expiry_date = date.fromisoformat(inputs["expiry_date"])
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


# ── Commendations / Awards Table ────────────────────────────────────────────

class SheriffCommendation(db.Model):
    """Awards, commendations, and disciplinary notes."""
    __tablename__ = 'sheriff_commendations'

    id = db.Column(db.Integer, primary_key=True)
    sheriff_user_id = db.Column(db.Integer, db.ForeignKey('sheriff_users.id'), nullable=False)
    _title = db.Column(db.String(255), nullable=False)
    _description = db.Column(db.Text, nullable=True)
    _date_awarded = db.Column(db.Date, nullable=True)
    _awarded_by = db.Column(db.String(255), nullable=True)
    _type = db.Column(db.String(50), default="Commendation")  # Commendation, Medal, Unit Citation

    def __init__(self, sheriff_user_id, title, description="",
                 date_awarded=None, awarded_by="", award_type="Commendation"):
        self.sheriff_user_id = sheriff_user_id
        self._title = title
        self._description = description
        self._date_awarded = date_awarded
        self._awarded_by = awarded_by
        self._type = award_type

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        return {
            "id": self.id,
            "sheriff_user_id": self.sheriff_user_id,
            "title": self._title,
            "description": self._description,
            "date_awarded": self._date_awarded.isoformat() if self._date_awarded else None,
            "awarded_by": self._awarded_by,
            "type": self._type,
        }

    def update(self, inputs):
        if not isinstance(inputs, dict):
            return self
        for key in ["title", "description", "awarded_by", "type"]:
            if key in inputs:
                setattr(self, f"_{key}", inputs[key])
        if inputs.get("date_awarded"):
            self._date_awarded = date.fromisoformat(inputs["date_awarded"])
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


# ── Emergency Contacts Table ────────────────────────────────────────────────

class SheriffEmergencyContact(db.Model):
    """Emergency contact information for each sheriff user."""
    __tablename__ = 'sheriff_emergency_contacts'

    id = db.Column(db.Integer, primary_key=True)
    sheriff_user_id = db.Column(db.Integer, db.ForeignKey('sheriff_users.id'), nullable=False)
    _contact_name = db.Column(db.String(255), nullable=False)
    _relationship = db.Column(db.String(100), nullable=True)
    _phone = db.Column(db.String(20), nullable=False)
    _email = db.Column(db.String(255), nullable=True)
    _is_primary = db.Column(db.Boolean, default=False)

    def __init__(self, sheriff_user_id, contact_name, phone,
                 relationship="", email="", is_primary=False):
        self.sheriff_user_id = sheriff_user_id
        self._contact_name = contact_name
        self._relationship = relationship
        self._phone = phone
        self._email = email
        self._is_primary = is_primary

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        return {
            "id": self.id,
            "sheriff_user_id": self.sheriff_user_id,
            "contact_name": self._contact_name,
            "relationship": self._relationship,
            "phone": self._phone,
            "email": self._email,
            "is_primary": self._is_primary,
        }

    def update(self, inputs):
        if not isinstance(inputs, dict):
            return self
        for key in ["contact_name", "relationship", "phone", "email"]:
            if key in inputs:
                setattr(self, f"_{key}", inputs[key])
        if "is_primary" in inputs:
            self._is_primary = inputs["is_primary"]
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


# ── Assignment History Table ────────────────────────────────────────────────

class SheriffAssignment(db.Model):
    """Station assignment and transfer history."""
    __tablename__ = 'sheriff_assignments'

    id = db.Column(db.Integer, primary_key=True)
    sheriff_user_id = db.Column(db.Integer, db.ForeignKey('sheriff_users.id'), nullable=False)
    _station = db.Column(db.String(255), nullable=False)
    _unit = db.Column(db.String(255), nullable=True)  # e.g. Patrol, Investigations, Court Services
    _rank_at_time = db.Column(db.String(100), nullable=True)
    _start_date = db.Column(db.Date, nullable=True)
    _end_date = db.Column(db.Date, nullable=True)  # NULL means current assignment
    _notes = db.Column(db.Text, nullable=True)

    def __init__(self, sheriff_user_id, station, unit="", rank_at_time="",
                 start_date=None, end_date=None, notes=""):
        self.sheriff_user_id = sheriff_user_id
        self._station = station
        self._unit = unit
        self._rank_at_time = rank_at_time
        self._start_date = start_date
        self._end_date = end_date
        self._notes = notes

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        return {
            "id": self.id,
            "sheriff_user_id": self.sheriff_user_id,
            "station": self._station,
            "unit": self._unit,
            "rank_at_time": self._rank_at_time,
            "start_date": self._start_date.isoformat() if self._start_date else None,
            "end_date": self._end_date.isoformat() if self._end_date else None,
            "notes": self._notes,
        }

    def update(self, inputs):
        if not isinstance(inputs, dict):
            return self
        for key in ["station", "unit", "rank_at_time", "notes"]:
            if key in inputs:
                setattr(self, f"_{key}", inputs[key])
        if inputs.get("start_date"):
            self._start_date = date.fromisoformat(inputs["start_date"])
        if inputs.get("end_date"):
            self._end_date = date.fromisoformat(inputs["end_date"])
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


# ── Seed Data ───────────────────────────────────────────────────────────────

def initSheriffs():
    """Create default sheriff users with related records for testing."""
    with app.app_context():
        db.create_all()

        sheriffs = [
            Sheriff(
                name="DSA Admin",
                uid="dsa_admin",
                sheriff_id="SD-0001",
                password="SheriffAdmin123!",
                email="admin@dsasd.org",
                rank="Captain",
                station="DSA Headquarters - Poway",
                phone="(858) 486-9009",
                role="Admin",
                status="Active",
                years_of_service=22,
                date_of_hire=date(2004, 3, 15),
                date_of_birth=date(1975, 8, 20),
                specialization="Administration",
                bio="Veteran captain overseeing DSA operations and member services."
            ),
            Sheriff(
                name="Maria Rodriguez",
                uid="mrodriguez",
                sheriff_id="SD-2847",
                password="Deputy2847!",
                email="mrodriguez@sdsheriff.org",
                rank="Sergeant",
                station="Vista Station",
                phone="(760) 940-4551",
                role="Member",
                status="Active",
                years_of_service=14,
                date_of_hire=date(2012, 6, 1),
                date_of_birth=date(1985, 11, 3),
                specialization="Investigations",
                bio="Experienced investigator specializing in fraud and financial crimes."
            ),
            Sheriff(
                name="James Thompson",
                uid="jthompson",
                sheriff_id="SD-3192",
                password="Deputy3192!",
                email="jthompson@sdsheriff.org",
                rank="Deputy",
                station="Rancho San Diego Station",
                phone="(619) 660-7090",
                role="Member",
                status="Active",
                years_of_service=5,
                date_of_hire=date(2021, 1, 10),
                date_of_birth=date(1993, 4, 17),
                specialization="Patrol",
                bio="Patrol deputy with a focus on community engagement and outreach."
            ),
            Sheriff(
                name="David Chen",
                uid="dchen",
                sheriff_id="SD-1584",
                password="Deputy1584!",
                email="dchen@sdsheriff.org",
                rank="Lieutenant",
                station="San Marcos Station",
                phone="(760) 510-5200",
                role="Member",
                status="Active",
                years_of_service=18,
                date_of_hire=date(2008, 9, 22),
                date_of_birth=date(1980, 1, 30),
                specialization="K-9 Unit",
                bio="K-9 handler and unit supervisor with multiple commendations."
            ),
        ]

        created_sheriffs = []
        for sheriff in sheriffs:
            try:
                created = sheriff.create()
                if created:
                    created_sheriffs.append(created)
            except IntegrityError:
                db.session.remove()
                print(f"Sheriff record exists or error: {sheriff.uid}")

        # Seed related records for each created sheriff
        _seed_training(created_sheriffs)
        _seed_certifications(created_sheriffs)
        _seed_commendations(created_sheriffs)
        _seed_emergency_contacts(created_sheriffs)
        _seed_assignments(created_sheriffs)


def _seed_training(sheriffs):
    """Seed training records."""
    if not sheriffs:
        return
    records = [
        # Admin
        (0, "Sheriff's Academy Basic Training", "San Diego Regional Academy", 960, date(2004, 9, 15), "Pass", "Academy"),
        (0, "Executive Leadership Program", "POST", 80, date(2018, 5, 20), "Pass", "Leadership"),
        # Rodriguez
        (1, "Sheriff's Academy Basic Training", "San Diego Regional Academy", 960, date(2012, 12, 1), "Pass", "Academy"),
        (1, "Advanced Interview and Interrogation", "Reid Institute", 40, date(2016, 3, 10), "Pass", "Investigations"),
        (1, "Financial Crimes Investigation", "NW3C", 24, date(2019, 8, 15), "Pass", "Investigations"),
        # Thompson
        (2, "Sheriff's Academy Basic Training", "San Diego Regional Academy", 960, date(2021, 7, 10), "Pass", "Academy"),
        (2, "Crisis Intervention Training", "POST", 40, date(2022, 4, 5), "Pass", "Crisis Response"),
        # Chen
        (3, "Sheriff's Academy Basic Training", "San Diego Regional Academy", 960, date(2009, 3, 22), "Pass", "Academy"),
        (3, "K-9 Handler Certification Course", "National Police Canine Association", 200, date(2014, 6, 1), "Pass", "K-9"),
        (3, "Supervisor Development Course", "POST", 80, date(2020, 11, 15), "Pass", "Leadership"),
    ]
    for idx, course, institution, hours, comp_date, score, category in records:
        if idx < len(sheriffs):
            SheriffTraining(
                sheriff_user_id=sheriffs[idx].id,
                course_name=course, institution=institution,
                hours=hours, completion_date=comp_date,
                score=score, category=category
            ).create()


def _seed_certifications(sheriffs):
    """Seed certification records."""
    if not sheriffs:
        return
    records = [
        (0, "POST Management Certificate", "California POST", date(2016, 1, 15), date(2028, 1, 15), "POST-MC-44821"),
        (0, "CPR/First Aid Instructor", "American Red Cross", date(2024, 6, 1), date(2026, 6, 1), "ARC-INS-9912"),
        (1, "POST Intermediate Certificate", "California POST", date(2017, 4, 20), date(2029, 4, 20), "POST-IC-55102"),
        (1, "Certified Fraud Examiner", "ACFE", date(2020, 9, 1), date(2027, 9, 1), "CFE-202055"),
        (2, "POST Basic Certificate", "California POST", date(2021, 8, 1), date(2027, 8, 1), "POST-BC-71234"),
        (2, "CPR/AED Certification", "American Red Cross", date(2025, 1, 10), date(2027, 1, 10), "ARC-CPR-33421"),
        (3, "POST Supervisory Certificate", "California POST", date(2019, 5, 10), date(2029, 5, 10), "POST-SC-48830"),
        (3, "K-9 Handler Certification", "National Police Canine Association", date(2023, 6, 1), date(2026, 6, 1), "NPCA-K9-1102"),
    ]
    for idx, cert, issuer, issue, expiry, number in records:
        if idx < len(sheriffs):
            SheriffCertification(
                sheriff_user_id=sheriffs[idx].id,
                cert_name=cert, issuing_body=issuer,
                issue_date=issue, expiry_date=expiry,
                cert_number=number
            ).create()


def _seed_commendations(sheriffs):
    """Seed commendation records."""
    if not sheriffs:
        return
    records = [
        (0, "Distinguished Service Medal", "Awarded for outstanding leadership during wildfire evacuations.", date(2020, 11, 1), "Sheriff Bill Gore", "Medal"),
        (1, "Meritorious Unit Citation", "Part of task force dismantling county-wide identity theft ring.", date(2021, 3, 15), "Chief of Investigations", "Unit Citation"),
        (2, "Community Service Award", "Recognized for founding youth mentorship program in Spring Valley.", date(2023, 9, 10), "Captain James Ward", "Commendation"),
        (3, "Medal of Valor", "K-9 team located missing child in remote terrain during night search.", date(2022, 7, 4), "Sheriff Kelly Martinez", "Medal"),
        (3, "Lifesaving Award", "Administered emergency first aid to vehicle accident victim.", date(2019, 2, 18), "Lieutenant Sara Kim", "Commendation"),
    ]
    for idx, title, desc, award_date, awarded_by, award_type in records:
        if idx < len(sheriffs):
            SheriffCommendation(
                sheriff_user_id=sheriffs[idx].id,
                title=title, description=desc,
                date_awarded=award_date, awarded_by=awarded_by,
                award_type=award_type
            ).create()


def _seed_emergency_contacts(sheriffs):
    """Seed emergency contact records."""
    if not sheriffs:
        return
    records = [
        (0, "Linda Admin-Spouse", "Spouse", "(858) 555-0101", "linda@email.com", True),
        (1, "Carlos Rodriguez", "Spouse", "(760) 555-0202", "carlos.r@email.com", True),
        (1, "Elena Rodriguez", "Mother", "(760) 555-0203", "", False),
        (2, "Sarah Thompson", "Spouse", "(619) 555-0301", "sarah.t@email.com", True),
        (3, "Amy Chen", "Spouse", "(760) 555-0401", "amy.chen@email.com", True),
        (3, "Robert Chen", "Father", "(760) 555-0402", "", False),
    ]
    for idx, name, rel, phone, email, primary in records:
        if idx < len(sheriffs):
            SheriffEmergencyContact(
                sheriff_user_id=sheriffs[idx].id,
                contact_name=name, relationship=rel,
                phone=phone, email=email, is_primary=primary
            ).create()


def _seed_assignments(sheriffs):
    """Seed assignment history records."""
    if not sheriffs:
        return
    records = [
        (0, "San Diego Central Station", "Patrol", "Deputy", date(2004, 9, 20), date(2010, 3, 1), "Initial assignment after academy."),
        (0, "Court Services", "Courtroom Security", "Sergeant", date(2010, 3, 2), date(2016, 8, 1), "Promoted to Sergeant, transferred to Courts."),
        (0, "DSA Headquarters - Poway", "Administration", "Captain", date(2016, 8, 2), None, "Current assignment — DSA operations."),
        (1, "Encinitas Station", "Patrol", "Deputy", date(2013, 1, 5), date(2017, 6, 1), ""),
        (1, "Vista Station", "Investigations", "Sergeant", date(2017, 6, 2), None, "Promoted; specializing in fraud."),
        (2, "Rancho San Diego Station", "Patrol", "Deputy", date(2021, 7, 15), None, "First assignment."),
        (3, "Santee Station", "Patrol", "Deputy", date(2009, 4, 1), date(2014, 5, 1), ""),
        (3, "San Marcos Station", "K-9 Unit", "Sergeant", date(2014, 5, 2), date(2020, 10, 1), "K-9 handler."),
        (3, "San Marcos Station", "K-9 Unit", "Lieutenant", date(2020, 10, 2), None, "Promoted to unit supervisor."),
    ]
    for idx, station, unit, rank, start, end, notes in records:
        if idx < len(sheriffs):
            SheriffAssignment(
                sheriff_user_id=sheriffs[idx].id,
                station=station, unit=unit, rank_at_time=rank,
                start_date=start, end_date=end, notes=notes
            ).create()
