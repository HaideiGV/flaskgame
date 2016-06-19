from flask import Flask, render_template, redirect, url_for, request, session, Response
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, close_room, disconnect, send, rooms
from gevent import monkey
from extension import get_all_combos
import random
from flask_oauth import OAuth
from flask_cors import cross_origin
from flask.ext.cors import CORS
from flask_headers import headers

monkey.patch_all()


SECRET_KEY = 'development key'
FACEBOOK_APP_ID = '301138273559491'
FACEBOOK_APP_SECRET = '568f4f72499b113c7fc7f27c546132ba'


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
oauth = OAuth()

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)


socketio = SocketIO(app)
broadcasting = False

wins_combo = [
	[1,2,3],[4,5,6],[7,8,9],
	[1,4,7],[2,5,8],[3,6,9],
	[1,5,9],[3,5,7]
]


# #___________________________________________________
# @app.route('/')
# def login():
#     return facebook.authorize(callback=url_for('facebook_authorized',
#         next=request.args.get('next') or request.referrer or None,
#         _external=True))


# @app.route('/login/authorized')
# @facebook.authorized_handler
# def facebook_authorized(resp):
#     if resp is None:
#         return 'Access denied: reason=%s error=%s' % (
#             request.args['error_reason'],
#             request.args['error_description']
#         )
#     session['oauth_token'] = (resp['access_token'], '')
#     me = facebook.get('/me')
#     return 'Logged in as id=%s name=%s redirect=%s' % \
#         (me.data['id'], me.data['name'], request.args.get('next'))


# @facebook.tokengetter
# def get_facebook_oauth_token():
#     return session.get('oauth_token')

# #___________________________________________________


# show game board
@app.route('/game')
@headers({'Access-Control-Allow-Origin': '*', "Access-Control-Allow-Credentials": "true", 'Allow':'GET,HEAD,OPTION,POST'})
def index():
    return render_template('index.html')

@app.route('/game-with-comp')
@headers({'Access-Control-Allow-Origin': '*', "Access-Control-Allow-Credentials": "true", 'Allow':'GET,HEAD,OPTION,POST'})
def index_comp():
    # return Response('index-with-comp.html.html', headers=['Access-Control-Allow-Origin: *'])
    return render_template('index-with-comp.html')

# login func
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        human_trigger = request.form.get('human')
        bot_trigger = request.form.get('bot')
        if request.form['username'] not in ['admin1', 'admin2'] or request.form['password'] not in ['admin1', 'admin2']:
            error = 'Invalid Credentials. Please try again.'
        else:
            if human_trigger:
                session['username'] = request.form['username']
                session['steps'] = []
                return redirect(url_for('index'))
            elif bot_trigger:
                session['username'] = request.form['username']
                session['all_choices'] = [1,2,3,4,5,6,7,8,9]
                session['bot_steps'] = []
                session['steps'] = []
                return redirect(url_for('index_comp'))
    return render_template('login.html')


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



# function for display each events for game with bot on the right chat
@socketio.on('bot event', namespace='/test')
def test_message(message):
    name = session['username']
    emit('bot response', {'data': message['data'], 'name': name}, broadcast=broadcasting)


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




#game with bot
@socketio.on('bot cell event', namespace='/test')
def test_message(message):
    name = session['username']
    cell_id = int(message['data'])
    existing_steps = session.get('steps', 0)
    bot_existing_steps = session.get('bot_steps', 0)
    existing_steps.append(cell_id)
    session['steps'] = existing_steps
    for i in wins_combo:
        if i in get_all_combos(existing_steps):
            emit('bot wins response', {'data': message['data'], 'win': name}, broadcast=broadcasting)
            test_disconnect('Game Over')
            break
    my_left_choices = list(set(session['all_choices']).difference([cell_id]))
    if my_left_choices:
        next_bot_step = random.choice(my_left_choices)
        bot_left_choices = list(set(my_left_choices).difference([next_bot_step]))
        session['all_choices'] = bot_left_choices
        bot_existing_steps.append(next_bot_step)
        session['bot_steps'] = bot_existing_steps
    else:
        next_bot_step = None
    for j in wins_combo:
        if j in get_all_combos(bot_existing_steps):
            bot_name = 'Bot'
            emit('bot wins response', {'data': message['data'], 'win': bot_name, 'username': name}, broadcast=broadcasting)
            test_disconnect('Game Over')
            break
    emit('bot cell response', {'data': message['data'], 'name': name, 'bot_step': next_bot_step}, broadcast=broadcasting)



#connect function
@socketio.on('connect', namespace='/test')
def test_connect():
    name = session['username']
    emit('my connecting', {'data': 'Connected', 'name': name}, broadcast=broadcasting)


# disconnect function
@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected!')




#connect function
@socketio.on('bot connect', namespace='/test')
def test_connect():
    name = session['username']
    emit('bot connecting', {'data': 'Connected', 'name': name}, broadcast=broadcasting)


# disconnect function
@socketio.on('bot disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected!')


if __name__ == '__main__':
    socketio.run(app, debug=True, host='localhost', port=50001)
    # socketio.run(app)