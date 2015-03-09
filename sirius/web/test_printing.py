import flask

from sirius.models import hardware
from sirius.models.db import db
from sirius.testing import base


# pylint: disable=no-member
class TestPrinting(base.Base):

    def setUp(self):
        base.Base.setUp(self)
        self.autologin()
        hardware.Printer.phone_home('000d6f000273ce0b')
        self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4', 'my test printer')
        db.session.commit()
        self.printer = hardware.Printer.query.first()

    def get_print_url(self):
        return flask.url_for(
            'printer_print.printer_print',
            user_id=self.testuser.id,
            username=self.testuser.username,
            printer_id=self.printer.id,
        )

    def test_print_ok(self):
        r = self.client.post(self.get_print_url(), data=dict(
            target_printer=self.printer.id, message='hello'))
        print r.headers
        self.assertRedirects(r, '/printer/1')

    def test_print_wrong_printer(self):
        r = self.client.post(self.get_print_url(), data=dict(
            target_printer='10', message='hello2'))
        self.assertIn('Not a valid choice', r.data)
        self.assert200(r)
