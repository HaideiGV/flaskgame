from flask import Flask, render_template, redirect, url_for, request, session
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect, send, rooms
from gevent import monkey
monkey.patch_all()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

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
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


# use the room if the room have less than 1 users
@socketio.on('join', namespace='/test')
def on_join(data):
    name = session['username']
    session['receive_count'] = session.get('receive_count', 0) + 1
    room = data['room']
    print(room)
    if session['receive_count'] <= 2:
        join_room(room)
        emit('my response', {
            'data': name+' connected. In rooms: ' + ', '.join(rooms()),
        })
    else:
        emit('my response', {'data': name+' not connected. In room 2 gamers '})


# out from the room
@socketio.on('leave', namespace='/test')
def on_leave(data):
    name = session['username']
    room = data['room']
    leave_room(room)
    send(name + ' has left the room.', room=room)


# function for display each events on the right chat
@socketio.on('my event', namespace='/test')
def test_message(message):
    name = session['username']
    emit('my response', {'data': message['data'], 'name': name}, broadcast=True)


# function which send username into cells, which was clicked
@socketio.on('cell event', namespace='/test')
def test_message(message):
    name = session['username']
    emit('cell response', {'data': message['data'], 'name': name}, broadcast=True)


#connect function
@socketio.on('connect', namespace='/test')
def test_connect():
    name = session['username']
    emit('my connecting', {'data': 'Connected', 'name': name}, broadcast=True)


# disconnect function
@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected!')


if __name__ == '__main__':
    socketio.run(app, debug=True)