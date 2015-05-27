"""
A management command for online migrations
"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError


HELP_STR = (
    """
    Usage:
        ./manage.py online_migration <app_name> <command> <migration_name>

    Commands:
        run       Create the migration table and copy the data.
        restart   Restart the copy from the original table to the migration table
        rename    Replace the old table with the migration table and archive the old table.
    """
)

# pylint: disable=print-statement


class Command(BaseCommand):
    """
    A command for building fixtures
    """

    option_list = BaseCommand.option_list + (
        make_option("--start", action="store", type="int", dest="start", help="The start id for copying to the migration table"),
        make_option("--limit", action="store", type="int", dest="limit", help="The limit id for copying to the migration table"),
        make_option("--chunk_size", action="store", type="int", dest="chunk_size", help="The number of rows to copy for each chunk"),
    )

    def handle(self, *args, **options):
        if len(args) != 3:
            print HELP_STR
            return
        to_run = __import__("%s.online_migrations.%s" % (args[0], args[2]), fromlist=[""])
        getattr(to_run, args[1])(**options)
