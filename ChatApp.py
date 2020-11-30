"""
   * Author - danish
   * Date - 26/11/20
   * Time - 1:56 AM
   * Title - chatapp
"""
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
from flask_mysqldb import MySQL
from datetime import datetime
import os

app = Flask(__name__)
socketio = SocketIO(app)

# MySQL database connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.environ['username']
app.config['MYSQL_PASSWORD'] = os.environ['password']
app.config['MYSQL_DB'] = 'danishDB'

mysql = MySQL(app)

@app.route('/')
def home():
    """ Method Discription
    :return: To the Home Page
    """
    return render_template("index.html")

@app.route('/chat')
def chat():
    """ Method Discription
    :return: To the Chat Page
    """
    username = request.args.get('username')
    room = request.args.get('room')
    if username and room:
        return render_template('chat.html', username=username, room=room)
    else:
        return redirect(url_for('home'))

def create_tables():
    """ Method Discription
    Create Table in MySQL DataBase And Chat Detail
    """
    with app.app_context():
        cur = mysql.connection.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS user (id INT AUTO_INCREMENT PRIMARY KEY, \
                            username VARCHAR(20),room INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS chatDetail (id INT AUTO_INCREMENT PRIMARY KEY, \
                            message TEXT, send_on DATETIME,user_id INT ,FOREIGN KEY(user_id) REFERENCES user (id))")

        mysql.connection.commit()
        cur.close()
create_tables()

@socketio.on('join_room')
def handle_join_room(data):
    """ For Joining Room """
    print("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('send_message')
def handle_send_message_event(data):
    """ Method Discription
    For Send Massage
    """
    print("{} has sent message to the room {}: {}".format(data['username'],data['room'],data['message']))
    cur = mysql.connection.cursor()
    now = datetime.now()
    # extracting id from user table for current user and room
    cur.execute("SELECT id from user WHERE username=%s and room=%s", (data['username'], data['room']))
    id = cur.fetchall()
    if not id:
        table = """INSERT INTO user (username,room) VALUES (%s,%s)"""
        val = (data['username'], data['room'])
        cur.execute(table, val)
        user_id = cur.lastrowid
        table = """INSERT INTO chatDetail (message,send_on,user_id) VALUES (%s,%s,%s)"""
        val = (data['message'], now, user_id)
        cur.execute(table, val)
    else:
        table = """INSERT INTO chatDetail (message,send_on,user_id) VALUES (%s,%s,%s)"""
        val = (data['message'], now, id[0][0])
        cur.execute(table, val)
    mysql.connection.commit()
    cur.close()
    socketio.emit('receive_message', data, room=data['room'])

@socketio.on('leaveRoom')
def handle_leave_room_event(data):
    """ for handle leave room event """
    print("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])

if __name__ == '__main__':
    socketio.run(app, debug=True)
