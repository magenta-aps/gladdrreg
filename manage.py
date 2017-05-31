#!/usr/bin/env python
'''Django script invocation

Customised to create and configure a virtual environment.

'''

from __future__ import print_function, absolute_import

import base64
import os
import platform
import subprocess
import sys

REQUIRED_PYTHON = (3, 5)
CURRENT_PYTHON = sys.version_info[:2]

if __name__ == "__main__":
    basedir = os.path.abspath(os.path.dirname(__file__))

    # allow testing on different platforms and VMs
    venvdir = os.path.join(basedir, "venv-{}-{}-{}.{}".format(
        platform.system(), platform.python_implementation(),
        *platform.python_version_tuple()[:2]
    ).lower())

    # commonpath() is Python 3.5+, so first, check for the platform
    is_in_venv = (
        REQUIRED_PYTHON <= CURRENT_PYTHON and
        (os.path.splitdrive(sys.executable)[0] ==
         os.path.splitdrive(basedir)[0]) and
        os.path.commonpath([sys.executable, basedir]) == basedir
    )

    exec_name = os.path.basename(sys.executable)
    venv_executable = (os.path.join(venvdir, 'bin', exec_name)
                       if platform.system() != 'Windows'
                       else os.path.join(venvdir, 'Scripts', exec_name))

    # create the virtual env, if necessary
    if not is_in_venv:
        if (CURRENT_PYTHON[0] != REQUIRED_PYTHON[0] or
                CURRENT_PYTHON[1] < REQUIRED_PYTHON[1]):
            if platform.system() == 'Windows':
                raise Exception('This script requires Python %d.%d or later' %
                                REQUIRED_PYTHON)
            exe = 'python%d.%d' % REQUIRED_PYTHON

            os.execlp(exe, exe, *sys.argv)

        if not os.path.isfile(venv_executable):
                import venv

                try:
                    venv.main(['--upgrade', venvdir])
                except SystemExit:
                    # handle Ubuntu's horrible hackery where you get a
                    # venv without pip...
                    import shutil
                    shutil.rmtree(venvdir)
                    raise

        subprocess.check_call([
            venv_executable, '-m', 'pip', 'install', '-qe', basedir
        ])

        if platform.system() == 'Windows':
            # os.execlp doesn't actually replace the current process
            # on Windows
            with subprocess.Popen([venv_executable] + sys.argv) as proc:
                try:
                    proc.wait()
                except KeyboardInterrupt:
                    proc.terminate()

                sys.exit(proc.returncode)
        else:
            os.execlp(venv_executable, venv_executable, *sys.argv)

    # create a secret key, so that we can guarantee its presence
    # whilst keeping it out of version control
    key_file = os.path.join(basedir, '.secret-key')
    if not os.path.isfile(key_file):
        with open(key_file, 'wt') as fp:
            k = os.urandom(64)
            fp.write(base64.urlsafe_b64encode(k).rstrip(b"=").decode('ascii'))
            fp.write('\n')

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "addrsite.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
