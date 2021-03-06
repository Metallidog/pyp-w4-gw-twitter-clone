import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)

app = Flask(__name__)


def connect_db(db_name):
    return sqlite3.connect(db_name)

def _hash_password(password):
    """
    Uses md5 hashing for now
    """
    return md5(password.encode("utf-8").hexdigest())
    
#def _collect_tweet(user_id):
#    


@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url)) 
        return f(*args, **kwargs)
    return decorated_function

#to add our current directory to pythonpath
#PYTHONPATH=. python twitter_clone/runserver.py

# implement your views here

@app.route("/login/", methods = ["GET", "POST"])
def login():
    """
    Log in page
    """
    if request.method == 'GET':
        return render_template('login.html')
    
    elif request.method == "POST":
        
        username = request.form["username"]
        password = request.form["password"]
        # hashedPassword = _hash_password(password)

        #cursor = g.db.cursor()
        #Parametetrize SQL queries to prevent sql injection
        try:
            query = "SELECT id, username FROM user WHERE username = ? AND password = ?"
            cursor = g.db.execute(query, (username, password))
            # cursor = g.db.execute(query, (username, hashedPassword))
            results = cursor.fetchall()
        # if results == None: # not this
        #return username + password + str(results)  #empty list???
            user_id = results[0][0]
            username = results[0][1]
            session["logged_in"] = True
            session["user_id"] = str(user_id)
            session["username"] = username
            return redirect(url_for('display_feed', username = session['username']))
        except: # here
            
            return redirect(url_for('login'))

def _is_user_page(username):
    """
    Checks to see if the user is visiting his/her own timeline
    """
    return session['username'] == username

@app.route("/<username>", methods = ["GET", "POST"])
@login_required
def display_feed(username):
    
    if _is_user_page(username) == True:
        
        if request.method == 'GET':
            tweets = _retrieve_tweets(session['user_id'])
            return render_template('own_feed.html', tweets=tweets)
            
        if request.method == 'POST':
            #check if tweet is less than 140 chars, otherwise spit a message
            _post_tweet(session['user_id'], request.form['tweet'])
            # want to upload request.form['tweet'] = tweet text, need user_id that posted it
            tweets = _retrieve_tweets(session['user_id'])
            return render_template('own_feed.html', tweets=tweets)
            
    elif _is_user_page(username) == False:
        if request.method == 'GET':
            user_id = _get_user_id(username)
            tweets = _retrieve_tweets(user_id)
            return render_template('other_feed.html', tweets=tweets, username=username)

@app.route("/tweets/<tweet_id>/delete", methods = ["POST"])    
def delete(tweet_id):
    _delete_tweet(tweet_id)
    return redirect(url_for('own_feed', username = session['username']))

@app.route("/logout/")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/profile/", methods = ['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        profile_details = _get_profile_information(session['user_id'])
        # return str(profile_details[0][1])
        return render_template('profile.html', first_name=profile_details[0][0], last_name=profile_details[0][1], birth_date=profile_details[0][2])
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birth_date = request.form['birth_date']
        _profile_update(first_name, last_name, birth_date)
        return render_template('profile.html', first_name=first_name, last_name=last_name, birth_date=birth_date)

# DROP TABLE if exists user;
# CREATE TABLE user (
#   id INTEGER PRIMARY KEY autoincrement,
#   username TEXT NOT NULL,
#   password TEXT NOT NULL,
#   first_name TEXT,
#   last_name TEXT,
#   birth_date DATE,
#   CHECK (
#       length("birth_date") = 10
#   )
# );

    
@app.route('/')
#@login_required()
def homepage():
    return redirect(url_for('login'))

#SQL query helper functions
def _post_tweet(user_id, tweet_text):
    query = 'INSERT INTO "tweet" ("user_id", "content") VALUES (?, ?)'
    g.db.execute(query, (user_id, tweet_text))
    g.db.commit()
    
def _delete_tweet(tweet_id):
    query = "DELETE FROM 'tweet' WHERE id = ?"
    g.db.execute(query, (tweet_id,))
    g.db.commit()
    
def _retrieve_tweets(user_id):
    query = "SELECT id, created, content FROM tweet WHERE user_id = ? ORDER BY created desc"
    cursor = g.db.execute(query, (user_id,))
    tweets = [dict(tweet_id = str(row[0]), created = row[1], content = row[2]) for row in cursor.fetchall()]
    return tweets

def _get_user_id(username):
    query = "SELECT id FROM 'user' WHERE username = ?"
    cursor = g.db.execute(query, (username,))
    result = cursor.fetchall()
    user_id = str(result[0][0])
    return user_id

def _profile_update(first_name, last_name, birth_date):
    if len(birth_date) != 10:
        query = "UPDATE user SET first_name = ?, last_name = ? WHERE id = ?"
        g.db.execute(query, (first_name, last_name, session['user_id']))
    else:
        query = "UPDATE user SET first_name = ?, last_name = ?, birth_date = ? WHERE id = ?"
        g.db.execute(query, (first_name, last_name, birth_date, session['user_id']))
    g.db.commit()

def _get_profile_information(user_id):
    query = "SELECT first_name, last_name, birth_date FROM user WHERE id = ?"
    cursor = g.db.execute(query, (user_id,))
    results = cursor.fetchall()
    return results

if __name__ == "__main__":
    app.run()