from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(150), nullable=False)
    role          = db.Column(db.Enum('admin', 'inventory_staff'), nullable=False, default='inventory_staff')
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class Item(db.Model):
    __tablename__ = 'items'
    id           = db.Column(db.Integer, primary_key=True)
    item_code    = db.Column(db.String(50), nullable=False, unique=True)
    category     = db.Column(db.String(100), nullable=False)
    subcategory  = db.Column(db.String(100), nullable=False)
    name         = db.Column(db.String(200), nullable=False)
    unit_measure = db.Column(db.String(50), default='unit')
    unit_value   = db.Column(db.Numeric(15, 2), default=0)
    system_qty   = db.Column(db.Integer, nullable=False, default=0)
    is_deleted   = db.Column(db.Boolean, default=False)
    created_by   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class History(db.Model):
    __tablename__ = 'history'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action    = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user      = db.relationship('User', foreign_keys=[user_id])
