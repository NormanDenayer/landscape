from landscape import app, db
from landscape.models import User, WidgetType, Widget

from flask import request, render_template, redirect, url_for, flash, session, abort, send_from_directory
from flask_login import login_user, login_required, current_user
from flask.json import jsonify
from sqlalchemy.sql import or_


if app.config.get('DEBUG', False) is True:
    @app.route('/static/<path:filename>')
    def static_file(filename):
        return send_from_directory(app.config['STATIC_FOLDER'], filename, as_attachment=True)


@app.route('/', methods=['GET'])
def index():
    return 'Hello World!'


@app.route('/user/widgets', methods=['GET'])
@login_required
def widgets():
    return render_template('widgets.html', widget_types=[(t.value, t.name) for t in WidgetType], user=current_user)


@app.route('/user/<user_id>/widgets', methods=['GET'])
@login_required
def widgets_old(user_id):
    if str(session['user_id']) != user_id:  # ok you are logged but you are not god!
        return abort(status=403)
    return render_template('widgets_old.html', widget_types=[(t.value, t.name) for t in WidgetType], user=current_user)


@app.route('/api/v01/user/<user_id>/widgets', methods=['GET', 'CREATE', 'POST'], endpoint='api_widgets')
@login_required
def api_widgets(user_id):
    if str(session['user_id']) != user_id:  # ok you are logged but you are not god!
        return abort(status=403)
    # return the widgets configured (if GET)
    if request.method == 'GET':
        db_widgets = Widget.query.filter_by(user_id=session['user_id']).all()
        widgets = []
        for w in db_widgets:
            d = w.to_dict(limited=True)
            d['url'] = url_for('api_widget', user_id=session['user_id'], widget_id=w.id)
            widgets.append(d)
        return jsonify({'widgets': widgets})
    # update the widgets (if POST)
    if request.method == 'POST':
        db_widgets = Widget.query.filter_by(user_id=session['user_id']).all()
        db_widgets = {w.id: w for w in db_widgets}
        for widget in request.json['widgets']:
            try:
                db_widget = db_widgets[int(widget['i'])]
            except (KeyError, ValueError):
                app.logger.warning('unknown widget (possible threat): %s for %s', widget['i'], session['user_id'])
                continue
            db_widget.x = widget['x']
            db_widget.y = widget['y']
            db_widget.height = widget['h']
            db_widget.width = widget['w']
        db.session.commit()
        return jsonify({'success': True})

    # create a new widget (if CREATE)
    if request.method == 'CREATE':
        coord = Widget.new_coordinates(session['user_id'])
        if request.form['type'] == str(WidgetType.FEED.value):
            widget = Widget(type=WidgetType.FEED, user_id=session['user_id'], uri=request.form['url'],
                            title=request.form['title'], refresh_freq=request.form.get('freq', 60), **coord)
        else:
            return abort(status=422, description='Invalid type')

        db.session.add(widget)
        db.session.commit()
        return jsonify({'success': True, 'widget': widget.to_dict(limited=True)})


@app.route('/api/v01/user/<user_id>/widget/<widget_id>', methods=['GET', 'DELETE'], endpoint='api_widget')
@login_required
def api_widget(user_id, widget_id):
    if str(session['user_id']) != user_id:  # ok you are logged but you are not god!
        return abort(status=403)
    if request.method == 'GET':
        widget = Widget.query.filter_by(user_id=user_id, id=widget_id).first()
        if widget is not None:
            return jsonify({'widget': widget.to_dict()})
        return abort(status=404)

    if request.method == 'DELETE':
        widget = Widget.query.filter_by(user_id=user_id, id=widget_id).first()
        db.session.delete(widget)
        db.session.commit()
        return jsonify({'widget': widget.to_dict(limited=True)})


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
