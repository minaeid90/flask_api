from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import tweepy


app = Flask(__name__)

db = SQLAlchemy(app)

POSTGRES = {
    'user': 'admin',
    'pw': 'admin',
    'db': 'test',
    'host': 'localhost',
    'port': '5432',
}

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:\
%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(120), unique=True)

    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

    def __repr__(self):
        return '<user %r>' % self.name


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))

    def __init__(self, text, user_id):
        self.text = text
        self.user_id = user_id

    def __repr__(self):
        return '<Tweet %r>' % self.text


ACCESS_TOKEN = '278792533-ULd6ENiw5NX8xZ267qZ9KrlN1S3ZLYlB93APss4x'
ACCESS_SECRET = 'iLljQvUYRiAgSGVBxFNAQf5Gtst79sRyX6eCqu3gwkxno'
CONSUMER_KEY = 'HCYxyF5BQNt1VuCJ89HCVOlst'
CONSUMER_SECRET = 'xQuxW5qUGbshwD4cZHZ0WQ5mb6dWJ7GTd4mcJfcLQNQHriMjMb'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)


api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())


@app.route('/')
def index():
    return 'Home'


@app.route('/users/<int:user_id>')
def get_user(user_id):

    local = request.args.get('local')

    if local == 'true':

        user = User.query.filter_by(user_id=user_id).first()
        return jsonify({'user': [{'user_id': user.user_id, 'name': user.name}]})

    user = api.get_user(id=user_id)
    exists = db.session.query(db.exists().where(
        User.user_id == user['id'])).scalar()
    new_user = User(user_id=user['id'], name=user['screen_name'])

    if not exists:
        db.session.add(new_user)
        db.session.commit()
    return jsonify({'user': [{'user_id': user['id'], 'name': user['name']}]})


@app.route('/users/<int:id>/posts')
def get_tweets(id):
    local = request.args.get('local')
    if local == 'true':
        tweets_text = Tweet.query.all()
        return jsonify({'tweets': [{'tweets': tweet.text}for tweet in tweets_text]})

    latest_tweets = api.user_timeline(id=id, count=25)
    tweets_text = [tweet['text'] for tweet in latest_tweets]
    for tweet in latest_tweets:
        if Tweet.query.filter_by(text=tweet['text']).count() > 0:
            continue
        new_tweet = Tweet(text=tweet['text'],
                          user_id=api.get_user(id=id)['id'])
        db.session.add(new_tweet)
        db.session.commit()

    return jsonify({'tweets': tweets_text})


@app.route('/users/')
def get_users():
    users = User.query.all()
    return jsonify({'users': [{'user_id': user.user_id, 'name': user.name}for user in users]})


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
