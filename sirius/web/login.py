from flask.ext import login

from sirius.models import user

manager = login.LoginManager()


@manager.user_loader
def load_user(user_id):
    return user.User.query.get(user_id)
