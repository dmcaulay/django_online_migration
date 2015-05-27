"Test migrations"
import datetime
from decimal import Decimal

from django.db import connections
from django.test import TestCase

from django_online_migration.migrate import (
    Intersection,
    archive_name,
    dest_name,
    finish_migration,
    change_table,
    copy_in_chunks,
    create_dest,
    create_indexes,
    create_triggers,
    delete_triggers,
    execute,
    joined,
    rename_tables,
    restart_copy,
    select_limit,
    select_start,
    trigger_name,
    typed,
)


RUNNING_WITH_MYSQL = True


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


ORIGIN_INDEXES = [
    "CREATE INDEX `campaign_87a49a9a` ON `campaign` (`post_id`)",
    "CREATE INDEX `campaign_87a49a9z` ON `campaign` (`objective`, `post_id`)",
]


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


class TestMigrations(TestCase):
    "Tests for migrations"

    def setUp(self):
        self.drop_migrate = False
        self.drop_archive = False
        self.table_name = "campaign"
        self.dest_name = "migrate_campaign"
        execute("default", ORIGIN_TABLE_SQL)
        for idx in ORIGIN_INDEXES:
            execute("default", idx)

    def tearDown(self):
        execute("default", "DROP TABLE %s" % self.table_name)
        if self.drop_migrate:
            execute("default", "DROP TABLE %s" % self.dest_name)
        if self.drop_archive:
            execute("default", "DROP TABLE %s" % archive_name(self.table_name))

    def _init(self, setup=None):
        "setup the migration"
        setup = setup or {}
        create_dest("default", self.table_name, DEST_TABLE_SQL)
        self.drop_migrate = True
        if setup.get("indexes", True):
            create_indexes("default", self.table_name, DEST_INDEXES)
            if setup.get("triggers", True):
                intersection = Intersection(ORIGIN_COLUMNS, DEST_COLUMNS, RENAMES)
                create_triggers("default", self.table_name, intersection)

    def _init_with_data(self, count):
        "Add default data into the table"
        self._init({'triggers': False})
        for i in range(1, 1 + count):
            self._insert(i)
        intersection = Intersection(ORIGIN_COLUMNS, DEST_COLUMNS, RENAMES)
        create_triggers("default", self.table_name, intersection)

    def _select_from_dest(self, table_name, id):
        "Select an id from the table"
        select_sql = "SELECT id, display_name, objective, budget, goal_spend, post_id, start_date, end_date, created_time, like_count FROM {0} WHERE id = {1}"
        return execute("default", select_sql.format(table_name, id))

    def _insert(self, id):
        "Load data into our original table"
        insert_sql = (
            """
            INSERT INTO {0} (id, name, objective, description, budget, goal_value, post_id, start_date, end_date)
            VALUES ({id}, "campaign {id}", "objective {id}", "description {id}", 10{id}.00, 9{id}.00, "1{id}_2{id}", "2015-05-0{id} 15:45:05", "2015-06-0{id} 12:30:15")
            """
        )
        return execute("default", insert_sql.format(self.table_name, id=id))

    def _expected_dest(self, id):
        "Expected result in the destination table"
        return (
            id,
            "campaign %d" % id,
            "objective %d" % id,
            100 + id,
            90 + id,
            '1%d_2%d' % (id, id),
            datetime.datetime(2015, 5, id, 15, 45, 5, 0),
            datetime.datetime(2015, 6, id, 12, 30, 15, 0),
            None,
            None,
        )

    def _count(self, table):
        "The count for the given table"
        ((count,),) = execute("default", "SELECT COUNT(*) FROM %s" % table)
        return count

    def test_dest_name(self):
        "Test destination name"
        self.assertEquals(dest_name(self.table_name), "migrate_campaign")

    def test_archive_name(self):
        "Test archive name"
        self.assertEquals(archive_name(self.table_name), "archive_campaign")

    def test_create_dest(self):
        "Test destination table creation"
        create_dest("default", self.table_name, DEST_TABLE_SQL)
        self.drop_migrate = True
        execute("default", "SELECT 1 FROM %s LIMIT 1" % self.dest_name)

    def test_create_indexes(self):
        "Test the creation of the new indexes"
        self._init({'indexes': False})
        create_indexes("default", self.table_name, DEST_INDEXES)
        res = execute("default", "SHOW INDEX FROM %s" % self.dest_name)
        self.assertEquals(len(res), 4)
        rows = [(row[2], row[3], row[4]) for row in res]
        self.assertItemsEqual(rows, [
            ("PRIMARY", 1, "id"),
            ("campaign_87a49a9a", 1, "post_id"),
            ("campaign_87a49a9z", 1, "objective"),
            ("campaign_87a49a9z", 2, "start_date"),
        ])

    def test_intersection(self):
        "Test the intersection class"
        intersection = Intersection(ORIGIN_COLUMNS, DEST_COLUMNS, RENAMES)

        # sorted intersection followed by renames keys
        self.assertEqual(intersection.origin_columns(), [
            "budget",
            "end_date",
            "id",
            "objective",
            "post_id",
            "start_date",
            "name",
            "goal_value",
        ])
        # sorted intersection followed by renames values
        self.assertEqual(intersection.dest_columns(), [
            "budget",
            "end_date",
            "id",
            "objective",
            "post_id",
            "start_date",
            "display_name",
            "goal_spend",
        ])
        # joined
        self.assertEqual(
            joined(intersection.origin_columns()),
            "`budget`, `end_date`, `id`, `objective`, `post_id`, `start_date`, `name`, `goal_value`"
        )
        # qualified
        self.assertEqual(
            typed('NEW', intersection.origin_columns()),
            "`NEW`.`budget`, `NEW`.`end_date`, `NEW`.`id`, `NEW`.`objective`, `NEW`.`post_id`, `NEW`.`start_date`, `NEW`.`name`, `NEW`.`goal_value`"
        )

    def test_trigger_name(self):
        "Test the trigger name"
        self.assertEquals(trigger_name("update", self.table_name), "migration_trigger_update_campaign")

    def test_create_triggers(self):
        "Test the triggers"
        self._init({'triggers': False})

        # insert before we create triggers
        self._insert(1)

        # create triggers
        intersection = Intersection(ORIGIN_COLUMNS, DEST_COLUMNS, RENAMES)
        create_triggers("default", self.table_name, intersection)

        # test insert
        self._insert(2)
        res = self._select_from_dest(self.dest_name, 2)
        self.assertEquals(res, (self._expected_dest(2),))

        # test update
        update_sql = "UPDATE %s SET budget=200, goal_value=198 WHERE id = 1" % self.table_name
        execute("default", update_sql)
        res = self._select_from_dest(self.dest_name, 1)
        self.assertEquals(res, ((
            1,
            "campaign 1",
            "objective 1",
            200,
            198,
            "11_21",
            datetime.datetime(2015, 5, 1, 15, 45, 5, 0),
            datetime.datetime(2015, 6, 1, 12, 30, 15, 0),
            None,
            None,
        ),))

        # test delete
        delete_sql = "DELETE FROM %s WHERE id = 1" % self.table_name
        execute("default", delete_sql)
        res = self._select_from_dest(self.dest_name, 1)
        self.assertEquals(res, ())

        # make sure the other rows are good
        self.assertEquals(self._count(self.table_name), 1)
        self.assertEquals(self._count(self.dest_name), 1)

    def test_delete_triggers(self):
        "Test deleting triggers"
        self._init()
        res = execute("default", "SHOW TRIGGERS FROM test")
        self.assertEquals(len(res), 3)
        delete_triggers("default", self.table_name)
        res = execute("default", "SHOW TRIGGERS FROM test")
        self.assertEquals(len(res), 0)

    def test_select_limit(self):
        "Test the limit id"
        self._init_with_data(3)
        self.assertEquals(select_limit("default", self.table_name), 3)

    def test_select_start(self):
        "Test the limit id"
        self._init_with_data(3)
        self.assertEquals(select_start("default", self.table_name), 1)

    def test_copy_in_chunks(self):
        "Test copy_in_chunks"
        self._init_with_data(5)
        intersection = Intersection(ORIGIN_COLUMNS, DEST_COLUMNS, RENAMES)
        copy_in_chunks("default", self.table_name, intersection, chunk_size=3)
        self.assertEquals(self._count(self.dest_name), 5)
        for i in range(1, 6):
            self.assertEquals(self._select_from_dest(self.dest_name, i), (self._expected_dest(i),))

    def test_copy_in_chunks_with_start_and_limit(self):
        "Test copy_in_chunks"
        self._init_with_data(5)
        intersection = Intersection(ORIGIN_COLUMNS, DEST_COLUMNS, RENAMES)
        copy_in_chunks("default", self.table_name, intersection, chunk_size=2, start=2, limit=3)
        self.assertEquals(self._count(self.dest_name), 2)
        for i in range(2, 3):
            self.assertEquals(self._select_from_dest(self.dest_name, i), (self._expected_dest(i),))

    def test_restart_copy(self):
        "Test copy_in_chunks"
        self._init_with_data(5)
        restart_copy("default", self.table_name, ORIGIN_COLUMNS, DEST_COLUMNS, renames=RENAMES, chunk_size=2, start=2, limit=3)
        self.assertEquals(self._count(self.dest_name), 2)
        for i in range(2, 3):
            self.assertEquals(self._select_from_dest(self.dest_name, i), (self._expected_dest(i),))

    def test_rename_tables(self):
        "Test rename table"
        self._init_with_data(5)
        intersection = Intersection(ORIGIN_COLUMNS, DEST_COLUMNS, RENAMES)
        copy_in_chunks("default", self.table_name, intersection, chunk_size=5)
        rename_tables("default", self.table_name)
        self.drop_migrate = False
        self.drop_archive = True

        # check the new tables
        self.assertEquals(self._count(self.table_name), 5)
        self.assertEquals(self._count(archive_name(self.table_name)), 5)

        for i in range(1, 6):
            self.assertEquals(self._select_from_dest(self.table_name, i), (self._expected_dest(i),))

        # check indexes
        res = execute("default", "SHOW INDEX FROM %s" % self.table_name)
        self.assertEquals(len(res), 4)
        rows = [(row[2], row[3], row[4]) for row in res]
        self.assertItemsEqual(rows, [
            ("PRIMARY", 1, "id"),
            ("campaign_87a49a9a", 1, "post_id"),
            ("campaign_87a49a9z", 1, "objective"),
            ("campaign_87a49a9z", 2, "start_date"),
        ])

    def test_change_table(self):
        "End to end test"
        # insert data
        for i in range(1, 6):
            self._insert(i)

        # run migration
        change_table("default", self.table_name, DEST_TABLE_SQL, DEST_INDEXES, ORIGIN_COLUMNS, DEST_COLUMNS, renames=RENAMES, chunk_size=3)
        finish_migration("default", self.table_name)
        self.drop_archive = True

        # check the new tables
        self.assertEquals(self._count(self.table_name), 5)
        self.assertEquals(self._count(archive_name(self.table_name)), 5)

        for i in range(1, 6):
            self.assertEquals(self._select_from_dest(self.table_name, i), (self._expected_dest(i),))

        # check indexes
        res = execute("default", "SHOW INDEX FROM %s" % self.table_name)
        self.assertEquals(len(res), 4)
        rows = [(row[2], row[3], row[4]) for row in res]
        self.assertItemsEqual(rows, [
            ("PRIMARY", 1, "id"),
            ("campaign_87a49a9a", 1, "post_id"),
            ("campaign_87a49a9z", 1, "objective"),
            ("campaign_87a49a9z", 2, "start_date"),
        ])
