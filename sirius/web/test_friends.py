from sirius.models.db import db
from sirius.models import user
from sirius.models import hardware
from sirius.testing import base


# pylint: disable=no-member
class TestFriends(base.Base):

    def setUp(self):
        base.Base.setUp(self)
        db.create_all()
        u0 = user.User(username='u0')
        u1 = user.User(username='u1')
        oa0 = user.TwitterOAuth(
            user=u0,
            screen_name='twitter0',
            token='token',
            token_secret='token_secret',
            friends=[user.Friend('twitter1', 't1', ''), user.Friend('twitter2', 't2', '')],
        )
        oa1 = user.TwitterOAuth(
            user=u1,
            screen_name='twitter1',
            token='token',
            token_secret='token_secret',
            friends=[user.Friend('twitter2', 't2', '')],
        )
        db.session.add_all([u0, u1, oa0, oa1])
        db.session.commit()
        self.u0 = u0
        self.u1 = u1

        # Register a printer for user so we can test friends printers
        u0.claim_printer('vcty-8s95-40hq-6k1z', 'u0 printer')
        hardware.Printer.phone_home('dd5ebbcce362f584')

        u1.claim_printer('pmo0-bjf1-ste8-51c1', 'u1 printer')
        hardware.Printer.phone_home('35fef3793dce4692')


    def tearDown(self):
        db.session.remove()
        db.drop_all()


    def test_signed_up_friends(self):
        f0, _ = self.u0.signed_up_friends()
        f1, _ = self.u1.signed_up_friends()

        self.assertItemsEqual(f0, [
            user.Friend('twitter1', 't1', ''),
            user.Friend('twitter2', 't2', '')])

        self.assertItemsEqual(f1, [
            user.Friend('twitter2', 't2', '')])


    def test_friends_printers(self):
        fp0 = list(self.u0.friends_printers())
        fp1 = list(self.u1.friends_printers())
        # u0 follows u1 but the reverse is not true.  That means u1
        # should be able to print on u0's printer but u0 should not be
        # able to print on u1's printer
        self.assertEqual(len(fp0), 0)
        self.assertEqual(len(fp1), 1)

        self.assertEqual(fp1[0].name, 'u0 printer')
