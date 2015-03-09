import flask
import flask_wtf
import wtforms
from flask.ext import login
import datetime

from sirius.coding import claiming
from sirius.web import twitter


blueprint = flask.Blueprint('landing', __name__)


class ClaimForm(flask_wtf.Form):
    claim_code = wtforms.StringField(
        'Claim code',
        validators=[wtforms.validators.DataRequired()],
    )
    printer_name = wtforms.StringField(
        'Name your printer',
        validators=[wtforms.validators.DataRequired()],
    )

    def validate_claim_code(self, field):
        try:
            claiming.unpack_claim_code(field.data)
        except claiming.InvalidClaimCode:
            raise wtforms.validators.ValidationError(
                "`{}` doesn't look like a valid claim code :(".format(field.data)
            )


class TwitterRefreshFriendsForm(flask_wtf.Form):
    "CSRF-only form."

@blueprint.route('/about')
def about():
	return flask.render_template('about.html')

@blueprint.route('/')
def landing():
    if not login.current_user.is_authenticated():
        return flask.render_template('landing.html')

    return overview()


@login.login_required
def overview():
    user = login.current_user
    my_printers = user.printers.all()

    friends, signed_up_friends = user.signed_up_friends()
    form = TwitterRefreshFriendsForm()

    friends_printers = user.friends_printers()

    return flask.render_template(
        'overview.html',
        form=form,
        my_printers=my_printers,
        signed_up_friends=list(signed_up_friends),
        friends=friends,
        friends_printers=list(friends_printers),
        seconds_to_next_refresh=user.twitter_oauth.seconds_to_next_refresh(),
        last_friend_refresh=user.twitter_oauth.last_friend_refresh,
    )


@blueprint.route('/<int:user_id>/<username>/claim', methods=['GET', 'POST'])
@login.login_required
def claim(user_id, username):
    user = login.current_user
    assert user_id == user.get_id()
    assert username == user.username

    form = ClaimForm()
    if form.validate_on_submit():
        user.claim_printer(
            form.claim_code.data,
            form.printer_name.data)
        return flask.redirect(flask.url_for('.landing'))

    return flask.render_template(
        'claim.html',
        form=form,
    )


@blueprint.route('/<int:user_id>/<username>/twitter-friend-refresh', methods=['POST'])
@login.login_required
def twitter_friend_refresh(user_id, username):
    user = login.current_user
    assert user_id == login.current_user.get_id()
    assert username == login.current_user.username

    assert user.twitter_oauth.seconds_to_next_refresh() == 0

    # TODO error handling when hitting twitter rate limit ...
    login.current_user.twitter_oauth.friends = twitter.get_friends(login.current_user)
    login.current_user.twitter_oauth.last_friend_refresh = datetime.datetime.utcnow()

    return flask.redirect(flask.url_for('.landing'))
