from flask import Flask, render_template, session, redirect, request
from flask_socketio import SocketIO, send, emit
import sqlite3
import os
import json
import datetime
import time as t

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins='*')

print('App Ready!')

# * date operations

def getYYYYMMDD(date):
    return str(datetime.datetime.strptime(date, '%a %b %d %Y').date())

def getEnglishDate(date):
    return str(datetime.datetime.strptime(date, '%Y-%m-%d').ctime().replace('00:00:00', ''))

# * db operations

def createUsersTable():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT,
        password TEXT
    )
    ''')

    conn.commit()
    conn.close()

def createMessagesTable():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        data TEXT
    )
    ''')

    conn.commit()
    conn.close()

def createCleanupsTable():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS cleanups (
        cleanupDate TEXT
    )
    ''')

    conn.commit()
    conn.close()

def createUserCleanupTable():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS userCleanup (
        username TEXT,
        cleanupDate TEXT
    )
    ''')

    conn.commit()
    conn.close()

def createUserPointsTable():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS userPoints (
        username TEXT,
        userPoints INTEGER
    )
    ''')

    conn.commit()
    conn.close()

def clearUserDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('DELETE FROM users')

    conn.commit()
    conn.close()

    clearAllSessions()

def clearMessagesDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('DELETE FROM messages')

    conn.commit()
    conn.close()

def clearCleanupsDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('DELETE FROM cleanups')

    conn.commit()
    conn.close()

def clearUserCleanupDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('DELETE FROM userCleanup')

    conn.commit()
    conn.close()

def clearUserPointsDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('DELETE FROM userPoints')

    conn.commit()
    conn.close()

def resetUserPointsDb():
    clearUserPointsDb()
    for user, _ in readUserDb():
        initializeOneUsersPointsDb(user)

def readUserDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('SELECT * FROM users')
    users = c.fetchall()
    conn.close()

    return users

def readMessagesDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('SELECT data FROM messages')
    rows = c.fetchall()

    messages = [json.loads(row[0]) for row in rows]

    conn.close()
    return messages

def readCleanupsDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('SELECT * FROM cleanups')
    cleanups = c.fetchall()
    conn.close()

    return cleanups

def readUserCleanupDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('SELECT * FROM userCleanup')
    data = c.fetchall()
    conn.close()

    return data

def readUserPointsDb():
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute('SELECT * FROM userPoints')
    data = c.fetchall()
    conn.close()

    return data

def addUserDb(username, password):
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

    conn.commit()
    conn.close()

    return True

def addMessageDb(username, message, userPoints):
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    payload = {
        'username': username,
        'message': message,
        'userPoints': userPoints
    }

    messageJson = json.dumps(payload)

    c.execute("INSERT INTO messages (data) VALUES (?)", (messageJson,))
    
    conn.commit()
    conn.close()

def addCleanupDb(cleanupDate):
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute("INSERT INTO cleanups (cleanupDate) VALUES (?)", (cleanupDate,))

    conn.commit()
    conn.close()

    return True

def addUserCleanupDb(username, cleanupDate):
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    c.execute("INSERT INTO userCleanup (username, cleanupDate) VALUES (?, ?)", (username, cleanupDate))

    conn.commit()
    conn.close()

    return True

def initializeOneUsersPointsDb(username):
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    # ? Start at 0 points for now? Maybe start at 10 or some ambiguous point
    c.execute("INSERT INTO userPoints (username, userPoints) VALUES (?, ?)", (username, 0))

    conn.commit()
    conn.close()

    return True

def getOneUsersPoints(username):
    for user, userPoints in readUserPointsDb():
        print(user, userPoints, username)
        if user == username:
            return userPoints
    raise Exception('User not found!')

def addUserPointsDb(username, additionalPoints):
    currentPoints = getOneUsersPoints(username)
    

    conn = sqlite3.connect('climate.db')
    c = conn.cursor()

    finalPoints = currentPoints + additionalPoints

    c.execute("""
    UPDATE userPoints
    SET userPoints = ?
    WHERE username = ?
    """, (finalPoints, username))

    conn.commit()
    conn.close()

    return True

def userInDb(username):
    for curUser, _ in readUserDb():
        if curUser == username:
            return True
    return False 

def userAndPasswordInDb(username, password):
    for curUser, curPass in readUserDb():
        if curUser == username and curPass == password:
            return True
    return False 

def userInCleanupDb(username):
    for curUser, _ in readCleanupsDb():
        if curUser == username:
            return True
    return False 

def usersInACleanupDate(cleanupDate):
    users = []
    for curUser, curDate in readUserCleanupDb():
        if curDate == cleanupDate:
            users.append(curUser)
    return users 

def cleanupDatesUserIsIn(username):
    dates = []
    for curUser, curDate in readUserCleanupDb():
        if curUser == username:
            dates.append(curDate)
    return dates

def deleteCleanup(cleanupDate):
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()
    
    print([f"DELETE FROM cleanups WHERE cleanupDate = '{cleanupDate[0]}'"])
    c.execute(f"DELETE FROM cleanups WHERE cleanupDate = '{cleanupDate[0]}'")

    conn.commit()
    conn.close()

    return True

def deleteUserCleanup(username, cleanupDate):
    conn = sqlite3.connect('climate.db')
    c = conn.cursor()
    c.execute(f"DELETE FROM userCleanup WHERE cleanupDate = '{cleanupDate}' AND username = '{username}'")

    conn.commit()
    conn.close()

    return True
    
def clearAllSessions():
    app.secret_key = os.urandom(32)

def checkToClearAnyExpiredCleanups():
    currentCleanups = readCleanupsDb()
    currentDate = str(datetime.date.today())
    for date in currentCleanups:
        print(date[0], currentDate)
        date1 = datetime.datetime.strptime(date[0], "%Y-%m-%d").date()
        date2 = datetime.datetime.strptime(currentDate, "%Y-%m-%d").date()
        if date1 < date2:
            deleteCleanup(date)
            for user in usersInACleanupDate(date[0]):
                deleteUserCleanup(user, date[0])
                # * Add some points for completing a cleanup! - Incentive for ppl to join and attend the cleanups
                print('------------------------------ adding to', {user}, '1000 points')
                addUserPointsDb(user, 1000)

app.secret_key = 'verySecretKey295738$&*#&./,'

createUsersTable()
createMessagesTable()
createCleanupsTable()
createUserCleanupTable()
createUserPointsTable()

checkToClearAnyExpiredCleanups()

print('Database Ready!')

def plainTextPage(text:str, link, linkText):    
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Flight Pingr</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                text-align: center;
            }
            h1 {
                color: #333;
                font-size: 36px;
                margin-bottom: 20px;
            }
            p {
                color: #666;
                font-size: 18px;
            }
        </style>
        <style>
            .link {
                color: #93a782; /* Link color */
                text-decoration:none; /* Underline to mimic link */
                cursor: pointer; /* Change cursor to pointer on hover */
                font-size: 20px;
                margin-top: 40px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>''' + text + '''</h1>
            <div class="link" onclick="window.location.href=\''''+link+'''\'">'''+linkText+'''</div>
        </div>
    </body>
    </html>
    '''

@app.before_request
def checkForExpiredCleanupsBeforeRequest():
    checkToClearAnyExpiredCleanups()

# * webapp route operations

@app.route('/')
def goToChat():
    return redirect('/chat')

@app.route('/chat')
def chat():
    if session.get('loggedIn'):
        username = session.get('username')
        print(username)
        return render_template('chat.html', username=username)
    else:
        return redirect('/login', 302)

@app.route('/register')
def registerPage():
    return render_template('registerAccount.html')

@app.route('/login')
def loginPage():
    if session.get('loggedIn'):
        return redirect('/chat')
    else:
        return render_template('loginPage.html')

@app.route('/loginAuth', methods=['POST'])
def loginAuth():
    username = request.form['username'].strip()
    password = request.form['password'].strip()

    if username and password:
        if not userAndPasswordInDb(username, password):
            return plainTextPage('Incorrect Credentials', '/login', 'Retry?')
        else:
            session['loggedIn'] = True
            session['username'] = username
            session['password'] = password
            return redirect('/chat')
    else:
        return plainTextPage('Blank Username or Password', '/login', 'Retry?')
    

@app.route('/registerAuth', methods=['POST'])
def registerAuth():
    username = request.form['username'].strip()
    password = request.form['password'].strip()

    if username and password:
        if userInDb(username):
            return plainTextPage('Username Taken', '/register', 'Retry?')
        else:
            addUserDb(username, password)
            initializeOneUsersPointsDb(username)
            return redirect('/login')
    else:
        return plainTextPage('Blank Username or Password', '/register', 'Retry?')


@app.route('/cleanups')
def cleanupsPage():
    if session.get('loggedIn'):        
        dates = [i[0] for i in readCleanupsDb()]
        for i in range(len(dates)):
            dates[i] = getEnglishDate(dates[i])

        if dates:
            return render_template('cleanups.html', dates=dates)
        else:
            return plainTextPage('No Cleanups Scheduled', '/chat', 'Go back?')
    else:
        return redirect('/login')

@app.route('/createCleanup')
def createCleanupPage():
    if session.get('loggedIn') == True:
        return render_template('createCleanup.html')
    else:
        return redirect('/login')


@app.route('/createCleanupAuth', methods=['POST'])
def createCleanupAuth():
    if session.get('loggedIn'):
        date = request.form['date']
        for i in readCleanupsDb():
            if date == i[0]:
                return redirect('/cleanups')

        addCleanupDb(date)
        return redirect('/cleanups')
    else:
        return redirect('/login')


@app.route('/cleanups/date/<date>')
def viewOneCleanup(date):
    if session.get('loggedIn'):
        date = date.replace('%20', ' ')

        if usersInACleanupDate(getYYYYMMDD(date)):
            signedUp = True
        else:
            signedUp = False

        return render_template('viewCleanupDate.html', users=usersInACleanupDate(getYYYYMMDD(date)), date=date, signedUp=signedUp)
    else:
        return redirect('/login')

@app.route('/cleanupSignupAuth/date/<date>', methods=['GET'])
def cleanupSignupAuth(date):
    if session.get('loggedIn'):
        date = str(getYYYYMMDD(date))
        if session['username'] in usersInACleanupDate(date):
            return redirect(f'/cleanups/date/{getEnglishDate(date)}')
        else:
            addUserCleanupDb(session['username'], date)
            return redirect(f'/cleanups/date/{getEnglishDate(date)}')
    else:
        return redirect('/login')
    
@app.route('/cleanupLeaveAuth/date/<date>', methods=['GET'])
def cleanupLeaveAuth(date):
    if session.get('loggedIn'):
        date = str(getYYYYMMDD(date))
        if session['username'] in usersInACleanupDate(date):
            deleteUserCleanup(session['username'], date)
            return redirect(f'/cleanups/date/{getEnglishDate(date)}')
        else:
            return redirect(f'/cleanups/date/{getEnglishDate(date)}')            
    else:
        return redirect('/login')

@app.route('/yourCleanups')
def yourCleanups():
    if session.get('loggedIn'):
        dates = [getEnglishDate(date) for date in cleanupDatesUserIsIn(session['username'])]
        if dates:
            return render_template('yourCleanups.html', dates=dates)
        else:
            return plainTextPage('You Have No Cleanups Scheduled', '/chat', 'Go back?')        
    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    session['loggedIn'] = False
    return redirect('/login') 


# * websocket operations

@socketio.on('connect')
def handleConnect():
    print('User Connected')

    messages = readMessagesDb()

    st = t.time()
    
    finalIndex = len(messages) - 1
    for messageIndex, messageJson in enumerate(messages):
        if messageIndex != finalIndex:
            messageJson['connect'] = True
        else:
            messageJson['connect'] = False
        emit('message', messageJson)
    print(t.time()-st, 'message load time')
    

@socketio.on('message')
def handleMessage(msg):
    print('Message:', msg)
    if msg['message'] != 'Client Connected':
        if msg['message'] == '/clearMessages':
            emit('clearMessages', {'data': 'clearMessages'}, broadcast=True)
            clearMessagesDb()
        elif msg['message'] == '/clearSessions':
            emit('reloadPage', {'data': 'reloadPage'}, broadcast=True)
            clearAllSessions()
        elif msg['message'] == '/clearUsers':
            emit('reloadPage', {'data': 'reloadPage'}, broadcast=True)
            clearUserDb()
        elif msg['message'] == '/clearCleanups':
            emit('reloadPage', {'data': 'reloadPage'}, broadcast=True)
            clearCleanupsDb()
        elif msg['message'] == '/clearUserCleanups':
            emit('reloadPage', {'data': 'reloadPage'}, broadcast=True)
            clearUserCleanupDb()
        elif msg['message'] == '/clearUserPoints':
            emit('reloadPage', {'data': 'reloadPage'}, broadcast=True)
            resetUserPointsDb()
        else:
            # * Add some points for a user chatting
            addUserPointsDb(msg['username'], 5)

            msg['userPoints'] = getOneUsersPoints(msg['username'])
            print('  Modified Message:', msg)

            addMessageDb(msg['username'], msg['message'], msg['userPoints'])
            send(msg, broadcast=True)
            

@app.errorhandler(404)
def notExistent(e):
    return plainTextPage('Page Not Found!', '/', 'Go back to safety?')         
    
if __name__ == '__main__':
    # socketio.run(app, host='localhost', port=5000)
    socketio.run(app, host='0.0.0.0', port=10000, allow_unsafe_werkzeug=True)    
