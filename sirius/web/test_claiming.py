import flask
from flask.ext import testing
from flask.ext import login

from sirius.models import user
from sirius.models import hardware
from sirius.models.db import db
from sirius.web import webapp


class Base(testing.TestCase):

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

    def autologin(self):
        # Most disgusting hack but I see no other way to log in users:
        # Flask session doesn't pick up the cookies if I call just
        # login_user. The login_user call needs to be embedded in a
        # request.
        @self.app.route('/autologin')
        def autologin():
            login.login_user(self.testuser)
            return ''

        self.client.get('/autologin')


class TestClaiming(Base):

    def test_claim_first(self):
        self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4', 'my test printer')
        hardware.Printer.phone_home('000d6f000273ce0b')
        db.session.commit()
        printer = hardware.Printer.query.first()

        self.assertEqual(printer.owner, self.testuser)

    def test_printer_phone_home_first(self):
        hardware.Printer.phone_home('000d6f000273ce0b')
        self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4', 'my test printer')
        db.session.commit()
        printer = hardware.Printer.query.first()

        self.assertEqual(printer.owner, self.testuser)


class TestClaimingWeb(Base):

    def get_claim_url(self):
        return flask.url_for(
            'landing.claim',
            user_id=self.testuser.id,
            username=self.testuser.username)

    def test_invalid_claim_code(self):
        self.autologin()
        r = self.client.post(self.get_claim_url(), data=dict(
            claim_code='invalid', printer_name='lp'))
        # invalid keeps us on claiming page and doesn't redirect
        self.assert200(r)

    def test_valid_claim_code(self):
        self.autologin()
        r = self.client.post(self.get_claim_url(), data=dict(
            claim_code='n5ry-p6x6-kth7-7hc4', printer_name='lp'))

        # valid code: redirect to overview.
        self.assertRedirects(r, '/')
