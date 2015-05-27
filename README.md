# Django Online Migration

The Django Online Migration project performs MySQL table migrations while your Django application is live without locking the table. It accomplishes this with a table copy and triggers similar to [github.com/soundcloud/lhm](https://github.com/soundcloud/lhm).

## Project Status

This project is currently in Beta mode and is currently being tested in production environments.

## Requirements

Django Online Migration only works with MySQL and currently requires a Django database connection.

## Limitations

The Django Online Migration tool works best with auto increment id primary keys. If your primary key is not sorted by insertion order and your application is deleting records your database might end up in an inconsistent state.

## TODO

* Add a trigger to prevent deletes when the user isn't using auto incrementing primary keys
  * http://stackoverflow.com/questions/14319950/trigger-to-prevent-delete-on-table
* Add a simple interface similar to Django migrations that allows developers to add/rename/drop columns and add indexes.
  * Parse the current result from `SHOW CREATE TABLE`
  * Track all add/rename/drop calls
  * Build the change_table inputs
* Generate the migration automagically.

## Usage

Django Online Migration adds an `online_migration` management command to Django that can be used to apply individual migrations. The migrations live in the project's `online_migrations` directory and look similar to the following example (please be patient while we simplify the interface):

```py
from facebook_analytics_service.utils.migrations import (
    change_table,
    finish_migration,
    restart_copy,
)


# This is only here to show the original table, it is not used
# during the migration
ORIGIN_TABLE_SQL = (
    """
    CREATE TABLE `campaign` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `name` varchar(255) NOT NULL,
        `objective` varchar(255) NOT NULL,
        `description` varchar(255) NOT NULL,
        `budget` numeric(12, 2) NOT NULL,
        `goal_value` numeric(12, 2),
        `post_id` varchar(128),
        `start_date` datetime,
        `end_date` datetime
    )
    """
)


DEST_TABLE_SQL = (
    """
    CREATE TABLE `campaign` (
        `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
        `display_name` varchar(255) NOT NULL,
        `objective` varchar(255) NOT NULL,
        `budget` numeric(12, 2) NOT NULL,
        `goal_spend` numeric(12, 2),
        `post_id` varchar(128),
        `start_date` datetime,
        `end_date` datetime,
        `created_time` datetime,
        `like_count` int
    )
    """
)


DEST_INDEXES = [
    "CREATE INDEX `campaign_87a49a9a` ON `campaign` (`post_id`)",
    "CREATE INDEX `campaign_87a49a9z` ON `campaign` (`objective`, `start_date`)",
]


ORIGIN_COLUMNS = [
    "id",
    "name",
    "objective",
    "description",
    "budget",
    "goal_value",
    "post_id",
    "start_date",
    "end_date",
]


DEST_COLUMNS = [
    "id",
    "display_name",
    "objective",
    "budget",
    "goal_spend",
    "post_id",
    "start_date",
    "end_date",
    "created_time",
    "like_count",
]

RENAMES = {
    "name": "display_name",
    "goal_value": "goal_spend",
}

def run(**kwargs):
    "run the migration"
    kwargs['renames'] = RENAMES
    change_table("default", "campaign", DEST_TABLE_SQL, DEST_INDEXES, ORIGIN_COLUMNS, DEST_COLUMNS, **kwargs)


def restart(**kwargs):
    "restart the copy"
    kwargs['renames'] = RENAMES
    restart_copy("default", "campaign", ORIGIN_COLUMNS, DEST_COLUMNS, **kwargs)


def rename(**kwargs):
    "rename the migration"
    # pylint: disable=W0613
    finish_migration("default", "campaign")
```

