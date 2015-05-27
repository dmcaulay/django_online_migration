"""A test runner that allows us to run tests on an empty DB"""

from django.test.runner import DiscoverRunner as BaseRunner


class EmptyDatabaseMixin(object):
    """
    Test runner mixin that only initializes the default database
    """

    def setup_databases(self, *args, **kwargs):
        """
        Override the default behavior. This assumes that your
        test database already exists and your tests cleanup
        after themselves.
        """
        pass

    def teardown_databases(self, old_config, **kwargs):
        """
        Do nothing here. See the comment above.
        """
        pass


class EmptyDatabaseRunner(EmptyDatabaseMixin, BaseRunner):
    """Actual test runner sub-class to make use of the mixin."""
