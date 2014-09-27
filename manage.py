#!/usr/bin/env python2.7

import os

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from app import create_app, db
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db)
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
