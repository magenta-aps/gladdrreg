#
# Example settings overrides
#

SECRET_KEY = '...'

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gladdrreg',
    },
}

ALLOWED_HOSTS = 'gladdrreg.example.com'
