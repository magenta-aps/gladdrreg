Greenlandic Address Resolution Register
=======================================

Welcome to *gladdrreg*, a `Django`_ webapp implementing the Greenlandic
Address Resolution Register.

.. _`Django`: https://www.djangoproject.com

System Requirements
-------------------

* Python 3.5 or later

Quick Setup
-----------

The central entry point to this managing this application is the
``manage.py`` script, which both downloads and configures the
application environment, and runs the application itself.

To build the application, run the following commands in a shell::

  $ python3 ./manage.py migrate
  $ python3 ./manage.py babelcompilemessages
  $ python3 ./manage.py collectstatic

You can now run the application, like so::

  $ python3 ./manage.py runserver

This will result in an application running without any data available.
Please note that the databases is *SQLite* by default, which is rather
slow.

You can prime the database with a dump of addresses in Greenland::

  $ python3 ./manage.py import

Depending on your computer and database, this can take up to 30
minutes, although it shouldn't take more than five with in a reasonably
fast setup.

If you want to customise the setup, put your settings in a file called
``local_settings.py`` within the ``addrsite`` directory within this
source directory. For an example, see ``local_settings-example.py``
within the same location.

See the `Django reference documentation`_ for details on the available
settings.

.. _`Django reference documentation`:
   https://docs.djangoproject.com/en/1.10/ref/settings/
