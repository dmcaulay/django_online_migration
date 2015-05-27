"Settings used for unit tests"

SECRET_KEY = 'fcf9acf96e3720c27587a7889befd5f99add2937e818fcec9f15447d5c5ef376'

TEST_RUNNER = 'django_online_migration.tests.runner.EmptyDatabaseRunner'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test',
        'HOST': '/opt/boxen/data/mysql/socket',
        'PORT': '13306',
        'USER': 'root',
        'PASSWORD': ''
    },
}
