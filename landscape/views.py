from landscape import app, db
from landscape.models import User
from flask import request, render_template, redirect, url_for, flash
from flask_login import login_user, login_required
from sqlalchemy.sql import or_


@app.route('/', methods=['GET'])
def index():
    return 'Hello World!'


@app.route('/user/<user_id>/widgets', methods=['GET', 'CREATE'])
@login_required
def widgets(user_id):
    if request.accept_mimetypes.accept_html:
        return render_template('widgets.html')
    # todo: return the widgets configured (if GET)
    # todo: create a new widget (if CREATE)


@app.route('/user/<user_id>/widget/<widget_id>', methods=['GET', 'DELETE'])
@login_required
def widget(user_id, widget_id):
    # todo: return widget details or delete the widget
    pass


@app.route('/knock-knock', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = User.encode_password(request.form['password'])
    registered_user = User.query.filter(or_(User.username == username, User.email == username), User.password == password).first()
    if registered_user is None:
        flash('Username or Password is invalid', 'danger')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('Logged in successfully', 'success')
    return redirect(request.args.get('next') or url_for('widgets', user_id=registered_user.id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = User(username=request.form['username'], password=request.form['password'], email=request.form['email'])
    db.session.add(user)
    db.session.commit()
    flash(f'Welcome {user.username}', 'success')
    return redirect(url_for('login'))
