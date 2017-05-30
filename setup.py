import codecs
import os
import platform
import sys

import setuptools

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

requires = [
        "django>=1.10, <1.11",
        "django-enumfields>=0.9.0",
        "django_extensions>=1.7.8",
        "django-modeladmin-reorder>=0.2",
        "openpyxl>=2.4",
        "eventlet>=0.21",
        "babel>=2.4.0",
        "progress>=1.3",
]

if sys.platform != 'win32':
    requires += [
        "psycopg2>=2.7"
        if platform.python_implementation() != 'PyPy'
        else "psycopg2cffi>=2.7"
    ]
else:
    requires += [
        'django-mssql>=1.8',
        "pypiwin32",
        'django-windows-tools',
    ]

setuptools.setup(
    name='gladdrreg',
    version='0.0.1',

    description='Address Resolution Register of Greenland',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/magenta-aps/gladdrreg',

    # Author details
    author='Magenta ApS',
    author_email='info@magenta.dk',
    license='MPL2',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='django greenland dafo',
    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests']),

    install_requires=requires,
    extras_require={
        # 'dev': ['check-manifest'],
        'test': [
            'pycodestyle>=1.7',
            'freezegun>=0.3.8',
            'pytz>=2016.10',
        ],
    },
)
