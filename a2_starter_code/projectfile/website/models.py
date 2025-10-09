from . import db
from datetime import datetime
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100), index=True, unique=True, nullable=False)
    emailid = db.Column(db.String(100), index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    comments = db.relationship('Comment', backref='user')

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    eventname = db.Column(db.String(80)) #
    category = db.Column(db.String(80)) #picklist
    description = db.Column(db.String(250))
    eventdate = db.Column (db.DateTime) #need to be adjusted
    startime = db.Column (db.DateTime) #need to be adjusted
    endtime = db.Column (db.DateTime) #need to be adjusted
    venue = db.Column(db.String(80))
    image = db.Column(db.String(80))
    numticket = db.Column (db.Integer)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=datetime.now())
    # add the foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))

class Order(db.Model): 
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer) #needs to be adjusted
    quantity = db.Column(db.Integer)
    date = db.Column (db.DateTime) #need to be adjusted
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
