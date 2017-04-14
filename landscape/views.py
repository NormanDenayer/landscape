from landscape import app, db
from landscape.models import User
from flask import request, render_template, redirect, url_for, flash
from flask.ext.login import login_user, login_required


@app.route('/', methods=['GET'])
def index():
    return 'Hello World!'


@app.route('/secured', methods=['GET'])
@login_required
def secured():
    return 'This is secured'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    registered_user = User.query.filter_by(username=username, password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid', 'error')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))
