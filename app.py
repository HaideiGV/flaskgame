from flask import Flask, render_template, redirect, url_for, request, session
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect, send, rooms
from gevent import monkey
from extension import get_all_combos
monkey.patch_all()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
broadcasting = False

wins_combo = [
	[1,2,3],[4,5,6],[7,8,9],
	[1,4,7],[2,5,8],[3,6,9],
	[1,5,9],[3,5,7]
]

# show game board
@app.route('/game')
def index():
    return render_template('index.html')


# login func
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] not in ['admin1', 'admin2'] or request.form['password'] not in ['admin1', 'admin2']:
            error = 'Invalid Credentials. Please try again.'
        else:
            session['username'] = request.form['username']
            session['steps'] = []
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


# use the room if the room have less than 1 users
@socketio.on('join', namespace='/test')
def on_join(data):
    name = session['username']
    session['receive_count'] = session.get('receive_count', 0) + 1
    room = data['room']
    if session['receive_count'] <= 2:
        join_room(room)
        global broadcasting
        broadcasting = True
        emit('my response', {
            'data': name+' connected. In rooms: ' + room,
        }, broadcast=broadcasting)
    else:
        emit('my response', {'data': name+' not connected. In room 2 gamers '})


# out from the room
@socketio.on('leave', namespace='/test')
def on_leave(data):
    name = session['username']
    session['receive_count'] = session.get('receive_count', 0) - 1
    room = data['room']
    leave_room(room)
    global broadcasting
    broadcasting = False
    emit('my response', {'data': name + ' has left the room.' + room}, broadcast=broadcasting)


# function for display each events on the right chat
@socketio.on('my event', namespace='/test')
def test_message(message):
    name = session['username']
    emit('my response', {'data': message['data'], 'name': name}, broadcast=broadcasting)


# function which send username into cells, which was clicked
@socketio.on('cell event', namespace='/test')
def test_message(message):
    name = session['username']
    cell_id = int(message['data'])
    existing_steps = session.get('steps', 0)
    existing_steps.append(cell_id)
    session['steps'] = existing_steps
    for i in wins_combo:
        if i in get_all_combos(existing_steps):
            emit('wins response', {'data': message['data'], 'win': name}, broadcast=broadcasting)
            break
    emit('cell response', {'data': message['data'], 'name': name}, broadcast=broadcasting)


#connect function
@socketio.on('connect', namespace='/test')
def test_connect():
    name = session['username']
    emit('my connecting', {'data': 'Connected', 'name': name}, broadcast=broadcasting)


# disconnect function
@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected!')


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0')