Migrations are meant for production systems. In order to start with a
clean migration layout run the following after a model change:

```sh
rm -f sirius/data.sqlite
-git rm -f migrations/versions/*py
rm -f migrations/versions/*pyc
rm -f migrations/versions/*py
./manage.py db revision --autogenerate -m "Sirius models."
./manage.py db upgrade
git add migrations/versions/*py
```
