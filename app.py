from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskdb'

mysql = MySQL(app)

Session(app)

socketio = SocketIO(app, manage_session=False)


@app.route('/', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/validate-login', methods=['GET', 'POST'])
def validateLogin():
    username = request.form["username"]
    password = request.form["password"]
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM users WHERE name = '" + username + "' AND password = '" + password + "' OR email = '" + username + "' AND password = '" + password + "'"
    users = cursor.execute(query)
    mysql.connection.commit()
    cursor.close()
    if users > 0:
        return redirect(url_for("home", username = username))
    return redirect("/")

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/validate-register', methods=['GET', 'POST'])
def validateRegister():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    cursor = mysql.connection.cursor()
    query = "INSERT INTO users (name, email, password) VALUES ('"+ username +"', '"+ email +"', '"+ password +"')"
    cursor.execute(query)
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("home", username = username))

@app.route('/history', methods=['GET', 'POST'])
def history():
    username = request.args.get("username")
    print(username)
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM history WHERE username = '" + username + "'"
    data = cursor.execute(query)
    if data > 0:
        historyData = cursor.fetchall()
        return render_template('history.html', historyData = historyData)

@app.route('/home', methods=['GET', 'POST'])
def home():
    username = request.args.get('username')
    return render_template('index.html', username = username)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if(request.method=='POST'):
        username = request.form['username']
        room = request.form['room']

        # Store the details in the database.
        cursor = mysql.connection.cursor()
        query = "INSERT INTO history (username, room) VALUES ('"+ username +"', '"+ room +"')"
        cursor.execute(query)
        mysql.connection.commit()
        cursor.close()

        #Store the data in session
        session['username'] = username
        session['room'] = room
        return render_template('chat.html', session = session, username = username)
    else:
        if(session.get('username') is not None):
            return render_template('chat.html', session = session)
        else:
            return redirect(url_for('home'))

@socketio.on('join', namespace='/chat')
def join(message):
    room = session.get('room')
    join_room(room)
    emit('status', {'msg':  session.get('username') + ' has entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    room = session.get('room')
    emit('message', {'msg': '<b>' + session.get('username') + ':</b> ' + message['msg']}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)


if __name__ == '__main__':
    socketio.run(app)