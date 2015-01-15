"""User models. Login only via twitter for now to avoid the whole
forgot-password/reset-password dance.
"""
import datetime

from sirius.coding import claiming

from sirius.models.db import db
from sirius.models import hardware

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # username can't be unique because we may have multiple identity
    # providers. For now we just copy the  twitter handle.
    username = db.Column(db.String)

    def __repr__(self):
        return 'User {}'.format(self.username)

    # Flask-login interface:
    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def claim_printer(self, claim_code, name):
        """Claiming can happen before the printer "calls home" for the first
        time so we need to be able to deal with that."""

        hardware_xor, _ = claiming.process_claim_code(claim_code)
        hcc = hardware.ClaimCode(
            by_id=self.id,
            hardware_xor=hardware_xor,
            claim_code=claim_code,
            name=name,
        )
        db.session.add(hcc)

        # Check whether we've seen this printer and if so: connect it
        # to claim code and make it "owned".
        printer_query = hardware.Printer.query.filter_by(
            hardware_xor=hardware_xor)
        printer = printer_query.first()
        if printer is None:
            return

        assert printer_query.count() == 1, \
            "hardware xor collision: {}".format(hardware_xor)

        printer.claim_code = claim_code
        printer.hardware_xor = hardware_xor
        printer.owner_id = hcc.by_id
        printer.name = name
        db.session.add(printer)
        return printer


class TwitterOAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    screen_name = db.Column(db.String, unique=True)
    token = db.Column(db.String, unique=True)

TwitterOAuth.user = db.relationship(
    User,
    primaryjoin=TwitterOAuth.user_id==User.id,
    backref=db.backref('twitteroauth', lazy='dynamic'),
)
