import flask
from flask.ext import oauth

from sirius.models import user
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
    consumer_key='DdrpQ1uqKuQouwbCsC6OMA4oF',
    consumer_secret='S8XGuhptJ8QIJVmSuIk7k8wv3ULUfMiCh9x1b19PmKSsBh1VDM',
)


@twitter.tokengetter
def get_twitter_token(token=None):
    return flask.session.get('twitter_token')


@blueprint.route('/twitter/login')
def login():
    # Clear token, see https://github.com/mitsuhiko/flask-oauth/issues/48:
    flask.session.pop('twitter_token', None)
    flask.session.pop('twitter_screen_name', None)

    return twitter.authorize(callback=flask.url_for('twitter_oauth.oauth_authorized',
        next=flask.request.args.get('next') or flask.request.referrer or None))


@blueprint.route('/twitter/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(response):
    next_url = flask.request.args.get('next') or '/'
    if response is None:
        flask.flash(u"Twitter didn't authorize our sign-in request.")
        return flask.redirect(next_url)

    flask.session['twitter_token'] = (
        response['oauth_token'],
        response['oauth_token_secret'],
    )
    flask.session['twitter_screen_name'] = response['screen_name']

    oauth = db.session.query(user.TwitterOAuth).filter_by(
        screen_name=response['screen_name'],
    ).first()

    # Create local user model for keying resources (e.g. claim codes)
    # if we haven't seen this twitter user before.
    if oauth is None:
        new_user = user.User(
            username=response['screen_name'],
        )
        db.session.add(new_user)
        db.session.add(user.TwitterOAuth(
            user=new_user,
            screen_name=response['screen_name'],
            token=response['oauth_token'],
        ))
        db.session.commit()

    return flask.redirect(next_url)
