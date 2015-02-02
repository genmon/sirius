from flask.ext import testing
from flask.ext import login

from sirius.models.db import db
from sirius.web import webapp
from sirius.web import twitter


# Mock network-accessing function:
twitter.get_friends = lambda x: []


# pylint: disable=no-member
class TestOAuthFlow(testing.TestCase):
    def setUp(self):
        testing.TestCase.setUp(self)
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_app(self):
        app = webapp.create_app('test')
        return app

    def test_oauth_authorized(self):
        self.assertEqual(login.current_user.is_authenticated(), False)
        twitter.process_authorization(
            'token',
            'secret_token',
            'test_screen_name',
            '/next_url',
        )
        self.assertEqual(login.current_user.username, 'test_screen_name')
        self.assertEqual(login.current_user.is_authenticated(), True)
