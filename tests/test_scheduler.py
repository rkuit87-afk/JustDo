"""
Unit tests for scheduler.py

Covers: get_week_start, _due_this_week, generate_weekly_tasks,
        get_tasks_for_artisan, mark_task_done, get_tasks_for_week,
        get_task_completion_rate.
"""

import pytest
from datetime import date, timedelta


# ============================================================
# get_week_start
# ============================================================

class TestGetWeekStart:
    def test_monday_returns_same(self):
        from scheduler import get_week_start
        monday = date(2025, 6, 16)  # a Monday
        assert get_week_start(monday) == monday

    def test_tuesday_returns_monday(self):
        from scheduler import get_week_start
        tuesday = date(2025, 6, 17)
        assert get_week_start(tuesday) == date(2025, 6, 16)

    def test_sunday_returns_previous_monday(self):
        from scheduler import get_week_start
        sunday = date(2025, 6, 22)
        assert get_week_start(sunday) == date(2025, 6, 16)

    def test_saturday(self):
        from scheduler import get_week_start
        saturday = date(2025, 6, 21)
        assert get_week_start(saturday) == date(2025, 6, 16)

    def test_wednesday(self):
        from scheduler import get_week_start
        wednesday = date(2025, 6, 18)
        assert get_week_start(wednesday) == date(2025, 6, 16)

    def test_no_arg_returns_current_week(self):
        from scheduler import get_week_start
        result = get_week_start()
        today = date.today()
        expected = today - timedelta(days=today.weekday())
        assert result == expected


# ============================================================
# _due_this_week
# ============================================================

class TestDueThisWeek:
    def _make_sched(self, frequency, last_generated):
        """Build a dict that looks like a pm_schedule row."""
        return {
            "frequency": frequency,
            "last_generated": last_generated,
        }

    def test_weekly_never_generated(self):
        from scheduler import _due_this_week
        sched = self._make_sched("weekly", None)
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_weekly_generated_this_week(self):
        from scheduler import _due_this_week
        sched = self._make_sched("weekly", "2025-06-16")
        assert _due_this_week(sched, date(2025, 6, 16)) is False

    def test_weekly_generated_last_week(self):
        from scheduler import _due_this_week
        sched = self._make_sched("weekly", "2025-06-09")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_biweekly_only_one_week_ago(self):
        from scheduler import _due_this_week
        sched = self._make_sched("biweekly", "2025-06-09")
        assert _due_this_week(sched, date(2025, 6, 16)) is False

    def test_biweekly_two_weeks_ago(self):
        from scheduler import _due_this_week
        sched = self._make_sched("biweekly", "2025-06-02")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_monthly_four_weeks_ago(self):
        from scheduler import _due_this_week
        sched = self._make_sched("monthly", "2025-05-19")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_monthly_two_weeks_ago(self):
        from scheduler import _due_this_week
        sched = self._make_sched("monthly", "2025-06-02")
        assert _due_this_week(sched, date(2025, 6, 16)) is False

    def test_quarterly_due(self):
        from scheduler import _due_this_week
        sched = self._make_sched("quarterly", "2025-03-17")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_quarterly_not_due(self):
        from scheduler import _due_this_week
        sched = self._make_sched("quarterly", "2025-05-01")
        assert _due_this_week(sched, date(2025, 6, 16)) is False

    def test_annual_due(self):
        from scheduler import _due_this_week
        sched = self._make_sched("annual", "2024-06-10")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_annual_not_due(self):
        from scheduler import _due_this_week
        sched = self._make_sched("annual", "2025-01-01")
        assert _due_this_week(sched, date(2025, 6, 16)) is False

    def test_unknown_frequency_defaults_to_weekly(self):
        from scheduler import _due_this_week
        sched = self._make_sched("unknown_freq", "2025-06-09")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_none_frequency_defaults_to_weekly(self):
        from scheduler import _due_this_week
        sched = self._make_sched(None, "2025-06-09")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_invalid_last_generated_date(self):
        from scheduler import _due_this_week
        sched = self._make_sched("weekly", "not-a-date")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_3weekly(self):
        from scheduler import _due_this_week
        sched = self._make_sched("3weekly", "2025-05-26")
        assert _due_this_week(sched, date(2025, 6, 16)) is True
        sched2 = self._make_sched("3weekly", "2025-06-02")
        assert _due_this_week(sched2, date(2025, 6, 16)) is False

    def test_semiannual(self):
        from scheduler import _due_this_week
        sched = self._make_sched("semiannual", "2024-12-16")
        assert _due_this_week(sched, date(2025, 6, 16)) is True

    def test_4weekly_alias(self):
        from scheduler import _due_this_week
        sched = self._make_sched("4weekly", "2025-05-19")
        assert _due_this_week(sched, date(2025, 6, 16)) is True


# ============================================================
# generate_weekly_tasks (integration with temp DB)
# ============================================================

class TestGenerateWeeklyTasks:
    def _setup_schedule(self, conn):
        """Insert a user, equipment, and PM schedule using high IDs to avoid seed conflicts."""
        conn.execute(
            "INSERT INTO users (id, name, role) VALUES (900, 'Test User', 'artisan')"
        )
        conn.execute(
            "INSERT INTO equipment (id, name, area) VALUES (900, 'Test Machine', 'Wetmill')"
        )
        conn.execute(
            "INSERT INTO pm_schedule (id, title, equipment_id, assigned_to, frequency, active) "
            "VALUES (900, 'Weekly Check', 900, 900, 'weekly', 1)"
        )
        conn.commit()

    def test_creates_tasks(self, seeded_db):
        conn = seeded_db
        self._setup_schedule(conn)
        from scheduler import generate_weekly_tasks, get_week_start
        generate_weekly_tasks()
        week_start = get_week_start().isoformat()
        tasks = conn.execute(
            "SELECT * FROM pm_tasks WHERE schedule_id=900 AND week_start=?",
            (week_start,)
        ).fetchall()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Weekly Check"
        assert tasks[0]["status"] == "pending"

    def test_no_duplicate_tasks(self, seeded_db):
        conn = seeded_db
        self._setup_schedule(conn)
        from scheduler import generate_weekly_tasks, get_week_start
        generate_weekly_tasks()
        generate_weekly_tasks()  # second run
        week_start = get_week_start().isoformat()
        tasks = conn.execute(
            "SELECT * FROM pm_tasks WHERE schedule_id=900 AND week_start=?",
            (week_start,)
        ).fetchall()
        assert len(tasks) == 1

    def test_inactive_schedule_skipped(self, seeded_db):
        conn = seeded_db
        conn.execute(
            "INSERT INTO users (id, name, role) VALUES (901, 'User2', 'artisan')"
        )
        conn.execute(
            "INSERT INTO equipment (id, name, area) VALUES (901, 'Machine2', 'Wetmill')"
        )
        conn.execute(
            "INSERT INTO pm_schedule (id, title, equipment_id, assigned_to, frequency, active) "
            "VALUES (901, 'Inactive Check', 901, 901, 'weekly', 0)"
        )
        conn.commit()
        from scheduler import generate_weekly_tasks, get_week_start
        generate_weekly_tasks()
        week_start = get_week_start().isoformat()
        tasks = conn.execute(
            "SELECT * FROM pm_tasks WHERE schedule_id=901 AND week_start=?",
            (week_start,)
        ).fetchall()
        assert len(tasks) == 0


# ============================================================
# get_task_completion_rate
# ============================================================

class TestTaskCompletionRate:
    def test_empty_week(self, db_conn):
        from scheduler import get_task_completion_rate
        rate = get_task_completion_rate(date(2025, 6, 16))
        assert rate["total"] == 0
        assert rate["completion_rate"] == 0

    def test_with_tasks(self, db_conn):
        from scheduler import get_task_completion_rate
        conn = db_conn
        conn.execute("INSERT INTO users (id, name, role) VALUES (1, 'Test', 'artisan')")
        conn.execute("INSERT INTO equipment (id, name, area) VALUES (1, 'M1', 'Wetmill')")
        week = "2025-06-16"
        conn.execute(
            "INSERT INTO pm_tasks (title, equipment_id, assigned_to, week_start, status) "
            "VALUES ('T1', 1, 1, ?, 'done')", (week,)
        )
        conn.execute(
            "INSERT INTO pm_tasks (title, equipment_id, assigned_to, week_start, status) "
            "VALUES ('T2', 1, 1, ?, 'pending')", (week,)
        )
        conn.commit()

        rate = get_task_completion_rate(date(2025, 6, 16))
        assert rate["total"] == 2
        assert rate["completed"] == 1
        assert rate["pending"] == 1
        assert rate["completion_rate"] == 50.0


# ============================================================
# get_tasks_for_week
# ============================================================

class TestGetTasksForWeek:
    def test_returns_tasks(self, db_conn):
        from scheduler import get_tasks_for_week
        conn = db_conn
        conn.execute("INSERT INTO users (id, name, role) VALUES (1, 'Test', 'artisan')")
        conn.execute("INSERT INTO equipment (id, name, area) VALUES (1, 'M1', 'Wetmill')")
        week = "2025-06-16"
        conn.execute(
            "INSERT INTO pm_tasks (title, equipment_id, assigned_to, week_start, status) "
            "VALUES ('T1', 1, 1, ?, 'pending')", (week,)
        )
        conn.commit()
        tasks = get_tasks_for_week(date(2025, 6, 16))
        assert len(tasks) == 1
        assert tasks[0]["title"] == "T1"
        assert tasks[0]["assigned_to_name"] == "Test"

    def test_empty_week(self, db_conn):
        from scheduler import get_tasks_for_week
        tasks = get_tasks_for_week(date(2025, 1, 1))
        assert tasks == []


# ============================================================
# mark_task_done
# ============================================================

class TestMarkTaskDone:
    def test_marks_done(self, db_conn):
        from scheduler import mark_task_done
        conn = db_conn
        conn.execute("INSERT INTO users (id, name, role) VALUES (1, 'Test', 'artisan')")
        conn.execute("INSERT INTO equipment (id, name, area) VALUES (1, 'M1', 'Wetmill')")
        conn.execute(
            "INSERT INTO pm_tasks (id, title, equipment_id, assigned_to, week_start, status) "
            "VALUES (1, 'T1', 1, 1, '2025-06-16', 'pending')"
        )
        conn.execute(
            "INSERT INTO pm_checklist_items (id, task_id, item) VALUES (1, 1, 'Check oil')"
        )
        conn.commit()

        mark_task_done(
            task_id=1,
            completed_by=1,
            outcome="OK",
            condition="Good",
            notes="All fine",
            parts=[{"desc": "Bolt", "qty": 2}],
            checklist_states={"1": True},
        )

        task = conn.execute("SELECT * FROM pm_tasks WHERE id=1").fetchone()
        assert task["status"] == "done"
        assert task["completed_by"] == 1
        assert task["outcome"] == "OK"

        # Check parts recorded
        parts = conn.execute("SELECT * FROM pm_parts WHERE task_id=1").fetchall()
        assert len(parts) == 1
        assert parts[0]["part_desc"] == "Bolt"
        assert parts[0]["qty"] == 2

        # Check reorder entry
        reorder = conn.execute("SELECT * FROM reorder").fetchall()
        assert len(reorder) == 1

        # Check checklist updated
        cl = conn.execute("SELECT * FROM pm_checklist_items WHERE id=1").fetchone()
        assert cl["checked"] == 1

    def test_empty_parts(self, db_conn):
        from scheduler import mark_task_done
        conn = db_conn
        conn.execute("INSERT INTO users (id, name, role) VALUES (1, 'Test', 'artisan')")
        conn.execute("INSERT INTO equipment (id, name, area) VALUES (1, 'M1', 'Wetmill')")
        conn.execute(
            "INSERT INTO pm_tasks (id, title, equipment_id, assigned_to, week_start, status) "
            "VALUES (2, 'T2', 1, 1, '2025-06-16', 'pending')"
        )
        conn.commit()
        mark_task_done(2, 1, "OK", "Good", "", parts=[], checklist_states={})
        task = conn.execute("SELECT * FROM pm_tasks WHERE id=2").fetchone()
        assert task["status"] == "done"


# ============================================================
# get_tasks_for_artisan
# ============================================================

class TestGetTasksForArtisan:
    def test_returns_assigned_tasks(self, db_conn):
        from scheduler import get_tasks_for_artisan, get_week_start
        conn = db_conn
        conn.execute("INSERT INTO users (id, name, role) VALUES (1, 'Art1', 'artisan')")
        conn.execute("INSERT INTO users (id, name, role) VALUES (2, 'Art2', 'artisan')")
        conn.execute("INSERT INTO equipment (id, name, area) VALUES (1, 'M1', 'Wetmill')")
        week = get_week_start().isoformat()
        conn.execute(
            "INSERT INTO pm_tasks (id, title, equipment_id, assigned_to, week_start, status) "
            "VALUES (1, 'Art1 Task', 1, 1, ?, 'pending')", (week,)
        )
        conn.execute(
            "INSERT INTO pm_tasks (id, title, equipment_id, assigned_to, week_start, status) "
            "VALUES (2, 'Art2 Task', 1, 2, ?, 'pending')", (week,)
        )
        conn.commit()

        tasks = get_tasks_for_artisan(1)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Art1 Task"

    def test_excludes_done_tasks(self, db_conn):
        from scheduler import get_tasks_for_artisan, get_week_start
        conn = db_conn
        conn.execute("INSERT INTO users (id, name, role) VALUES (1, 'Art1', 'artisan')")
        conn.execute("INSERT INTO equipment (id, name, area) VALUES (1, 'M1', 'Wetmill')")
        week = get_week_start().isoformat()
        conn.execute(
            "INSERT INTO pm_tasks (id, title, equipment_id, assigned_to, week_start, status) "
            "VALUES (1, 'Done Task', 1, 1, ?, 'done')", (week,)
        )
        conn.commit()
        tasks = get_tasks_for_artisan(1)
        assert len(tasks) == 0

    def test_includes_checklist(self, db_conn):
        from scheduler import get_tasks_for_artisan, get_week_start
        conn = db_conn
        conn.execute("INSERT INTO users (id, name, role) VALUES (1, 'Art1', 'artisan')")
        conn.execute("INSERT INTO equipment (id, name, area) VALUES (1, 'M1', 'Wetmill')")
        week = get_week_start().isoformat()
        conn.execute(
            "INSERT INTO pm_tasks (id, title, equipment_id, assigned_to, week_start, status) "
            "VALUES (1, 'Task', 1, 1, ?, 'pending')", (week,)
        )
        conn.execute(
            "INSERT INTO pm_checklist_items (task_id, item, sort_order) VALUES (1, 'Check A', 0)"
        )
        conn.execute(
            "INSERT INTO pm_checklist_items (task_id, item, sort_order) VALUES (1, 'Check B', 1)"
        )
        conn.commit()
        tasks = get_tasks_for_artisan(1)
        assert len(tasks) == 1
        assert len(tasks[0]["checklist"]) == 2
        assert tasks[0]["checklist"][0]["item"] == "Check A"
