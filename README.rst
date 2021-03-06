Greenlandic Address Resolution Register
=======================================

Welcome to *gladdrreg*, a `Django`_ webapp implementing the Greenlandic
Address Resolution Register.

.. _`Django`: https://www.djangoproject.com

System Requirements
-------------------

* Python 3.5 or later
* python3-venv (Ubuntu only)

Quick Setup
-----------

The central entry point to this managing this application is the
``manage.py`` script, which both downloads and configures the
application environment, including its Python virtual environment, and
runs the application itself.

To build the application, run the following commands in a shell::

  $ python3 ./manage.py migrate
  $ python3 ./manage.py babelcompilemessages
  $ python3 ./manage.py collectstatic

You can now run the application, like so::

  $ python3 ./manage.py runserver

This will result in an application running without any data available,
or any users.
Please note that the default database engine is the somewhat slow
*SQLite*.

You can prime the database with a dump of addresses in Greenland::

  $ python3 ./manage.py import

Depending on your computer and database, this can take up to 30
minutes, although it shouldn't take more than five with a reasonably
fast setup.

To create an initial super-user, use::

  $ python3 ./manage.py createsuperuser

If you want to customise the setup, put your settings in a file called
``local_settings.py`` within the ``addrsite`` directory within this
source directory. For an example, see ``local_settings-example.py``
within the same location.

See the `Django reference documentation`_ for details on the available
settings.

.. _`Django reference documentation`:
   https://docs.djangoproject.com/en/1.10/ref/settings/

Gotchas
-------

Time zones
    The application uses UTC by default, but you can select another by
    adding the following to ``addrsite/local_settings.py``::

      TIME_ZONE = 'Amerika/Godthab'

    The value above is an example, and the time zone covering most
    areas of Greenland. `Other possible values`_ include
    ``Europe/Copenhagen`` or ``Etc/UTC`` — which is our default.

.. _`Other possible values`:
   https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

Localisation
    The UI is fully localised to English and Danish, and uses
    whichever language your browser requests. Your milage may vary
    with other languages; Django speaks many languages, but
    unfortunately Greenlandic is not among them. Patches welcome!

Access control
    Django operates with two levels of privilege relevant to this
    application: *staff* and *superuser* rights. Staff grants you
    access to the administrative interface, i.e. the application
    itself. Superusers may edit all objects; other users may only edit
    objects on certain municipalities, granted by “Municipality
    Rights” in the UI.

    Please note that users without staff rights cannot log in, and
    that users default to not having them.
