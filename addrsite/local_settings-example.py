#
# Example settings overrides
#

# Ensure that we keep the secret key used in production secret!
# manage.py generates a secret key automatically

# SECRET_KEY = '...'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Where to push events
# PUSH_URL = 'http://localhost:8445/command/dump'


# Example PostgreSQL setup
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gladdrreg',
    },
}

#
# Set the time zone for the UI.
#
# The value below is an example, other possible values include
# 'Europe/Copenhagen'. We default to UTC.
#
TIME_ZONE = 'Amerika/Godthab'

# You can restrict the allowed host names to certain settings

# ALLOWED_HOSTS = 'gladdrreg.example.com'
