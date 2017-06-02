#
# Example settings overrides
#

# Ensure that we keep the secret key used in production secret!
# manage.py generates a secret key automatically
#SECRET_KEY = '...'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Example PostgreSQL setup
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gladdrreg',
    },
}

# You can restrict the allowed host names to certain settings
#ALLOWED_HOSTS = 'gladdrreg.example.com'
