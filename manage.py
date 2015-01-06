#!/usr/bin/env python2.7

import os

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        name, value = line.strip().split('=', 1)
        os.environ[name] = value

from sirius.web import webapp
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = webapp.create_app(os.getenv('FLASK_CONFIG', 'default'))
manager = Manager(app)
migrate = Migrate(app, webapp.db)

def make_shell_context():
    return dict(app=app, db=webapp.db)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def deploy():
	"""Run deployment tasks."""
	from flask.ext.migrate import upgrade

	# migrate database to latest revision
	upgrade()


if __name__ == '__main__':
    manager.run()

# run with
#gunicorn -b 0.0.0.0:5000 -k flask_sockets.worker manage:app
