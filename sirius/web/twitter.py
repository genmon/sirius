from __future__ import absolute_import

import os
import datetime
import flask
from gevent import pool
from flask.ext import oauth
from flask.ext import login

import twitter as twitter_api

from sirius.models import user as user_model
from sirius.models.db import db


blueprint = flask.Blueprint('twitter_oauth', __name__)
oauth_app = oauth.OAuth()

# TODO move the consumer_key/secret to flask configuration. The
# current key is a test app that redirects to 127.0.0.1:8000.
twitter = oauth_app.remote_app(
    'twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=os.environ.get('TWITTER_CONSUMER_KEY', 'DdrpQ1uqKuQouwbCsC6OMA4oF'),
    consumer_secret=os.environ.get('TWITTER_CONSUMER_SECRET', 'S8XGuhptJ8QIJVmSuIk7k8wv3ULUfMiCh9x1b19PmKSsBh1VDM'),
)


@twitter.tokengetter
def get_twitter_token(token=None):
    return flask.session.get('twitter_token')


@blueprint.route('/twitter/login')
def twitter_login():
    # Clear token, see https://github.com/mitsuhiko/flask-oauth/issues/48:
    flask.session.pop('twitter_token', None)
    flask.session.pop('twitter_screen_name', None)

    return twitter.authorize(callback=flask.url_for('twitter_oauth.oauth_authorized',
        next=flask.request.args.get('next') or flask.request.referrer or None))

@blueprint.route('/twitter/logout')
def twitter_logout():
    flask.session.pop('user_id', None)
    flask.flash('You were signed out')
    return flask.redirect('/')

@blueprint.route('/twitter/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(response):
    next_url = flask.request.args.get('next') or '/'

    if response is None:
        flask.flash(u"Twitter didn't authorize our sign-in request.")
        return flask.redirect(next_url)

    return process_authorization(
        response['oauth_token'],
        response['oauth_token_secret'],
        response['screen_name'],
        next_url,
    )


def process_authorization(token, token_secret, screen_name, next_url):
    """Process the incoming twitter oauth data. Validation has already
    succeeded at this point and we're just doing the book-keeping."""

    flask.session['twitter_token'] = (token, token_secret)
    flask.session['twitter_screen_name'] = screen_name

    oauth = user_model.TwitterOAuth.query.filter_by(
        screen_name=screen_name,
    ).first()

    # Create local user model for keying resources (e.g. claim codes)
    # if we haven't seen this twitter user before.
    if oauth is None:
        new_user = user_model.User(
            username=screen_name,
        )

        oauth = user_model.TwitterOAuth(
            user=new_user,
            screen_name=screen_name,
            token=token,
            token_secret=token_secret,
            last_friend_refresh=datetime.datetime.utcnow(),
        )

        # Fetch friends list from twitter. TODO: error handling.
        friends = get_friends(new_user)
        oauth.friends = friends

        db.session.add(new_user)
        db.session.add(oauth)
        db.session.commit()

    login.login_user(oauth.user)

    return flask.redirect(next_url)


def get_friends(user):
    api = twitter_api.Twitter(auth=twitter_api.OAuth(
        user.twitter_oauth.token,
        user.twitter_oauth.token_secret,
        twitter.consumer_key,
        twitter.consumer_secret,
    ))
    # Twitter allows lookup of 100 users at a time so we need to
    # chunk:
    chunk = lambda l, n: [l[x:x+n] for x in xrange(0, len(l), n)]
    friend_ids = list(api.friends.ids()['ids'])

    greenpool = pool.Pool(4)

    # Look up in parallel. Note that twitter has pretty strict 15
    # requests/second rate limiting.
    friends = []
    for result in greenpool.imap(
            lambda ids: api.users.lookup(user_id=','.join(str(id) for id in ids)),
            chunk(friend_ids, 100)):
        for r in result:
            friends.append(user_model.Friend(
                screen_name=r['screen_name'],
                name=r['name'],
                profile_image_url=r['profile_image_url'],
            ))

    return sorted(friends)
