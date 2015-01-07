"""User models. Login only via twitter for now to avoid the whole
forgot-password/reset-password dance.
"""
from sirius.models.db import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    # username can't be unique because we may have multiple identity
    # providers. For now we just copy the  twitter handle.
    username = db.Column(db.String)


class TwitterOAuth(db.Model):
    __tablename__ = 'twitter_oauth'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    screen_name = db.Column(db.String, unique=True)
    token = db.Column(db.String, unique=True)

TwitterOAuth.user = db.relationship(
    User,
    primaryjoin=TwitterOAuth.user_id==User.id,
    backref=db.backref('twitteroauth', lazy='dynamic'),
)
