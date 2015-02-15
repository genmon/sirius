import flask

from sirius.models import user
from sirius.models import hardware
from sirius.models.db import db
from sirius.testing import base


# pylint: disable=no-member
class TestClaiming(base.Base):

    def setUp(self):
        base.Base.setUp(self)
        self.testuser2 = user.User(username="testuser 2")
        db.session.add(self.testuser2)
        db.session.commit()

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

    def test_two_claims_different_users(self):
        "We expect this to fail because printers can't change users without reset."
        self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4', 'my test printer')
        with self.assertRaises(user.ClaimCodeInUse):
            # printer can't change user without reset
            self.testuser2.claim_printer('n5ry-p6x6-kth7-7hc4', 'my test printer 2')

    def test_two_claims_different_users_same_xor_different_code(self):
        "printer changes user after reset."
        self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4', 'my test printer')
        self.testuser2.claim_printer('0cx6-nk3t-49zq-7hc4', 'my test printer 2')

        hardware.Printer.phone_home('000d6f000273ce0b')
        db.session.commit()
        printer = hardware.Printer.query.filter_by(owner=self.testuser2)

        # One printer in system owner by testuser2
        self.assertIsNot(printer, None)

    def test_user_tries_to_reclaim_with_old_code(self):
        """What happens if we enter the same code twice and it'd change owners."""
        self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4', 'my test printer')
        self.testuser2.claim_printer('0cx6-nk3t-49zq-7hc4', 'my test printer 2')
        hardware.Printer.phone_home('000d6f000273ce0b')
        db.session.commit()

        # try to re-claim printer.
        with self.assertRaises(user.CannotChangeOwner):
            self.testuser.claim_printer('n5ry-p6x6-kth7-7hc4', 'my test printer')
            db.session.commit()

        printer = hardware.Printer.query.filter_by(owner=self.testuser2)
        # printer must still belong to user 2
        self.assertIsNot(printer, None)


class TestClaimingWeb(base.Base):

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
