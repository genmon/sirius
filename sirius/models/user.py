"""User models. Login only via twitter for now to avoid the whole
forgot-password/reset-password dance.
"""
import collections
import datetime

from sirius.coding import claiming

from sirius.models.db import db
from sirius.models import hardware


class CannotChangeOwner(Exception): pass
class ClaimCodeInUse(Exception): pass


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # username can't be unique because we may have multiple identity
    # providers. For now we just copy the  twitter handle.
    username = db.Column(db.String)
    twitter_oauth = db.relationship(
        'TwitterOAuth', uselist=False, backref=db.backref('user'))

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

        # TODO(tom): This method probably belongs to printer, not
        # user. Move at some point.

        claim_code = claiming.canonicalize(claim_code)

        hcc = hardware.ClaimCode.query.filter_by(claim_code=claim_code).first()
        hardware_xor, _ = claiming.process_claim_code(claim_code)

        if hcc is not None and hcc.by != self:
            raise ClaimCodeInUse(
                "Claim code {} already claimed by {}".format(
                    claim_code, hcc.by))

        if hcc is None:
            hcc = hardware.ClaimCode(
                by_id=self.id,
                hardware_xor=hardware_xor,
                claim_code=claim_code,
                name=name,
            )
            db.session.add(hcc)
        else:
            # we already have a claim code, don't do anything.
            pass

        # Check whether we've seen this printer and if so: connect it
        # to claim code and make it "owned" but *only* if it does not
        # have an owner yet.
        printer_query = hardware.Printer.query.filter_by(
            hardware_xor=hardware_xor)
        printer = printer_query.first()
        if printer is None:
            return

        if printer.owner is not None and printer.owner != self:
            raise CannotChangeOwner(
                "Printer {} already owned by {}. Cannot claim for {}.".format(
                    printer, printer.owner, self))

        assert printer_query.count() == 1, \
            "hardware xor collision: {}".format(hardware_xor)

        printer.used_claim_code = claim_code
        printer.hardware_xor = hardware_xor
        printer.owner_id = hcc.by_id
        printer.name = name
        db.session.add(printer)
        return printer

    def signed_up_friends(self):
        """
        A "friend" is someone this user follows on twitter.

        :returns: 2-tuple of (all friends, list of people who can print on
                  this user's printer)
        """
        friends = self.twitter_oauth.friends
        if not friends:
            return [], []
        return friends, User.query.filter(
            User.username.in_(x.screen_name for x in friends))

    def friends_printers(self):
        """
        :returns: List of printers this user can print on.
        """
        # TODO(tom): Querying the full database is O(N) and will not
        # scale. Replace the model with a N:M relationship.
        sn = self.twitter_oauth.screen_name
        reverse_friend_ids = [
            x.user_id for x in TwitterOAuth.query.all()
            for y in (x.friends or [])
            if sn == y.screen_name]

        # Avoid expensive sql by checking for list.
        if not reverse_friend_ids:
            return []

        return hardware.Printer.query.filter(
            hardware.Printer.owner_id.in_(reverse_friend_ids))


Friend = collections.namedtuple('Friend', 'screen_name name profile_image_url')

class TwitterOAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    screen_name = db.Column(db.String, unique=True)

    token = db.Column(db.String)
    token_secret = db.Column(db.String)

    # Twitter comes with a 15 requests / 15 minutes rate. To avoid
    # people DOS'ing our service we allow only one refresh per hour.
    last_friend_refresh = db.Column(db.DateTime)

    # List of Friend objects (see named tuple above this class)
    friends = db.Column(db.PickleType())

    def seconds_to_next_refresh(self, utcnow=None):
        if utcnow is None:
            utcnow = datetime.datetime.utcnow()

        if self.last_friend_refresh is None:
            return 0

        seconds_since_refresh = (
            utcnow - self.last_friend_refresh
        ).total_seconds() - 3600

        return abs(min(seconds_since_refresh, 0))
