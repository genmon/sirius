import flask

from flask.ext import login

blueprint = flask.Blueprint('landing', __name__)


@blueprint.route('/')
def landing():
    if not login.current_user.is_authenticated():
        return flask.render_template('landing.html')

    return overview()


@login.login_required
def overview():
    my_printers = login.current_user.printers.all()

    return flask.render_template(
        'overview.html',
        my_printers=my_printers,
    )


@blueprint.route('/<int:user_id>/<username>/claim')
@login.login_required
def claim(user_id, username):
    assert user_id == login.current_user.id
    assert username == login.current_user.username

    return flask.render_template(
        'claim.html',
    )
