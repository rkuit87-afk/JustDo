import sqlite3, os, json, logging
from datetime import datetime, date
from contextlib import contextmanager

# ---- Logging Setup ----
logger = logging.getLogger(__name__)

DB_FILE = os.environ.get('MILL_DB_FILE', os.path.join(os.path.dirname(__file__), 'mill.db'))

def get_db():
    """Get a database connection with WAL mode enabled."""
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_db_context():
    """Context manager for safe database connections.
    
    Usage:
        with get_db_context() as conn:
            result = conn.execute("SELECT * FROM users").fetchall()
    """
    conn = get_db()
    try:
        yield conn
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database schema and run migrations."""
    with get_db_context() as conn:
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            trade TEXT DEFAULT NULL,
            pin TEXT DEFAULT NULL,
            active INTEGER DEFAULT 1
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id TEXT,
            name TEXT NOT NULL,
            area TEXT NOT NULL,
            section TEXT DEFAULT NULL,
            criticality TEXT DEFAULT 'High',
            planned_hrs_day REAL DEFAULT 18,
            active INTEGER DEFAULT 1
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS checklist_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            item TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS pm_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            equipment_id INTEGER REFERENCES equipment(id),
            assigned_to INTEGER REFERENCES users(id),
            frequency TEXT NOT NULL,
            shift TEXT DEFAULT 'day',
            active INTEGER DEFAULT 1,
            last_generated DATE,
            checklist_template_id INTEGER
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS pm_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER REFERENCES pm_schedule(id),
            title TEXT NOT NULL,
            equipment_id INTEGER REFERENCES equipment(id),
            assigned_to INTEGER REFERENCES users(id),
            week_start DATE NOT NULL,
            due_date DATE,
            status TEXT DEFAULT 'pending',
            completed_by INTEGER REFERENCES users(id),
            completed_at DATETIME,
            outcome TEXT,
            condition_found TEXT,
            notes TEXT,
            task_type TEXT DEFAULT 'pm',
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS pm_checklist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER REFERENCES pm_tasks(id),
            item TEXT NOT NULL,
            checked INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS pm_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER REFERENCES pm_tasks(id),
            part_desc TEXT NOT NULL,
            qty INTEGER DEFAULT 1,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS breakdowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            log_date DATE,
            supervisor_id INTEGER REFERENCES users(id),
            artisan_id INTEGER REFERENCES users(id),
            equipment_id INTEGER REFERENCES equipment(id),
            sup_time_start TEXT,
            sup_time_end TEXT,
            sup_failure_type TEXT,
            sup_component TEXT,
            sup_failure_mode TEXT,
            sup_notes TEXT,
            sup_repair_action TEXT,
            sup_machine_status TEXT,
            art_time_start TEXT,
            art_time_end TEXT,
            art_description TEXT,
            art_repair_action TEXT,
            art_machine_status TEXT,
            art_followup TEXT,
            art_completed_at DATETIME,
            status TEXT DEFAULT 'supervisor_logged',
            disputed INTEGER DEFAULT 0,
            dispute_field TEXT,
            admin_resolved_by INTEGER REFERENCES users(id),
            admin_resolution_note TEXT,
            admin_resolved_at DATETIME,
            final_time_start TEXT,
            final_time_end TEXT,
            final_description TEXT,
            final_failure_type TEXT,
            downtime_mins INTEGER,
            production_downtime_mins INTEGER,
            maintenance_downtime_mins INTEGER,
            emailed INTEGER DEFAULT 0
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS breakdown_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            breakdown_id INTEGER REFERENCES breakdowns(id),
            part_desc TEXT NOT NULL,
            qty INTEGER DEFAULT 1,
            logged_by TEXT DEFAULT 'artisan'
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS reorder (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_desc TEXT NOT NULL,
            qty INTEGER DEFAULT 1,
            source TEXT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            cleared INTEGER DEFAULT 0
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS job_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requested_by INTEGER REFERENCES users(id),
            equipment_id INTEGER REFERENCES equipment(id),
            description TEXT NOT NULL,
            urgency TEXT DEFAULT 'Normal',
            status TEXT DEFAULT 'pending',
            admin_note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS shift_confirmations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            week_start DATE NOT NULL,
            shift TEXT NOT NULL,
            confirmed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            action_type TEXT,
            description TEXT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS failure_modes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode_name TEXT NOT NULL UNIQUE,
            category TEXT DEFAULT 'Mechanical',
            active INTEGER DEFAULT 1
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS boiler_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            log_date DATE,
            boiler_id INTEGER REFERENCES equipment(id),
            logged_by INTEGER REFERENCES users(id),
            tds_morning REAL,
            tds_night REAL,
            tds_highest REAL,
            blowdowns_total INTEGER DEFAULT 0,
            blowdown_done INTEGER DEFAULT 0,
            blowdown_time TEXT,
            condensate_meter_reading REAL,
            condensate_return REAL,
            makeup_water REAL,
            makeup_meter_reading REAL,
            softener_day INTEGER,
            softener_night INTEGER,
            salt_bags INTEGER,
            lost_time_mins INTEGER,
            downtime_incident INTEGER,
            notes TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS utility_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            log_date DATE,
            shift TEXT,
            substation_id INTEGER REFERENCES equipment(id),
            voltage_phase_a REAL,
            voltage_phase_b REAL,
            voltage_phase_c REAL,
            current_phase_a REAL,
            current_phase_b REAL,
            current_phase_c REAL,
            frequency REAL,
            power_factor REAL,
            gen_status TEXT,
            gen_load_percent REAL,
            fuel_level REAL,
            diesel_issued REAL DEFAULT 0,
            incidents TEXT,
            hour_meter REAL,
            run_hours_today REAL,
            oil_level TEXT,
            status TEXT DEFAULT 'standby',
            notes TEXT
        )''')

        # ============================================================
        # STORES MODULE TABLES (v10.1)
        # ============================================================

        # Department codes for stock numbering (e.g. ELK=Electrical, MEC=Mechanical)
        c.execute('''CREATE TABLE IF NOT EXISTS dept_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            label TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        )''')

        # Stock items
        c.execute('''CREATE TABLE IF NOT EXISTS stores_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT UNIQUE,
            part_desc TEXT NOT NULL,
            part_number TEXT,
            dept_code TEXT,
            category TEXT DEFAULT 'General',
            unit TEXT DEFAULT 'each',
            qty_on_hand REAL DEFAULT 0,
            qty_min_stock REAL DEFAULT 0,
            qty_max_stock REAL DEFAULT 0,
            bin_number TEXT,
            location TEXT,
            supplier TEXT,
            is_consumable INTEGER DEFAULT 0,
            is_critical INTEGER DEFAULT 0,
            critical_equipment_id INTEGER REFERENCES equipment(id),
            dead_stock INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_by INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Stock movements (issue / receive / adjust / return)
        c.execute('''CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id INTEGER REFERENCES stores_stock(id),
            movement_type TEXT NOT NULL,
            qty REAL NOT NULL,
            qty_after REAL,
            job_number TEXT,
            reference TEXT,
            notes TEXT,
            logged_by INTEGER REFERENCES users(id),
            logged_by_name TEXT,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Purchase requisitions
        c.execute('''CREATE TABLE IF NOT EXISTS requisitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pr_number TEXT UNIQUE,
            raised_by INTEGER REFERENCES users(id),
            raised_by_name TEXT,
            department TEXT,
            equipment_id INTEGER REFERENCES equipment(id),
            motivation TEXT,
            estimated_value REAL,
            is_special_order INTEGER DEFAULT 0,
            status TEXT DEFAULT 'submitted',
            actioned_by INTEGER REFERENCES users(id),
            actioned_at DATETIME,
            action_notes TEXT,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Requisition line items
        c.execute('''CREATE TABLE IF NOT EXISTS requisition_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requisition_id INTEGER REFERENCES requisitions(id),
            part_desc TEXT NOT NULL,
            part_number TEXT,
            qty REAL DEFAULT 1,
            unit TEXT DEFAULT 'each',
            is_special INTEGER DEFAULT 0,
            stock_id INTEGER REFERENCES stores_stock(id)
        )''')

        # Equipment spares (parts list per machine)
        c.execute('''CREATE TABLE IF NOT EXISTS equipment_spares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER REFERENCES equipment(id),
            part_desc TEXT NOT NULL,
            part_number TEXT,
            std_qty REAL DEFAULT 1,
            unit TEXT DEFAULT 'each',
            category TEXT DEFAULT 'General',
            stock_id INTEGER REFERENCES stores_stock(id),
            created_by INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Order templates (reorder templates per team leader)
        c.execute('''CREATE TABLE IF NOT EXISTS order_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            owner_id INTEGER REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS template_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER REFERENCES order_templates(id),
            item TEXT NOT NULL,
            part_number TEXT,
            unit TEXT DEFAULT 'each',
            sort_order INTEGER DEFAULT 0
        )''')

        # Suppliers (for RFQ email list)
        c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            category TEXT DEFAULT 'General',
            active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')


        # ============================================================
        # AREAS — plant area management (v10.2)
        # ============================================================
        c.execute('''CREATE TABLE IF NOT EXISTS areas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            code        TEXT,
            description TEXT,
            sort_order  INTEGER DEFAULT 0,
            active      INTEGER DEFAULT 1
        )''')

        # ============================================================
        # REQUISITION STATUS UPDATES (v10.1)
        # ============================================================
        c.execute('''CREATE TABLE IF NOT EXISTS requisition_status (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            requisition_id   INTEGER REFERENCES requisitions(id),
            status_update    TEXT,
            updated_by       INTEGER REFERENCES users(id),
            updated_by_name  TEXT,
            updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()
        logger.info("Database schema initialized")

    # Run migrations
    _run_migrations()

def _run_migrations():
    """Run any pending migrations."""
    migrations = [
        ("equipment",       "compound_id",                  "ALTER TABLE equipment ADD COLUMN compound_id TEXT"),
        ("breakdowns",      "art_failed_component",         "ALTER TABLE breakdowns ADD COLUMN art_failed_component TEXT"),
        ("breakdowns",      "art_failure_mode",             "ALTER TABLE breakdowns ADD COLUMN art_failure_mode TEXT"),
        ("breakdowns",      "source",                       "ALTER TABLE breakdowns ADD COLUMN source TEXT DEFAULT 'live'"),
        ("users",           "trade",                         "ALTER TABLE users ADD COLUMN trade TEXT DEFAULT NULL"),
        ("equipment",       "dept",                          "ALTER TABLE equipment ADD COLUMN dept TEXT"),
        ("equipment",       "planned_days_month",            "ALTER TABLE equipment ADD COLUMN planned_days_month INTEGER DEFAULT 23"),
        ("equipment",       "service_interval_hrs",          "ALTER TABLE equipment ADD COLUMN service_interval_hrs REAL"),
        ("equipment",       "last_service_hrs",              "ALTER TABLE equipment ADD COLUMN last_service_hrs REAL DEFAULT 0"),
        ("equipment",       "service_warning_hrs",           "ALTER TABLE equipment ADD COLUMN service_warning_hrs REAL DEFAULT 500"),
        ("equipment",       "decommissioned",                "ALTER TABLE equipment ADD COLUMN decommissioned INTEGER DEFAULT 0"),
        ("pm_tasks",        "blocked_reason",                "ALTER TABLE pm_tasks ADD COLUMN blocked_reason TEXT"),
        ("pm_tasks",        "recurring",                     "ALTER TABLE pm_tasks ADD COLUMN recurring INTEGER DEFAULT 0"),
        ("pm_tasks",        "frequency",                     "ALTER TABLE pm_tasks ADD COLUMN frequency TEXT"),
        ("pm_checklist_items", "flagged",                    "ALTER TABLE pm_checklist_items ADD COLUMN flagged INTEGER DEFAULT 0"),
        ("pm_checklist_items", "flag_comment",               "ALTER TABLE pm_checklist_items ADD COLUMN flag_comment TEXT"),
        # v10.2 — breakdown auto-timestamps, equipment mgmt, spares hierarchy
        ("breakdowns",       "sup_completed_at",       "ALTER TABLE breakdowns ADD COLUMN sup_completed_at DATETIME"),
        ("breakdowns",       "sup_completed_by",       "ALTER TABLE breakdowns ADD COLUMN sup_completed_by INTEGER"),
        ("equipment",        "area_code",               "ALTER TABLE equipment ADD COLUMN area_code TEXT"),
        ("equipment",        "description",             "ALTER TABLE equipment ADD COLUMN description TEXT"),
        ("equipment_spares", "part_category",           "ALTER TABLE equipment_spares ADD COLUMN part_category TEXT DEFAULT 'General'"),
        ("equipment_spares", "part_subcategory",        "ALTER TABLE equipment_spares ADD COLUMN part_subcategory TEXT"),
        ("equipment_spares", "supplier",                "ALTER TABLE equipment_spares ADD COLUMN supplier TEXT"),
        ("breakdown_parts",  "is_other",                "ALTER TABLE breakdown_parts ADD COLUMN is_other INTEGER DEFAULT 0"),
        ("breakdown_parts",  "other_note",              "ALTER TABLE breakdown_parts ADD COLUMN other_note TEXT"),
        ("requisition_items","planned_install_date",    "ALTER TABLE requisition_items ADD COLUMN planned_install_date DATE"),
        # v10.1 — job suspension / push-to-admin workflow
        ("pm_tasks",        "suspended",                     "ALTER TABLE pm_tasks ADD COLUMN suspended INTEGER DEFAULT 0"),
        ("pm_tasks",        "suspend_reason",                "ALTER TABLE pm_tasks ADD COLUMN suspend_reason TEXT"),
        ("pm_tasks",        "suspended_at",                  "ALTER TABLE pm_tasks ADD COLUMN suspended_at DATETIME"),
        ("pm_tasks",        "job_number",                    "ALTER TABLE pm_tasks ADD COLUMN job_number TEXT"),
        ("pm_tasks",        "is_tool",                       "ALTER TABLE pm_tasks ADD COLUMN is_tool INTEGER DEFAULT 0"),
        # v10.1 — users department + edit support
        ("users",           "department",                    "ALTER TABLE users ADD COLUMN department TEXT"),
        ("users",           "can_requisition",               "ALTER TABLE users ADD COLUMN can_requisition INTEGER DEFAULT 0"),
        ("users",           "stores_access",                 "ALTER TABLE users ADD COLUMN stores_access INTEGER DEFAULT 0"),
        ("users",           "create_scope",                  "ALTER TABLE users ADD COLUMN create_scope TEXT"),
    ]

    with get_db_context() as conn:
        for table, col, sql in migrations:
            try:
                conn.execute(sql)
                conn.commit()
                logger.debug(f"Migration applied: {table}.{col}")
            except sqlite3.OperationalError as e:
                # Column already exists
                pass
            except Exception as e:
                logger.error(f"Migration failed for {table}.{col}: {e}")

        # Handle shift_confirmations uniqueness
        try:
            conn.execute('''DELETE FROM shift_confirmations
                           WHERE id NOT IN (
                               SELECT MAX(id) FROM shift_confirmations GROUP BY user_id, week_start
                           )''')
            conn.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_shift_confirmation_user_week
                           ON shift_confirmations(user_id, week_start)''')
            conn.commit()
        except Exception as e:
            logger.debug(f"Shift confirmations cleanup: {e}")

    # Add indexes for performance
    _add_indexes()
    logger.info("Migrations completed")

def _add_indexes():
    """Add database indexes for query performance."""
    indexes = [
        ("idx_breakdowns_log_date", "breakdowns", "log_date"),
        ("idx_breakdowns_status", "breakdowns", "status"),
        ("idx_breakdowns_equipment_id", "breakdowns", "equipment_id"),
        ("idx_pm_tasks_assigned_to", "pm_tasks", "assigned_to"),
        ("idx_pm_tasks_week_start", "pm_tasks", "week_start"),
        ("idx_pm_tasks_status", "pm_tasks", "status"),
        ("idx_equipment_active", "equipment", "active"),
        ("idx_equipment_area", "equipment", "area"),
        ("idx_boiler_readings_log_date", "boiler_readings", "log_date"),
        ("idx_utility_readings_log_date", "utility_readings", "log_date"),
        ("idx_activity_log_logged_at", "activity_log", "logged_at"),
        ("idx_users_active", "users", "active"),
        ("idx_breakdowns_sup_completed", "breakdowns", "sup_completed_at"),
        ("idx_areas_active", "areas", "active"),

    ]

    with get_db_context() as conn:
        for idx_name, table, column in indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
                conn.commit()
            except Exception as e:
                logger.debug(f"Index creation skipped ({idx_name}): {e}")

def get_setting(key, default=''):
    """Retrieve a setting value."""
    with get_db_context() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row['value'] if row else default

def set_setting(key, value):
    """Set a setting value."""
    with get_db_context() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key,value,updated_at) VALUES (?,?,?)",
            (key, value, datetime.now().isoformat())
        )
        conn.commit()
    logger.info(f"Setting updated: {key}")

def seed_data():
    """Load initial seed data if database is empty."""
    with get_db_context() as conn:
        already = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0

    if not already:
        logger.info("Seeding initial data...")
        _seed_users_equipment()

    # These seeds are idempotent (INSERT OR IGNORE) so always safe to run
    _seed_areas()
    _seed_dept_codes()
    _seed_suppliers()
    logger.info("Seed data loaded successfully")


def _seed_users_equipment():
    """Seed the full team and equipment register (first run only)."""
    # role, trade, department, can_requisition, stores_access, create_scope
    users = [
        # ---- Admins ----
        ('Kuit, Roelof',            'admin',      None, None, 1, 1, 'all'),
        ('Coetser, Steven',         'stores_admin', None, None, 1, 1, 'stores'),
        ('Van Niekerk, Raymond',    'admin',      None, None, 1, 1, 'all'),
        # ---- Managers ----
        ('Van Den Heever, Andries', 'manager',    None, None, 1, 0, 'none'),   # allocates jobs, doesn't pick who
        ('Roth, Glen',              'manager',    None, None, 1, 0, 'all'),
        # ---- Team-leader managers (department-scoped creation) ----
        ('Botha, Stefan',           'manager',    None, 'Sawshop', 1, 1, 'sawshop'),   # own stock + requisitions, sawshop only
        ('Strydom, Francois',       'manager',    None, 'Wetmill', 1, 0, 'wetmill_nonelec'),
        ('Kock, Divan',             'manager',    None, 'Wetmill', 1, 0, 'wetmill_fitter'),
        ('Jacobs, JJ',              'manager',    None, 'Drymill', 1, 0, 'drymill'),
        ('Masebuko, Sunny',         'manager',    None, 'Drymill', 1, 0, 'drymill'),
        ('Sithole, Nathi',          'manager',    None, 'Drymill', 1, 0, 'drymill'),
        ('Buthelezi, Xolani',       'manager',    None, 'Drymill', 1, 0, 'drymill'),
        # ---- Electricians ----
        ('Hlophe, Given',           'artisan',    'Electrician', 'Wetmill', 0, 0, None),
        ('Simelane, Simanga',       'artisan',    'Electrician', 'Wetmill', 0, 0, None),
        ('Twala, Siyabonga',        'artisan',    'Electrician', 'Wetmill', 0, 0, None),
        ('Xaba, Khumbulani',        'artisan',    'Electrician', 'Wetmill', 0, 0, None),
        ('Pretorius, Chris',        'artisan',    'Electrician', 'Wetmill', 0, 0, None),
        # ---- Boilermakers ----
        ('Khumalo, Njabulo',        'artisan',    'Boilermaker', 'Wetmill', 0, 0, None),
        ('Tembe, Mandla',           'artisan',    'Boilermaker', 'Wetmill', 0, 0, None),
        ('Zikilala, Michael',       'artisan',    'Boilermaker', 'Wetmill', 0, 0, None),
        ('Gama, Doctor',            'artisan',    'Boilermaker', 'Wetmill', 0, 0, None),
        # ---- Fitters ----
        ('Davies, Wayne',           'artisan',    'Fitter', 'Wetmill', 0, 0, None),
        ('Lacante, Hendrik',        'artisan',    'Fitter', 'Wetmill', 0, 0, None),
        ('Maseko, Nkosinathi',      'artisan',    'Fitter', 'Wetmill', 0, 0, None),
        ('Swart, Petrus',           'artisan',    'Fitter', 'Wetmill', 0, 0, None),
        ('Nkosi, Sipho',            'artisan',    'Fitter', 'Wetmill', 0, 0, None),
        # ---- Operators ----
        ('Ngwenya, Paulos',         'artisan',    'Operator', 'Wetmill', 0, 0, None),
        # ---- Sawshop artisans ----
        ('Sawshop Fitter 1',        'artisan',    'Fitter', 'Sawshop', 0, 0, None),
    ]

    # From Raymond's Equipment Register (compound_id, name, dept, area, criticality, planned_hrs)
    equipment = [
        ('RDB-001 - DE-005', 'Ring Debarker 1 - VK800', 'Wetmill', 'PRM-WM-002', 'High', 18.0),
        ('BDS-001 - BE-004', 'Bandsaw 1 - Romeo', 'Wetmill', 'PRM-WM-003', 'High', 18.0),
        ('BDS-002 - BE-007', 'Bandsaw 2 - Juliet', 'Wetmill', 'PRM-WM-003', 'High', 18.0),
        ('BDS-003 - FE-003', 'Bandsaw 3 - Teletwin', 'Wetmill', 'PRM-WM-003', 'Medium', 9.0),
        ('BKO-001 - RE-007', 'Board Edger 1 - EWD', 'Wetmill', 'PRM-WM-004', 'High', 18.0),
        ('GNS-001 - BE-008', 'Gangsaw 1 - Multirip 240', 'Wetmill', 'PRM-WM-004', 'High', 18.0),
        ('GNS-002 - FE-010', 'Gangsaw 2 - DAMR', 'Wetmill', 'PRM-WM-004', 'Medium', 9.0),
        ('TMT-001 - ME-002', 'Trim Table 1 - Green chain Trimdeck', 'Wetmill', 'PRM-WM-005', 'High', 18.0),
        ('TMT-002 - FE-022', 'Trim Table 2 - Sky Trimmer', 'Wetmill', 'PRM-WM-005', 'Medium', 9.0),
        ('RDT-001 - ME-006', 'Roundtable 1', 'Wetmill', 'PRM-WM-005', 'High', 18.0),
        ('STR-001 - ME-007', 'Autostacker 1', 'Wetmill', 'PRM-WM-005', 'High', 18.0),
        ('CPR-001 - BE-018', 'Chipper 1 - Bandline', 'Wetmill', 'PRM-WM-006', 'High', 18.0),
        ('CPR-002 - FE-020', 'Chipper 2 - Frameline', 'Wetmill', 'PRM-WM-006', 'Medium', 18.0),
        ('SKR-001 - BE-020', 'Shaker 1 - Two Screen', 'Wetmill', 'PRM-WM-006', 'High', 18.0),
        ('SKR-002 - FE-021', 'Shaker 2 - One screen', 'Wetmill', 'PRM-WM-006', 'Medium', 18.0),
        ('SLR-001 - FE-019', 'Scalper 1 - Rotor', 'Wetmill', 'PRM-WM-006', 'Medium', 18.0),
        ('KLN-001 - KE-003', 'Kiln 1 - Bollman 1', 'Kilns', 'PRM-DM-007', 'High', 24.0),
        ('KLN-002 - KE-004', 'Kiln 2 - Bollman 2', 'Kilns', 'PRM-DM-007', 'High', 24.0),
        ('KLN-003 - KE-002', 'Kiln 3 - Winsor 2', 'Kilns', 'PRM-DM-007', 'High', 24.0),
        ('KLN-004 - KE-001', 'Kiln 4 - Winsor 1', 'Kilns', 'PRM-DM-007', 'High', 24.0),
        ('KLN-005 - KE-005', 'Kiln 5 - TFD 1', 'Kilns', 'PRM-DM-007', 'High', 24.0),
        ('PGS-001 - DE-001', 'Plank Grader-Stacker 1 - Odden', 'Drymill', 'PRM-DM-008', 'High', 9.0),
        ('OXC-001 - DE-101', 'Optimizing Cross Cutter 1 - Paul', 'Drymill', 'PRM-DM-008', 'Medium', 18.0),
        ('PLR-001 - DE-001', 'Planer 1 - Rex 1', 'Drymill', 'PRM-DM-009', 'High', 18.0),
        ('PLR-002 - DE-002', 'Planer 2 - Rex 2', 'Drymill', 'PRM-DM-009', 'Medium', 9.0),
        ('JTR-001 - DE-102', 'Jointer 1 - Finger Jointer', 'Drymill', 'PRM-DM-010', 'Medium', 9.0),
        ('CPR-003 - DE-002', 'Chipper 3 - Drymill', 'Drymill', 'PRM-DM-013', 'High', 18.0),
        ('GEN-523 - Perkings', 'Generator 523 - 2000KVA', 'Wetmill', 'PRM-UTI-016', 'Medium', 24.0),
        ('GEN-018 - Cummings', 'Generator 18 - 1000KVA', 'Drymill', 'PRM-UTI-016', 'Medium', 24.0),
        ('GEN-148 - Perkins', 'Generator 149 - 800KVA', 'Boilers & Kilns', 'PRM-UTI-016', 'Medium', 24.0),
        ('SOL-001 - FARM', 'Solar farm 1 - Inverter', 'Utility - Electrical', 'PRM-UTI-016', 'High', 24.0),
        ('VCT -001', 'Voltage-Current Transformer 1', 'Sawmill', 'PRM-UTI-016', 'High', 24.0),
        ('BLR-001', 'Boiler 1 - 12TpH', 'Boilers', 'PRM-UTI-018', 'High', 24.0),
        ('BLR-002', 'Boiler 2 - 10TpH', 'Boilers', 'PRM-UTI-018', 'High', 24.0),
        ('BLR-003', 'Boiler 3 - 10TpH', 'Boilers', 'PRM-UTI-018', 'High', 24.0),
    ]

    failure_modes = [
        ('Mechanical Failure', 'Mechanical'),
        ('Electrical Failure', 'Electrical'),
        ('Hydraulic Failure', 'Hydraulic'),
        ('Control System Failure', 'Control'),
        ('Belt/Chain Failure', 'Mechanical'),
        ('Bearing Failure', 'Mechanical'),
        ('Motor Failure', 'Electrical'),
        ('Sensor Failure', 'Control'),
        ('Seal Failure', 'Mechanical'),
        ('Lubrication Issue', 'Mechanical'),
    ]

    with get_db_context() as conn:
        conn.executemany(
            "INSERT INTO users (name,role,trade,department,can_requisition,stores_access,create_scope) "
            "VALUES (?,?,?,?,?,?,?)", users
        )
        conn.executemany(
            "INSERT INTO equipment (compound_id,name,dept,area,criticality,planned_hrs_day,section) "
            "VALUES (?,?,?,?,?,?,?)",
            [(c, n, d, a, cr, h, d) for (c, n, d, a, cr, h) in equipment]
        )
        conn.executemany(
            "INSERT INTO failure_modes (mode_name, category) VALUES (?, ?)",
            failure_modes
        )
        conn.commit()
    logger.info(f"Seeded {len(users)} users, {len(equipment)} equipment items")



def _seed_areas():
    """Seed standard plant areas (idempotent)."""
    areas = [
        ('Wetmill',  'WM', 'Wetmill processing area',          1),
        ('Drymill',  'DM', 'Drymill processing area',          2),
        ('Kilns',    'KL', 'Kiln drying area',                 3),
        ('Utility',  'UT', 'Utilities — Boilers & Generators', 4),
        ('Sawshop',  'SS', 'Sawshop area',                     5),
    ]
    with get_db_context() as conn:
        for name, code, desc, order in areas:
            conn.execute(
                "INSERT OR IGNORE INTO areas (name,code,description,sort_order) VALUES (?,?,?,?)",
                (name, code, desc, order)
            )
        conn.commit()

def _seed_dept_codes():
    """Seed standard stores department codes (idempotent)."""
    codes = [
        ('ELK', 'Electrical', 1),
        ('MEC', 'Mechanical', 2),
        ('HYD', 'Hydraulic', 3),
        ('PNE', 'Pneumatic', 4),
        ('CON', 'Consumables', 5),
        ('BRG', 'Bearings', 6),
        ('BLT', 'Belts', 7),
        ('FAS', 'Fasteners', 8),
        ('LUB', 'Lubricants', 9),
        ('SAW', 'Saw / Blades', 10),
        ('GEN', 'General', 11),
    ]
    with get_db_context() as conn:
        for code, label, order in codes:
            conn.execute(
                "INSERT OR IGNORE INTO dept_codes (code,label,sort_order) VALUES (?,?,?)",
                (code, label, order)
            )
        conn.commit()


def _seed_suppliers():
    """Seed a couple of example suppliers (idempotent)."""
    with get_db_context() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        if existing == 0:
            conn.executemany(
                "INSERT INTO suppliers (name,email,category) VALUES (?,?,?)",
                [
                    ('Example Electrical Supplier', 'electrical@example.com', 'Electrical'),
                    ('Example Mechanical Supplier', 'mechanical@example.com', 'Mechanical'),
                ]
            )
            conn.commit()

if __name__ == '__main__':
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    init_db()
    seed_data()
