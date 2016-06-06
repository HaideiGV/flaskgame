from flask import Flask, render_template, redirect, url_for, request, session
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect, send
from flask import logging
from extension import login_manager, LoginManager, CsrfProtect


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@app.route('/game')
def index():
    return render_template('index.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    session['game'] = {}
    session['counter'] = 0
    error = None
    if request.method == 'POST':
        if request.form['username'] not in ['admin1', 'admin2'] or request.form['password'] not in ['admin1', 'admin2']:
            error = 'Invalid Credentials. Please try again.'
        else:
            session['username'] = request.form['username']
            if not (session['game'] != {}):
                session['game']['user1'] = {0: request.form['username']}
            else:
                session['game']['user2'] = {1: request.form['username']}
            print(session['game'])
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@socketio.on('join')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response', {'data': 'In rooms: ' + ', '.join(request.namespace.rooms), 'count': session['receive_count']})

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)



@socketio.on('my event', namespace='/test')
def test_message(message):
    cell_name = session['username']
    emit('my response', {'data': message['data'], 'cell_name': cell_name}, broadcast=True)

@socketio.on('cell event', namespace='/test')
def test_message(message):
    cell_name = session['username']
    emit('cell response', {'data': message['data'], 'cell_name': cell_name }, broadcast=True)

@socketio.on('my broadcast event', namespace='/test')
def test_message(message):
    emit('login response', {'data': message['data']})

@socketio.on('connect', namespace='/test')
def test_connect():
    cell_name = session['username']
    emit('my response', {'data': 'Connected', 'cell_name': cell_name}, broadcast=True)

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected!')




if __name__ == '__main__':
    socketio.run(app, debug=True)