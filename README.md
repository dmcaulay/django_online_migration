# Django Online Migration

The Django Online Migration project performs MySQL table migrations while your Django application is live without locking the table. It accomplishes this with a table copy and triggers similar to [github.com/soundcloud/lhm](https://github.com/soundcloud/lhm).

## Project Status

This project is currently in Beta mode and is currently being tested in production environments.

## Requirements

Django Online Migration only works with MySQL and currently requires a Django database connection.

## Limitations

The Django Online Migration tool works best with an auto incremented primary key. If your primary key not auto incremented and not sorted by insertion order your database might end up in an inconsistent state.

## Usage

Django Online Migration adds an `online_migration` management command to Django that can be used to apply individual migrations. The migrations live in the project's `online_migrations` directory and look similar to the following example:

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

The migration above implements three different functions: `run`, `restart` and `rename`. These functions map to the three possible commands executed by the django management command.

### run

The `run` command is used to start the migration. It executes the following steps:
* Creates the destination table use `DEST_TABLE_SQL`
* Creates the indexes using `DEST_INDEXES`
* Creates  insert, update and delete triggers to keep the tables in sync during the copy
* Starts the copy from the original table to the destination table
  * `ORIGIN_COLUMNS`, `DEST_COLUMNS` and `RENAMES` are used to map original columns to new columns during the copy.

To exeucte the run command for migration `0001_campaign` you run the following:

```
$ ./manage.py online_migration <app_name> run 0001_campaign
```

### restart

The `restart` command is used to restart the copy if anything goes wrong during the `run` command. The `restart` command allows you to pass in a start id and a limit id so you can start where you left off. You can find these ids by reviewing the logs of the failed copy. 

To exeucte the restart command for migration `0001_campaign` you run the following:

```
$ ./manage.py online_migration <app_name> restart 0001_campaign --start=1000 --limit=20000
```

### rename

Once the copy completes the migration is finished with an atomic rename. This is accomplished with the `rename` command it should be done in place of the standard Django migration.

To exeucte the rename command for migration `0001_campaign` you run the following:

```
$ ./manage.py online_migration <app_name> rename 0001_campaign
```

## Notes

The first iteration of this tool has a somewhat crude interface that will be cleaned up in future releases. It was originally inspired by (github.com/soundcloud/lhm)[https://github.com/soundcloud/lhm] and plans to work seamlessly with Django migrations similar to the way lhm works with ActiveRecord and Rails migrations.

## TODO

* Add a trigger to prevent deletes when the user isn't using auto incrementing primary keys
  * http://stackoverflow.com/questions/14319950/trigger-to-prevent-delete-on-table
* Add a simple interface similar to Django migrations that allows developers to add/rename/drop columns and add indexes.
  * Parse the current result from `SHOW CREATE TABLE`
  * Track all add/rename/drop calls
  * Build the change_table inputs
* Generate the migration automagically.

