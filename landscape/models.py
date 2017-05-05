import enum
import json
import hashlib

from landscape import db
from sqlalchemy.sql import func


class WidgetType(enum.Enum):
    FEED = 1
    LINK = 2
    TODO = 3


class Widget(db.Model):
    __tablename__ = 'widgets'
    id = db.Column('widget_id', db.Integer, primary_key=True)
    type = db.Column('type', db.Enum(WidgetType), nullable=False)
    title = db.Column('title', db.String(100), nullable=False)
    uri = db.Column('uri', db.String(10000))
    content = db.Column('content', db.Text)
    refresh_freq = db.Column('refresh_freq', db.Integer, default=10)

    x = db.Column('x', db.Integer, default=0)
    y = db.Column('y', db.Integer, default=0)
    height = db.Column('height', db.Integer)
    width = db.Column('width', db.Integer)

    created_on = db.Column('created_on', db.DateTime, server_default=func.now())
    updated_on = db.Column('updated_on', db.DateTime, onupdate=func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

    def __init__(self, type, title, user_id, uri=None, refresh_freq=None, x=None, y=None, height=None, width=None):
        self.type = type
        self.uri = uri
        self.title = title
        self.refresh_freq = refresh_freq
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.user_id = user_id

    def __repr__(self):
        return f'<Widget.{self.type} {self.title} for user {self.user_id}>'

    def to_dict(self, limited=False):
        entry = {
            'id': self.id,
            'type': self.type.value,
            'x': self.x,
            'y': self.y,
            'height': self.height,
            'width': self.width,
            'uri': self.uri,
            'title': self.title,
        }
        if not limited:
            entry.update({
                'content': json.loads(self.content) if self.content else '',
                'refresh_freq': self.refresh_freq,
            })
        return entry

    @staticmethod
    def new_coordinates(user_id):
        widgets = Widget.query.filter_by(user_id=user_id).all()
        if widgets:
            w = max(widgets, key=lambda widget:widget.y + widget.height)
            next_y = w.y + w.height + 1
        else:
            next_y = 0

        return {
            'x': 0, 'y': next_y,
            'height': 3, 'width': 5,
        }


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(80), unique=True, index=True)
    email = db.Column('email', db.String(120), unique=True, index=True)
    password = db.Column('password', db.String(255))
    registered_on = db.Column('registered_on', db.DateTime, server_default=func.now())

    widgets = db.relationship('Widget', backref='user', lazy='dynamic')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = User.encode_password(password)

    def __repr__(self):
        return '<User %r>' % self.username

    @staticmethod
    def encode_password(password):
        return hashlib.sha512(password.encode()).hexdigest()

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
