# Emulation

The project comes with a very simple emulator layer. As a first step
we have to create a fake printer:

```console
$ ./manage.py fake printer
Importing environment from .env...
--------------------------------------------------------------------------------
DEBUG in webapp [/home/tom/devel/wizards/sirius/sirius/web/webapp.py:65]:
Creating app.
--------------------------------------------------------------------------------
DEBUG:sirius.web.webapp:Creating app.
     address: cc18aff27ed5cf3d
       DB id: 15
      secret: 6b79e72280
         xor: 15444370
  claim code: ebqp-pyg7-4b0f-qbdk

Created printer and saved as cc18aff27ed5cf3d.printer
```

This command wrote the file `cc18aff27ed5cf3d.printer`.

## Running a fake printer

I refer to the [README](README.md) file for running the main server
and assume it is running at `127.0.0.1:5000`.

You can run:

```console
$ ./manage.py emulate printer cc18aff27ed5cf3d.printer ws://127.0.0.1:5000/api/v1/connection
[...]
Asked for encryption key
Received encryption key, switching to heartbeat mode.
Heartbeat. Pom pom.
Heartbeat. Pom pom.
```
