from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

CSRF_COOKIE_SECURE = False  # Set to True if using HTTPS
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'  # This is the default header name for CSRF tokens


SECRET_KEY = 'django-insecure-nd(s+f(ycmop^8dj#ry#v=i_-gcl9eau_fj$l$-y7ms9c8drc$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*','b7a3-2409-40f3-1009-a49f-34a2-722a-5d9d-4f33.ngrok-free.app']


CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'https://b7a3-2409-40f3-1009-a49f-34a2-722a-5d9d-4f33.ngrok-free.app',
]

FILE_UPLOAD_MAX_MEMORY_SIZE = 10242880  # 5MB, for example



# settings.py

RAZORPAY_KEY_ID = 'rzp_test_Ey8ivDWGODPlAZ'
RAZORPAY_KEY_SECRET = 'ttmCr5Cy7mQYI2Eck7W6UD3u'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myadmin',
    'logistics',
    'business',
    'payment',
    'user',
    'django_crontab',
]

CRONJOBS = [
    ('*/5 9-11 * * *', 'django.core.management.call_command', ['generate_daily_orders']),
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'elaundry.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'elaundry.wsgi.application'



DATABASES = {
   'default': {
       'ENGINE': 'django.db.backends.sqlite3',
       'NAME': BASE_DIR / 'db.sqlite3',
   }
}


# DATABASES = {
#      'default': {
#          'ENGINE': 'django.db.backends.mysql',
#          'NAME': 'elaundrynew',
#          'USER': 'root',
#          'PASSWORD': '',
#          'HOST': 'localhost',
#          'PORT': '3307',
#      }
#  }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
USE_I18N = True
from django.utils import timezone


TIME_ZONE = "Asia/Kolkata"
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_ROOT = BASE_DIR / 'staticfiles'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



