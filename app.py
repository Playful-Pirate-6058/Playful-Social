import base64
import json
from random import randint
from flask import Flask, render_template, redirect, url_for, request, send_from_directory, jsonify, flash, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import socket
from datetime import date, datetime, timedelta
import os
import requests
import json

server_ip = socket.gethostbyname(socket.gethostname())
app = Flask(__name__)
sess = Session(app)
app.secret_key = 'c49m382v5p0m2498xuv9mh9hmxg934mcg9'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
sess.init_app(app)

def API_URL(task): return "https://hereus.pythonanywhere.com/API/"+task

def strings(region):
    return json.load(open("languages/"+region+".json", encoding="UTF-8"))

def today_date_to_number():
    return int(str(datetime.utcnow()).replace(":","").replace(" ","").replace("-","").split(".")[0])

def milattanturk(tarih):
    if "." in str(int(str(tarih.date()).split("-")[0])/4):
        tarih = tarih - timedelta(days=79)
    else:
        tarih = tarih - timedelta(days=78)
    yil = str(int(str(tarih.date()).split("-")[0])+209)
    hayvanlar = ["Lu", "Yılan", "Yond", "Koy", "Biçin", "Taguk", "İt", "Tonguz", "Sıçgan", "Ud", "Bars"]
    hayvan = hayvanlar[(int(yil)-(int(str(int(yil)/12).split(".")[0])*12))-1]
    kalan = str(tarih.date()).replace(str(tarih.date()).split("-")[0], "")
    return yil+kalan

def number_to_date(number):
    return datetime(int(str(number)[:4]),int(str(number)[4:][:2]),int(str(number)[6:][:2]), int(str(number)[8:][:2]),int(str(number)[10:][:2]),int(str(number)[12:][:2]),int(str(number)[14:][:2]))

@app.route('/')
def index():
    return redirect(url_for("feed"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            cuser = json.loads(requests.post(API_URL('DATA_USER'), data={"email":request.form['email'],"password":request.form['password'],"user":request.form['email'],"posts_included":"false"}).content)
            cuser.update({"email":request.form['email']})
            cuser.update({"password":request.form['password']})
            session['cuser'] = cuser
            print(session)
            if session['cuser'] == cuser: return redirect(url_for('feed'))
            else: return render_template('login.html', plus=cuser["plus"],message="We couldn't verify you because session is broken")
        except Exception as e: return render_template('login.html', plus=cuser["plus"],message="We couldn't verify you because "+str(e)[:1].lower()+str(e)[1:])
    return render_template('login.html', plus=False,message="")

#PLAYFUL CODE :)))
@app.route("/post/<id>", methods=["GET","POST"])
def posts(id):
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    if request.method == "POST":
        requests.post(API_URL('SEND_COMMENT'), data={'email':cuser['email'],'password':cuser['password'],'content':request.form['content'],'container':'post>'+id})
        return redirect(request.url)
    else:
        posted = json.loads(requests.post(API_URL('DATA_POST'), data={'email':cuser['email'],'password':cuser['password'],'id':id}).content)
        comments = posted["comments"]
        return render_template("posts.html", posted=posted, comments=comments, posted_id=str(id), current_user=cuser, plus=cuser["plus"], strings=strings(cuser['region']))

#PLAYFUL CODE :)))
@app.route('/feed/communities/<name>', methods=['GET','POST'])
def community(name):
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    if request.method == 'POST':
        requests.post(API_URL('SEND_POST'), data={'email':cuser['email'],'password':cuser['password'],'content':request.form['content'],'community':name})
        return redirect(url_for('feed'))
    community = json.loads(requests.post(API_URL('FEED_COMMUNITY'), data={'email':cuser['email'], 'password':cuser['password'], 'community':name}).content)['data']
    posts = community['posts']
    member_count = community['community_info']['member_count']
    if not "#" in community['community_info']['title']:
        return render_template('community.html', timedelta=timedelta, community_is=community, name=cuser['username'], email=cuser['email'], posts=posts, friends=cuser['friends'], current_user=cuser, member_count=str(member_count), communities=communities, plus=cuser["plus"],strings=strings(cuser['region']))
        #except: return community['community_info']
    if (community['name'].split("#")[1])[:1] == "-":
        return render_template('communitychat.html', timedelta=timedelta, community_is=community, name=cuser['username'], email=cuser['email'], posts=posts, friends=cuser['friends'], current_user=cuser, member_count=str(member_count), communities=communities, plus=cuser["plus"],strings=strings(cuser['region']))
    elif community['name'].split("#")[1] == "Etkinlikler":
        return render_template('community_events.html', timedelta=timedelta, community_is=community, name=cuser['username'], email=cuser['email'], posts=posts, friends=cuser['friends'], current_user=cuser, member_count=str(member_count), communities=communities, plus=cuser["plus"],strings=strings(cuser['region']))
    else:
        return render_template('community.html', timedelta=timedelta, community_is=community, name=cuser['username'], email=cuser['email'], posts=posts, friends=cuser['friends'], current_user=cuser, member_count=str(member_count), communities=communities, plus=cuser["plus"],strings=strings(cuser['region']))

#PLAYFUL CODE :)))
@app.route('/search', methods=['POST','GET'])
def search():
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    if request.method == "POST":
        key = request.form['key']
        results = json.loads(requests.post(API_URL('SEARCH_KEY'), data={'email':cuser['email'], 'password':cuser['password'], 'key':key}).content)
        return render_template('search.html', communities_search=results['communities'], accounts_search=results['users'], communities_all=results['communities'], accounts_all=results['users'], key=key, posts=results['posts'], plus=cuser["plus"],strings=strings(cuser['region']), current_user=cuser)
    else:
        posts_allall = Posts.query.order_by(Posts.date_created).all()
        posts_allall.reverse()
        accounts_allall = User.query.order_by(User.id).all()
        tags_from_friends = []
        for post in posts_allall:
            if post.email in current_user.friends:
                follow_count = -1
                for account in accounts_allall:
                    if post.email+";" in account.friends:
                        follow_count = follow_count + 1
                if follow_count > 0:
                    posts_from_friends_words = post.text.replace("|||","||| ").replace("<!--"," <!--").split(" ")
                    for word in posts_from_friends_words:
                        if word[:1] == "#":
                            tags_from_friends.append(word)
        communities = Communities.query.order_by(Communities.name).all()
        accounts = User.query.order_by(User.id).all()
        return render_template('trends.html', timedelta=timedelta, name=current_user.username, email=current_user.email, accounts=accounts, friends=current_user.friends, plus=cuser["plus"], strings=strings(cuser['region']), communities=communities, tags_from_friends=tags_from_friends)

#PLAYFUL CODE :)))
@app.route('/feed/follows', methods=['GET', 'POST'])
def feed():
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: print(session); return redirect(url_for('login'))
    if request.method == 'POST':
        requests.post(API_URL('SEND_POST'), data={'email':cuser['email'],'password':cuser['password'],'content':request.form['content'],'community':''})
        return redirect(url_for('feed'))
    posts = json.loads(requests.post(API_URL('FEED_FOLLOWS'), data=cuser).content)['data']
    mails_in_feed = {}
    for post in posts: mails_in_feed.update({post['email']:post['username']})
    friends = {}
    for friend in cuser['friends']:
        if not friend == '':
            try:
                if friend in mails_in_feed: friends.update({friend:mails_in_feed[friend]})
                else:
                    friends.update({friend:json.loads(requests.post(API_URL('DATA_USER'), data={"email":cuser["email"],"password":cuser["password"],"user":friend,"posts_included":"false"}).content)['username']})
            except: friends.update({friend:friend})
    return render_template('feed.html', timedelta=timedelta, name=cuser["username"], email=cuser["email"], posts=posts, friends=cuser["friends"], plus=cuser["plus"], strings=strings(cuser['region']), communities=communities, current_user=cuser, accounts=friends)

#PLAYFUL CODE :)))
@app.route('/feed/articles', methods=['GET', 'POST'])
def articles():
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    articles = json.loads(requests.post(API_URL('FEED_ARTICLES'), data=cuser).content)['data']
    articles.reverse()
    return render_template('article_feed.html', timedelta=timedelta, current_user=cuser, articles=articles, plus=cuser["plus"], strings=strings(cuser['region']))

#PLAYFUL CODE :)))
@app.route('/feed/articles/read/<id>')
def article(id):
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    article = json.loads(requests.post(API_URL('DATA_ARTICLE'), data={'email':cuser['email'],'password':cuser['password'],'id':id}).content)
    return render_template("article.html", article=article, plus=cuser["plus"], strings=strings(cuser['region']), current_user=cuser)

#PLAYFUL CODE :)))
@app.route('/feed/explore', methods=['GET', 'POST'])
def explore():
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    if request.method == 'POST':
        requests.post(API_URL('SEND_POST'), data={'email':cuser['email'],'password':cuser['password'],'content':request.form['content'],'community':''})
        return redirect(url_for('feed'))
    posts = json.loads(requests.post(API_URL('FEED_EXPLORE'), data=cuser).content)['data']
    mails_in_feed = {}
    for post in posts: mails_in_feed.update({post['email']:post['username']})
    friends = {}
    for friend in cuser['friends']:
        if not friend == '':
            try:
                if friend in mails_in_feed: friends.update({friend:mails_in_feed[friend]})
                else:
                    friends.update({friend:json.loads(requests.post(API_URL('DATA_USER'), data={"email":cuser["email"],"password":cuser["password"],"user":friend,"posts_included":"false"}).content)['username']})
            except: friends.update({friend:friend})
    return render_template('explore.html', timedelta=timedelta, name=cuser["username"], email=cuser["email"], posts=posts, friends=cuser["friends"], plus=cuser["plus"], strings=strings(cuser['region']), communities=communities, current_user=cuser, accounts=friends)

#PLAYFUL CODE :)))
@app.route('/feed/communities', methods=['GET', 'POST'])
def communities():
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    communities = cuser['communities']
    return render_template('communities.html', name=cuser['username'], email=cuser['email'], current_user=cuser, posts=posts, friends=cuser['friends'], communities=communities, plus=cuser["plus"], strings=strings(cuser['region']))

#PLAYFUL CODE :)))
@app.route('/delpost/<id>')
def del_post(id):
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    requests.post(API_URL('REMOVE_POST'), data={'email':cuser['email'],'password':cuser['password'],'id':id})
    return redirect(url_for('user', email=cuser['email']))

#PLAYFUL CODE :)))
@app.route('/delcomment/<id>')
def del_comment(id):
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    requests.post(API_URL('REMOVE_COMMENT'), data={'email':cuser['email'],'password':cuser['password'],'id':id})
    return redirect(url_for('user', email=cuser['email']))

@app.route('/logout')
def logout():
    session['cuser'] = {}
    return redirect(url_for('feed'))

#PLAYFUL CODE :)))
@app.route('/user/<email>/follow')
def follow(email):
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    requests.post(API_URL('FOLLOW_USER'), data={'email':cuser['email'],'password':cuser['password'],'user':email})
    return redirect(url_for('user', email=email))

#PLAYFUL CODE :)))
@app.route('/user/<email>')
def user(email):
    try: cuser = session['cuser']; print(session['cuser']['email'])
    except: return redirect(url_for('login'))
    user = json.loads(requests.post(API_URL('DATA_USER'), data={'email':cuser['email'],'password':cuser['password'],'user':email, 'posts_included':'true'}).content)
    posts_safe = user["posts"]
    mails_in_feed = {}
    friends = {}
    for friend in cuser['friends']:
        if not friend == '':
            try:
                if friend in mails_in_feed: friends.update({friend:mails_in_feed[friend]})
                else:
                    friends.update({friend:json.loads(requests.post(API_URL('DATA_USER'), data={"email":cuser["email"],"password":cuser["password"],"user":friend,"posts_included":"false"}).content)['username']})
            except: friends.update({friend:friend})
    return render_template('user.html', user=user, posts=posts_safe, current_user=cuser, plus=user["plus"], strings=strings(cuser['region']), friends=friends)

if __name__ == '__main__':
    app.run(debug=True, port=8000)