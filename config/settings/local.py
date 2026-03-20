from .base import * 
DEBUG = True 

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# 1. Add Silk to installed apps
INSTALLED_APPS += ["silk"]

# 2. Insert Silk Middleware at the very beginning of the list
# This ensures it tracks the full duration of the request
MIDDLEWARE.insert(0,'silk.middleware.SilkyMiddleware')


# 3. Optional Silk configurations
SILKY_PYTHON_PROFILER = True
SILKY_INTERCEPT_PERCENT = 100



