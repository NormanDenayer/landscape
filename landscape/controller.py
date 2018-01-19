import hashlib
import secrets
import sqlite3
import logging
import datetime

from aiohttp import web
from functools import wraps
from types import SimpleNamespace

logger = logging.getLogger('aiohttp.access')


def login_required(f):
    @wraps(f)
    async def _inner(request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if token is None:
            return web.Response(status=401)
        parts = token.split(' ', 1)
        if len(parts) != 2 or parts[0] != 'Bearer':
            return web.Response(status=401)
        _, token = parts
        user = request.app['db'].auth_user(token=token)
        if user is None:
            return web.Response(status=401)

        r = await f(request, user, *args, **kwargs)
        return r
    return _inner


WidgetFields = ('widget_id', 'type', 'title', 'uri', 'content', 'refresh_freq', 'x', 'y', 'height', 'width', 'user_id', 'updated_on')

class BuildFromRow(SimpleNamespace):
    FIELDS = []

    @classmethod
    def from_row(cls, row):
        keys = row.keys()
        values = tuple(row)
        return cls(**dict(zip(keys, values)))

    def as_dict(self, exclude=None):
        return {
            k:v for k, v in self.__dict__.items() if k in self.FIELDS and (exclude is None or k not in exclude)
        }


class Widget(BuildFromRow):
    FIELDS = WidgetFields
    DEFAULT_HEIGHT = 3
    DEFAULT_WIDTH = 5
    DEFAULT_X = 0

    @staticmethod
    def new_coordinates(existing_widgets=None):
        if existing_widgets:  # might be empty or None
            w = max(existing_widgets, key=lambda widget: widget.y + widget.height)
            next_y = w.y + w.height + 1
        else:
            next_y = 0

        return {
            'x': Widget.DEFAULT_X, 'y': next_y,
            'height': Widget.DEFAULT_HEIGHT, 'width': Widget.DEFAULT_WIDTH,
        }


UserFields = ('user_id', 'username', 'email', 'password', 'token')

class User(BuildFromRow):
    FIELDS = UserFields
    @staticmethod
    def encode_password(password):
        return hashlib.sha512(password.encode()).hexdigest()

    @staticmethod
    def generate_token():
        return secrets.token_hex(32)


class DatabaseHandler(object):
    def __init__(self, db_co):
        self.db = db_co
        self.db.row_factory = sqlite3.Row
        try:
            self.db.execute('ALTER TABLE users ADD token VARCHAR(255) DEFAULT "ABCD1234ABCD1234" NOT NULL')
        except:
            logger.info('ok, the column user was already there...')

    @property
    def widgets(self):
        recs = self.db.execute(f"select {', '.join(WidgetFields)} from widgets").fetchall()
        return [Widget.from_row(rec) for rec in recs]

    def get_widgets(self, user_id):
        recs = self.db.execute(f"select {', '.join(WidgetFields)} from widgets where user_id=?", (user_id,)).fetchall()
        return [Widget.from_row(rec) for rec in recs]

    def get_widget(self, user_id, widget_id):
        rec = self.db.execute(f"select {', '.join(WidgetFields)} from widgets where user_id=? and widget_id=?", (user_id, widget_id)).fetchone()
        return None if rec is None else Widget.from_row(rec)

    def add_widget(self, widget):
        with self.db:
            self.db.execute('''
                insert into widgets(
                    type, title, uri, content, refresh_freq, x, y, height, width, user_id
                ) values (?,?,?,?,?,?,?,?,?,?)''',
                (widget.type,
                 widget.title,
                 widget.uri,
                 widget.content,
                 widget.refresh_freq, widget.x, widget.y, widget.height, widget.width,
                 widget.user_id)
            )

    def update_widget(self, widget):
        now = datetime.datetime.now()
        now = now.replace(microsecond=0)
        with self.db:
            self.db.execute('''
                update widgets set
                    title=?, uri=?, content=?, refresh_freq=?, x=?, y=?, height=?, width=?, updated_on=?
                where widget_id=?''',
                (widget.title,
                 widget.uri,
                 widget.content,
                 widget.refresh_freq, widget.x, widget.y, widget.height, widget.width,
                 now,
                 widget.widget_id)
            )

    def delete_widget(self, widget_id):
        with self.db:
            self.db.execute('delete from widgets where widget_id=?', (widget_id,))

    def create_user(self, username, password, email):
        with self.db:
            self.db.execute(
                'insert into users (username, password, email, token) values (?, ?, ?, ?)',
                (username, User.encode_password(password), email, User.generate_token())
            )

    def auth_user(self, token):
        cu = self.db.execute(f"select {', '.join(UserFields)} from users where token=?", (token,))
        user = cu.fetchone()
        return User.from_row(user) if user is not None else None

    def get_user(self, username, password):
        cu = self.db.execute(
            f"select {', '.join(UserFields)} from users where username=? and password=?",
            (username, User.encode_password(password))
        )
        user = cu.fetchone()
        return User.from_row(user) if user is not None else None

    def reset_user_token(self, user):
        user.token = User.generate_token()
        with self.db:
            self.db.execute('update users set token=? where user_id=?', (user.token, user.user_id))
        return user

    @classmethod
    def create_connection(cls, database):
        co = sqlite3.connect(database=database, detect_types=sqlite3.PARSE_DECLTYPES)
        return cls(co)
