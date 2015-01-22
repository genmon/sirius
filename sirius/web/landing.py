import flask
import flask_wtf
import wtforms
from flask.ext import login

from sirius.coding import claiming

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


@blueprint.route('/<int:user_id>/<username>/claim', methods=['GET', 'POST'])
@login.login_required
def claim(user_id, username):
    assert user_id == login.current_user.get_id()
    assert username == login.current_user.username

    form = ClaimForm()
    if form.validate_on_submit():
        login.current_user.claim_printer(
            form.claim_code.data,
            form.printer_name.data)
        return flask.redirect(flask.url_for('.landing'))

    return flask.render_template(
        'claim.html',
        form=form,
    )
