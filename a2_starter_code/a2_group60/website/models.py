from . import db
from datetime import datetime, timezone
from flask_login import UserMixin

# User model includes username, the user's full name, their email address, home address and contact number.
# Also includes the relationship between comment and orders table.
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100), index=True, unique=True, nullable=False)
    fullname = db.Column(db.String(100))
    emailid = db.Column(db.String(100), index=True, nullable=False)
    address = db.Column(db.String(50))
    contact = db.Column(db.Integer)
    password_hash = db.Column(db.String(255), nullable=False)
    comments = db.relationship('Comment', backref='user')
    orders = db.relationship('Order', backref='user')
# Event table that will be used when creating events. 
# It features a relationship with comments, including the order in which they were made.
class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    eventname = db.Column(db.String(80)) 
    category = db.Column(db.String(80)) 
    description = db.Column(db.String(250))
    eventdate = db.Column (db.DateTime) 
    starttime = db.Column (db.DateTime)
    endtime = db.Column (db.DateTime) 
    venue = db.Column(db.String(80))
    image = db.Column(db.String(80))
    numticket = db.Column (db.Integer)    
    orders = db.relationship('Order', backref='event')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status   = db.Column(db.String(20), default='Open') 
    comments = db.relationship(
    'Comment',
    backref='event',
    lazy='dynamic',
    cascade='all, delete-orphan',
    order_by="desc(Comment.created_at)")
    
# Comments table
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
# Orders table, which include the type of ticket that the user has booked. 
class Order(db.Model): 
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    type = db.Column(db.Integer)
    date = db.Column (db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
