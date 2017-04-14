from datetime import datetime

from landscape import db


class Feed(db.Model):
    __tablename__ = 'feeds'
    id = db.Column('feed_id', db.Integer, primary_key=True)
    uri = db.Column('uri', db.String(10000), unique=True)
    frequency = db.Column('frequency', db.Integer)
    content = db.Column('content', db.Text)
    created_on = db.Column('registered_on', db.DateTime)
    last_update = db.Column('last_update', db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))


class Link(db.Model):
    __tablename__ = 'links'
    id = db.Column('link_id', db.Integer, primary_key=True)
    uri = db.Column('uri', db.String(10000))

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(80), unique=True, index=True)
    email = db.Column('email', db.String(120), unique=True, index=True)
    password = db.Column('password', db.String(255))
    registered_on = db.Column('registered_on', db.DateTime)

    feeds = db.relationship('Feed', backref='user', lazy='dynamic')
    links = db.relationship('Link', backref='user', lazy='dynamic')

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email
        self.registered_on = datetime.utcnow()

    def __repr__(self):
        return '<User %r>' % self.username

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
