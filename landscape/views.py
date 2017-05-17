from landscape import app, db
from landscape.models import User

from flask import request, render_template, redirect, url_for, flash, send_from_directory
from flask_login import login_user,login_required, current_user
from sqlalchemy.sql import or_


if app.config.get('SERVE_STATIC', False) is True:
    @app.route('/static/<path:filename>')
    def static_file(filename):
        return send_from_directory(app.config['STATIC_FOLDER'], filename, as_attachment=True)


@app.route('/', methods=['GET'])
def index():
    return 'Hello World!'


@app.route('/user/widgets', methods=['GET'])
@login_required
def widgets():
    return render_template('widgets.html', user=current_user)


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
