"""
Unit tests for database.py

Covers: schema init, migrations, settings CRUD, seed data,
        plant hierarchy (add/move/breadcrumb), parse_compound_id.
"""

import sqlite3
import pytest
from datetime import datetime


# ============================================================
# Schema & Init
# ============================================================

class TestInitDb:
    def test_creates_core_tables(self, db_conn):
        tables = {
            row[0]
            for row in db_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        expected = {
            "users", "equipment", "checklist_templates",
            "pm_schedule", "pm_tasks", "pm_checklist_items", "pm_parts",
            "breakdowns", "breakdown_parts", "breakdown_allocations",
            "reorder", "job_requests", "shift_confirmations",
            "settings", "activity_log", "failure_modes",
            "boiler_readings", "utility_readings",
            "stores_stock", "stock_movements", "requisitions",
            "requisition_items", "equipment_spares",
            "order_templates", "template_items", "suppliers",
            "areas", "requisition_status",
            "component_categories", "equipment_components", "component_events",
            "plant_nodes", "plant_node_ancestors", "migration_log",
            "dept_codes",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    def test_wal_mode_enabled(self, db_conn):
        mode = db_conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"

    def test_foreign_keys_enabled(self, db_conn):
        fk = db_conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1

    def test_init_is_idempotent(self, _use_tmp_db):
        import database
        database.init_db()
        database.init_db()  # second call should not raise


# ============================================================
# Migrations
# ============================================================

class TestMigrations:
    def test_migration_adds_compound_id(self, db_conn):
        cols = [
            row[1]
            for row in db_conn.execute("PRAGMA table_info(equipment)").fetchall()
        ]
        assert "compound_id" in cols

    def test_migration_adds_art_failed_component(self, db_conn):
        cols = [
            row[1]
            for row in db_conn.execute("PRAGMA table_info(breakdowns)").fetchall()
        ]
        assert "art_failed_component" in cols
        assert "art_failure_mode" in cols

    def test_indexes_created(self, db_conn):
        indexes = {
            row[1]
            for row in db_conn.execute(
                "SELECT * FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
            ).fetchall()
        }
        assert "idx_breakdowns_log_date" in indexes
        assert "idx_pm_tasks_week_start" in indexes
        assert "idx_equipment_active" in indexes


# ============================================================
# Settings CRUD
# ============================================================

class TestSettings:
    def test_get_default(self, db_conn):
        from database import get_setting
        assert get_setting("nonexistent") == ""

    def test_get_custom_default(self, db_conn):
        from database import get_setting
        assert get_setting("nonexistent", "fallback") == "fallback"

    def test_set_and_get(self, db_conn):
        from database import get_setting, set_setting
        set_setting("site_name", "Test Mill")
        assert get_setting("site_name") == "Test Mill"

    def test_set_overwrites(self, db_conn):
        from database import get_setting, set_setting
        set_setting("site_name", "First")
        set_setting("site_name", "Second")
        assert get_setting("site_name") == "Second"


# ============================================================
# Seed Data
# ============================================================

class TestSeedData:
    def test_seed_creates_users(self, seeded_db):
        count = seeded_db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert count > 0

    def test_seed_creates_equipment(self, seeded_db):
        count = seeded_db.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
        assert count > 0

    def test_seed_creates_failure_modes(self, seeded_db):
        count = seeded_db.execute("SELECT COUNT(*) FROM failure_modes").fetchone()[0]
        assert count > 0

    def test_seed_creates_areas(self, seeded_db):
        count = seeded_db.execute("SELECT COUNT(*) FROM areas").fetchone()[0]
        assert count > 0

    def test_seed_creates_dept_codes(self, seeded_db):
        count = seeded_db.execute("SELECT COUNT(*) FROM dept_codes").fetchone()[0]
        assert count > 0

    def test_seed_creates_suppliers(self, seeded_db):
        count = seeded_db.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        assert count > 0

    def test_seed_is_idempotent(self, seeded_db):
        import database
        count_before = seeded_db.execute("SELECT COUNT(*) FROM areas").fetchone()[0]
        database.seed_data()
        count_after = seeded_db.execute("SELECT COUNT(*) FROM areas").fetchone()[0]
        assert count_after == count_before


# ============================================================
# parse_compound_id
# ============================================================

class TestParseCompoundId:
    def test_valid_hierarchical(self):
        from database import parse_compound_id
        assert parse_compound_id("WM-ROM-SH1-MOT-001") == ["WM", "ROM", "SH1", "MOT", "001"]

    def test_dual_reference_returns_none(self):
        from database import parse_compound_id
        assert parse_compound_id("BDS-001 - BE-004") is None

    def test_short_code_returns_none(self):
        from database import parse_compound_id
        assert parse_compound_id("BLR-001") is None

    def test_empty_returns_none(self):
        from database import parse_compound_id
        assert parse_compound_id("") is None
        assert parse_compound_id(None) is None

    def test_non_numeric_tail_returns_none(self):
        from database import parse_compound_id
        assert parse_compound_id("WM-ROM-SH1-MOT-ABC") is None

    def test_lowercase_segment_returns_none(self):
        from database import parse_compound_id
        assert parse_compound_id("WM-rom-SH1-001") is None

    def test_three_segments_valid(self):
        from database import parse_compound_id
        assert parse_compound_id("WM-ROM-001") == ["WM", "ROM", "001"]

    def test_whitespace_stripped(self):
        from database import parse_compound_id
        assert parse_compound_id("  WM-ROM-SH1-001  ") == ["WM", "ROM", "SH1", "001"]


# ============================================================
# Plant Hierarchy
# ============================================================

class TestPlantHierarchy:
    def test_add_root_node(self, db_conn):
        from database import add_plant_node
        nid = add_plant_node(None, "Root")
        assert isinstance(nid, int)
        assert nid > 0

    def test_add_child_node(self, db_conn):
        from database import add_plant_node
        root_id = add_plant_node(None, "Root")
        child_id = add_plant_node(root_id, "Child")
        assert child_id != root_id

    def test_get_node_children(self, db_conn):
        from database import add_plant_node, get_node_children
        root_id = add_plant_node(None, "Root")
        add_plant_node(root_id, "A")
        add_plant_node(root_id, "B")
        children = get_node_children(root_id)
        assert len(children) == 2
        names = {c["name"] for c in children}
        assert names == {"A", "B"}

    def test_child_count_in_children(self, db_conn):
        from database import add_plant_node, get_node_children
        root_id = add_plant_node(None, "Root")
        mid_id = add_plant_node(root_id, "Mid")
        add_plant_node(mid_id, "Leaf")
        children = get_node_children(root_id)
        mid_row = [c for c in children if c["name"] == "Mid"][0]
        assert mid_row["child_count"] == 1

    def test_breadcrumb(self, db_conn):
        from database import add_plant_node, get_node_breadcrumb
        r = add_plant_node(None, "Root")
        m = add_plant_node(r, "Mid")
        l = add_plant_node(m, "Leaf")
        bc = get_node_breadcrumb(l)
        names = [n["name"] for n in bc]
        assert names == ["Root", "Mid", "Leaf"]

    def test_get_node_ancestors(self, db_conn):
        from database import add_plant_node, get_node_ancestors
        r = add_plant_node(None, "Root")
        m = add_plant_node(r, "Mid")
        l = add_plant_node(m, "Leaf")
        ancestors = get_node_ancestors(l)
        assert r in ancestors
        assert m in ancestors

    def test_move_node(self, db_conn):
        from database import add_plant_node, move_node, get_node_children
        r1 = add_plant_node(None, "Root1")
        r2 = add_plant_node(None, "Root2")
        child = add_plant_node(r1, "Child")
        assert move_node(child, r2) is True
        assert len(get_node_children(r1)) == 0
        assert len(get_node_children(r2)) == 1

    def test_move_into_own_subtree_fails(self, db_conn):
        from database import add_plant_node, move_node
        r = add_plant_node(None, "Root")
        c = add_plant_node(r, "Child")
        assert move_node(r, c) is False

    def test_move_to_nonexistent_parent_fails(self, db_conn):
        from database import add_plant_node, move_node
        r = add_plant_node(None, "Root")
        assert move_node(r, 99999) is False

    def test_get_equipment_node_returns_none_when_unlinked(self, db_conn):
        from database import get_equipment_node
        result = get_equipment_node("NONEXISTENT")
        assert result is None


# ============================================================
# get_db_context error handling
# ============================================================

class TestDbContext:
    def test_context_rolls_back_on_error(self, db_conn):
        from database import get_db_context
        with pytest.raises(sqlite3.OperationalError):
            with get_db_context() as conn:
                conn.execute("INSERT INTO users (name, role) VALUES ('Test', 'admin')")
                conn.execute("THIS IS INVALID SQL")
        # The insert should have been rolled back
        import database
        with database.get_db_context() as conn:
            count = conn.execute("SELECT COUNT(*) FROM users WHERE name='Test'").fetchone()[0]
            assert count == 0
