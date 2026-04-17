from datetime import date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    __tablename__ = 'categories'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    subcategories = db.relationship('Subcategory', backref='category', lazy=True, cascade='all, delete-orphan')
    items         = db.relationship('InventoryItem', backref='category', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class Subcategory(db.Model):
    __tablename__ = 'subcategories'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    items = db.relationship('InventoryItem', backref='subcategory', lazy=True)

    __table_args__ = (db.UniqueConstraint('name', 'category_id'),)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'category_id': self.category_id}


class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    id               = db.Column(db.Integer, primary_key=True)
    category_id      = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    subcategory_id   = db.Column(db.Integer, db.ForeignKey('subcategories.id'), nullable=False)
    name             = db.Column(db.String(255), nullable=False)
    quantity         = db.Column(db.Integer, nullable=False, default=0)

    # Detail fields (expanded view / create-new continuation)
    article          = db.Column(db.String(255))
    stock_number     = db.Column(db.String(100))
    unit_of_measure  = db.Column(db.String(100))
    unit_value       = db.Column(db.Numeric(15, 2))
    balance_per_card = db.Column(db.Integer)
    on_hand_per_count= db.Column(db.Integer)
    shortage_quantity= db.Column(db.Integer)
    overage_value    = db.Column(db.Numeric(15, 2))
    remarks          = db.Column(db.Text)

    date_created     = db.Column(db.Date, nullable=False, default=date.today)
    date_updated     = db.Column(db.Date, nullable=False, default=date.today, onupdate=date.today)

    def to_dict(self):
        return {
            'id':                self.id,
            'category_id':       self.category_id,
            'category_name':     self.category.name if self.category else '',
            'subcategory_id':    self.subcategory_id,
            'subcategory_name':  self.subcategory.name if self.subcategory else '',
            'name':              self.name,
            'quantity':          self.quantity,
            'article':           self.article,
            'stock_number':      self.stock_number,
            'unit_of_measure':   self.unit_of_measure,
            'unit_value':        float(self.unit_value) if self.unit_value else None,
            'balance_per_card':  self.balance_per_card,
            'on_hand_per_count': self.on_hand_per_count,
            'shortage_quantity': self.shortage_quantity,
            'overage_value':     float(self.overage_value) if self.overage_value else None,
            'remarks':           self.remarks,
            'date_created':      self.date_created.strftime('%m/%d/%Y') if self.date_created else '',
            'date_updated':      self.date_updated.strftime('%m/%d/%Y') if self.date_updated else '',
        }
