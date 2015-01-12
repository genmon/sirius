from flask.ext import testing


from sirius.models import user
from sirius.models import hardware
from sirius.models.db import db
from sirius.web import webapp

class TestClaiming(testing.TestCase):

    def create_app(self):
        app = webapp.create_app('test')
        return app

    def setUp(self):
        testing.TestCase.setUp(self)
        db.create_all()
        self.testuser = user.User(username="testuser")
        db.session.add(self.testuser)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_claim_first(self):
        self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4')
        hardware.Printer.phone_home('000d6f000273ce0b')
        db.session.commit()
        printer = hardware.Printer.query.first()

        self.assertEqual(printer.owner, self.testuser)

    def test_printer_phone_home_first(self):
        hardware.Printer.phone_home('000d6f000273ce0b')
        self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4')
        db.session.commit()
        printer = hardware.Printer.query.first()

        self.assertEqual(printer.owner, self.testuser)
