from sirius.models.db import db
from sirius.models import user


class Bridge(db.Model):
    """Bridges are not really interesting for users other than that they
    are connected so we don't store ownership for them.
    """
    __tablename__ = 'bridge'
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    bridge_address = db.Column(db.String, primary_key=True)


class Printer(db.Model):
    """On reset printers generate a new, unique device address, so every
    reset will result in a new Printer row.

    Note that this model is only ever created by a printer calling
    home. Users create a ClaimCode row.
    """
    __tablename__ = 'printer'
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    device_address = db.Column(db.String)
    hardware_xor = db.Column(db.String)

    # Update the following fields after we connected (i.e. joined over
    # hardware xor) a claim to a printer. The fields start out as
    # NULL.
    owner = db.Column(db.Integer, db.ForeignKey(user.User.id), nullable=True)
    used_claim_code = db.Column(db.String, nullable=True)


class ClaimCode(db.Model):
    """Printer and claim codes are joined over the hardware xor. There are
    several possible orders of creating the DB entries (dependent on
    whether the user claims a device before it calls home or the other
    way round).

    a.
      1. printer calls home with xor A
      2. claim code created with xor A code B
    b.
      1. claim code created with xor A code B
      2. printer calls home with xor A
    c.
      1. claim code created with xor A code B
      2. claim code created with xor A code C
      3. printer calls home with xor A

    The join is "loose" i.e. in general the order doesn't matter
    unless a printer is claimed twice. In That case the newest claim
    code has to be used (case c).

    Note also that claim codes are meant to be temporary. I.e. once a
    printer has been claimed the claim code becomes irrelevant and
    only the printer ownership counts. We don't enforce a valid time
    window for claim codes though.
    """
    id = db.Column(db.Integer, primary_key=True)
    __tablename__ = 'claim_code'
    created = db.Column(db.DateTime)
    by = db.Column(db.ForeignKey(user.User.id))
    hardware_xor = db.Column(db.String)
    claim_code = db.Column(db.String)


class DeviceLog(db.Model):
    """The device log Recorde state changes in the bridge and connected
    devices. We may selectively expose some of these to the user.
    """
    __tablename__ = 'device_log'
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    device_address = db.Column(db.String)

    # json dict of events dispatched on VALID_STATES. E.g.
    # {"type": "grant_access", "payload": {...}}
    entry = db.Column(db.String)

    VALID_STATES = [
        'power_on',
        'connect',
        'disconnect',
        'claim',
        'print',
        'grant_access',
        'revoke_access',
    ]

    # Expose an explicit API to force people to provide the correct
    # arguments.
    @classmethod
    def log_power_on(cls, bridge_address):
        pass

    @classmethod
    def log_connect(cls, device_address):
        pass

    @classmethod
    def log_disconnect(cls, device_address):
        pass

    # TODO log all the things
