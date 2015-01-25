# Dokku setup

We set up a Digital Ocean instance with Ubuntu 14.04 and dokku
0.2.3. Note that a 512M memory instance works but you'll have to
restart docker a lot because it doesn't free memory very often.

Let's assume the Digital Ocean instance's IP is `104.236.81.129`:

```
export DO=104.236.81.129
ssh root@${DO} dokku version
v0.2.3
```

One needs to run `dokku plugins-install` at least once before the
system works.

Note that this triggers apt which wants to overwrite your `nginx.conf`
file which you don't want. If apt seems stuck then CTRL-C the
`plugins-install`, run `dpkg --configure -a` and then `dokku
plugins-install` again.

We won't be able to run on sqlite in a docker container so we'll use
postgres via
[this dokku plugin](https://github.com/ohardy/dokku-psql psql).

```
ssh root@${DO}
cd /var/lib/dokku/plugins
https://github.com/ohardy/dokku-psql psql
dokku plugins-install
```

Now create the postgres database

```
dokku psql:start
dokku psql:create sirius
```


# Push your sirius app

We set our Digital Ocean instance as the remote with the dokku user as
our account:

```
git remote add dokku dokku@${DO}:sirius
git push --set-upstream dokku master
```

After deploying you'll need to pick the right database by setting the
FLASK_CONFIG, then migrate the database:

```
ssh root@${DO} dokku config:set sirius FLASK_CONFIG=heroku
ssh root@${DO} dokku run sirius python ./manage.py db upgrade
```


# Swap

One way around the memory pressure is to add swap. On the server run:

```
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```
