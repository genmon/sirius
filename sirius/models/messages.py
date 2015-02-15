import base64
import datetime
import logging
from sqlalchemy import desc

from sirius.models.db import db


logger = logging.getLogger(__name__)


TIMEOUT_SECONDS = 60

class Message(db.Model):
    """Messages are printed by someone on ("sender") to a "target
    printer".
    """
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    pixels = db.Column(db.LargeBinary)

    print_id = db.Column(db.Integer, unique=True)

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User', backref=db.backref('messages', lazy='dynamic'))

    target_printer_id = db.Column(db.Integer, db.ForeignKey('printer.id'))
    target_printer = db.relationship('Printer', backref=db.backref('messages', lazy='dynamic'))

    # The response is received by the protocol_loop. It's also
    # possible to not receive a response (e.g. printer got
    # disconnected) in which case we "time out" after TIMEOUT_SECONDS.
    response_timestamp = db.Column(db.DateTime, nullable=True)
    failure_message = db.Column(db.String, nullable=True)


    @classmethod
    def timeout_updates(cls, utcnow=None):
        """Update all messages that are timed-out with an error message. This
        is a destructive update. It should also be fairly cheap
        because of the index on created.

        We're doing these updates "eagerly" on every printer overview
        page load instead of through a cron job, but there's no reason
        why we couldn't do that.
        """

        if utcnow is None:
            utcnow = datetime.datetime.utcnow()
        cutoff = utcnow - datetime.timedelta(seconds=TIMEOUT_SECONDS)

        cls.query.filter(
            cls.created <= cutoff,
            cls.response_timestamp == None
        ).update(dict(
            response_timestamp=utcnow,
            failure_message="Timed out",
        ))
        db.session.commit()


    def base64_pixels(self):
        return base64.b64encode(self.pixels)


    @classmethod
    def ack(cls, return_code, command_id, utcnow=None):
        if return_code != 0:
            # TODO map codes to error messages
            failure_message = 'Problem printing: {}'.format(return_code)
        else:
            failure_message = None

        if utcnow is None:
            utcnow = datetime.datetime.utcnow()

        message = cls.query.filter_by(print_id=command_id).first()

        if message is None:
            logger.error("Ack'ed unknown message %s.", command_id)
            return

        message.response_timestamp = utcnow
        message.failure_message = failure_message

        db.session.add(message)
        db.session.commit()

    @classmethod
    def get_next_command_id(cls):
        """Return the next command id to be used by the bridge. Command ids
        are used to ack messages so we need to make sure we don't have
        any collisions. The best way to do so is to pick the
        next-highest number after the ones we already used up.
        """
        last = cls.query.order_by(desc('print_id')).first()
        if last is None:
            next_print_id = 1
        else:
            next_print_id = last.print_id + 1

        db.session.commit()
        return next_print_id
