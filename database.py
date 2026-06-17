import sqlite3, os, json, logging
from datetime import datetime, date
from contextlib import contextmanager

# Default Carbon Blue token values — used to seed theme_settings on first run
CARBON_BLUE_TOKENS = {
    "bg-base": "#0F172A",
    "bg-raised": "#141B2D",
    "bg-sunken": "#080D19",
    "surface-1": "#1E293B",
    "surface-2": "#334155",
    "surface-3": "#475569",
    "text-primary": "#F8FAFC",
    "text-secondary": "#CBD5E1",
    "text-muted": "#94A3B8",
    "text-inverse": "#0F172A",
    "border-subtle": "#334155",
    "border-default": "#475569",
    "border-strong": "#64748B",
    "action-primary": "#2563EB",
    "action-primary-hover": "#1D4EDB",
    "action-primary-active": "#1E40AF",
    "action-secondary": "#334155",
    "action-secondary-hover": "#475569",
    "accent": "#2563EB",
    "accent-subtle": "rgba(37,99,235,.12)",
    "focus-ring": "rgba(37,99,235,.5)",
    "status-success": "#10B981",
    "status-success-bg": "rgba(16,185,129,.12)",
    "status-success-border": "rgba(16,185,129,.3)",
    "status-success-text": "#10B981",
    "status-info": "#2563EB",
    "status-info-bg": "rgba(37,99,235,.12)",
    "status-info-border": "rgba(37,99,235,.3)",
    "status-info-text": "#60A5FA",
    "status-warning": "#F59E0B",
    "status-warning-bg": "rgba(245,158,11,.12)",
    "status-warning-border": "rgba(245,158,11,.3)",
    "status-warning-text": "#F59E0B",
    "status-critical": "#EF4444",
    "status-critical-bg": "rgba(239,68,68,.12)",
    "status-critical-border": "rgba(239,68,68,.3)",
    "status-critical-text": "#EF4444",
    "role-admin": "#EF4444",
    "role-manager": "#F59E0B",
    "role-supervisor": "#2563EB",
    "role-artisan": "#10B981",
    "role-team-leader": "#92400e",
    "role-team-leader-text": "#b45309",
    "role-team-leader-bg-subtle": "rgba(146,64,14,0.25)",
    "role-team-leader-border": "rgba(146,64,14,0.5)",
    "role-stores-admin": "#a855f7",
    "dispute-sup-color": "#93c5fd",
    "dispute-art-color": "#86efac",
    "badge-brown-text": "#b45309",
}

# Curated theme presets — each entry supplies only the tokens that differ from
# Carbon Blue. get_presets() merges these overrides against CARBON_BLUE_TOKENS
# to produce the full token set for each preset.
# Dark variants first, then their light counterparts.
_PRESET_OVERRIDES = [
    # ── DARK VARIANTS ──────────────────────────────────────────────────────────
    {
        "name": "Carbon Blue",
        "description": "Default dark blue — precision and clarity.",
        "tokens": {},
    },
    {
        "name": "Carbon Crimson",
        "description": "Red accent on dark — high-alert industrial feel.",
        "tokens": {
            "action-primary":        "#DC2626",
            "action-primary-hover":  "#B91C1C",
            "action-primary-active": "#991B1B",
            "action-secondary":      "#2D1515",
            "action-secondary-hover":"#3D1A1A",
            "accent":                "#DC2626",
            "accent-subtle":         "rgba(220,38,38,.12)",
            "focus-ring":            "rgba(220,38,38,.5)",
            "status-info":           "#DC2626",
            "status-info-bg":        "rgba(220,38,38,.12)",
            "status-info-border":    "rgba(220,38,38,.3)",
            "status-info-text":      "#FCA5A5",
        },
    },
    {
        "name": "Carbon Emerald",
        "description": "Green accent on dark — calm, operational, all-clear.",
        "tokens": {
            "action-primary":        "#059669",
            "action-primary-hover":  "#047857",
            "action-primary-active": "#065F46",
            "action-secondary":      "#0D2B20",
            "action-secondary-hover":"#143D2D",
            "accent":                "#059669",
            "accent-subtle":         "rgba(5,150,105,.12)",
            "focus-ring":            "rgba(5,150,105,.5)",
            "status-info":           "#059669",
            "status-info-bg":        "rgba(5,150,105,.12)",
            "status-info-border":    "rgba(5,150,105,.3)",
            "status-info-text":      "#6EE7B7",
        },
    },
    {
        "name": "Midnight",
        "description": "Deeper darks — eye comfort on long night shifts.",
        "tokens": {
            "bg-base":    "#060B14",
            "bg-raised":  "#0A1120",
            "bg-sunken":  "#030610",
            "surface-1":  "#111827",
            "surface-2":  "#1F2937",
            "surface-3":  "#374151",
            "border-subtle":  "#1F2937",
            "border-default": "#374151",
            "border-strong":  "#4B5563",
        },
    },
    {
        "name": "Slate",
        "description": "Warm grey on dark — neutral industrial, no colour cast.",
        "tokens": {
            "bg-base":    "#0F1117",
            "bg-raised":  "#161B22",
            "bg-sunken":  "#090C10",
            "surface-1":  "#1C2128",
            "surface-2":  "#2D333B",
            "surface-3":  "#444C56",
            "border-subtle":  "#2D333B",
            "border-default": "#444C56",
            "border-strong":  "#545D68",
        },
    },
    {
        "name": "Amber Workshop",
        "description": "Warm amber on dark — workshop, forge, machinery.",
        "tokens": {
            "action-primary":        "#D97706",
            "action-primary-hover":  "#B45309",
            "action-primary-active": "#92400E",
            "action-secondary":      "#2A1D06",
            "action-secondary-hover":"#3A2A0A",
            "accent":                "#D97706",
            "accent-subtle":         "rgba(217,119,6,.12)",
            "focus-ring":            "rgba(217,119,6,.5)",
            "status-info":           "#D97706",
            "status-info-bg":        "rgba(217,119,6,.12)",
            "status-info-border":    "rgba(217,119,6,.3)",
            "status-info-text":      "#FCD34D",
        },
    },
    {
        "name": "High Contrast",
        "description": "Pure black on dark — maximum legibility in dim conditions.",
        "tokens": {
            "bg-base":    "#000000",
            "bg-raised":  "#0A0A0A",
            "bg-sunken":  "#000000",
            "surface-1":  "#111111",
            "surface-2":  "#1A1A1A",
            "surface-3":  "#2A2A2A",
            "text-primary":   "#FFFFFF",
            "text-secondary": "#E5E5E5",
            "text-muted":     "#AAAAAA",
            "text-inverse":   "#000000",
            "border-subtle":  "#333333",
            "border-default": "#444444",
            "border-strong":  "#666666",
        },
    },
    {
        "name": "Ocean",
        "description": "Teal-blue on dark — calm focus, cooling energy.",
        "tokens": {
            "bg-base":    "#0C1A2E",
            "bg-raised":  "#102035",
            "bg-sunken":  "#071020",
            "surface-1":  "#1A3044",
            "surface-2":  "#234458",
            "surface-3":  "#2E5870",
            "border-subtle":  "#1A3044",
            "border-default": "#234458",
            "border-strong":  "#2E5870",
            "action-primary":        "#0891B2",
            "action-primary-hover":  "#0E7490",
            "action-primary-active": "#155E75",
            "action-secondary":      "#0C2233",
            "action-secondary-hover":"#143044",
            "accent":                "#0891B2",
            "accent-subtle":         "rgba(8,145,178,.12)",
            "focus-ring":            "rgba(8,145,178,.5)",
            "status-info":           "#0891B2",
            "status-info-bg":        "rgba(8,145,178,.12)",
            "status-info-border":    "rgba(8,145,178,.3)",
            "status-info-text":      "#7DD3FC",
        },
    },
    {
        "name": "Twilight",
        "description": "Purple on dark — shift changeover, thoughtful review.",
        "tokens": {
            "bg-base":    "#13111A",
            "bg-raised":  "#1A1724",
            "bg-sunken":  "#0A0910",
            "surface-1":  "#211D2E",
            "surface-2":  "#312B45",
            "surface-3":  "#44395C",
            "border-subtle":  "#211D2E",
            "border-default": "#312B45",
            "border-strong":  "#44395C",
            "action-primary":        "#7C3AED",
            "action-primary-hover":  "#6D28D9",
            "action-primary-active": "#5B21B6",
            "action-secondary":      "#1E1533",
            "action-secondary-hover":"#2A1D44",
            "accent":                "#7C3AED",
            "accent-subtle":         "rgba(124,58,237,.12)",
            "focus-ring":            "rgba(124,58,237,.5)",
            "status-info":           "#7C3AED",
            "status-info-bg":        "rgba(124,58,237,.12)",
            "status-info-border":    "rgba(124,58,237,.3)",
            "status-info-text":      "#C4B5FD",
        },
    },
    {
        "name": "Forest",
        "description": "Deep pine on dark — organic, sustainable, earthy.",
        "tokens": {
            "bg-base":    "#0A1208",
            "bg-raised":  "#0F1A0C",
            "bg-sunken":  "#060B05",
            "surface-1":  "#162110",
            "surface-2":  "#1E3018",
            "surface-3":  "#2A4022",
            "border-subtle":  "#162110",
            "border-default": "#1E3018",
            "border-strong":  "#2A4022",
            "action-primary":        "#16A34A",
            "action-primary-hover":  "#15803D",
            "action-primary-active": "#166534",
            "action-secondary":      "#0D2515",
            "action-secondary-hover":"#13341E",
            "accent":                "#16A34A",
            "accent-subtle":         "rgba(22,163,74,.12)",
            "focus-ring":            "rgba(22,163,74,.5)",
            "status-info":           "#16A34A",
            "status-info-bg":        "rgba(22,163,74,.12)",
            "status-info-border":    "rgba(22,163,74,.3)",
            "status-info-text":      "#86EFAC",
        },
    },

    # ── LIGHT VARIANTS ─────────────────────────────────────────────────────────
    {
        "name": "Carbon Blue — Light",
        "description": "Default blue accent on a crisp white canvas.",
        "tokens": {
            "bg-base":    "#F8FAFC",
            "bg-raised":  "#FFFFFF",
            "bg-sunken":  "#F1F5F9",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F1F5F9",
            "surface-3":  "#E2E8F0",
            "text-primary":   "#0F172A",
            "text-secondary": "#334155",
            "text-muted":     "#64748B",
            "text-inverse":   "#F8FAFC",
            "border-subtle":  "#E2E8F0",
            "border-default": "#CBD5E1",
            "border-strong":  "#94A3B8",
            "action-secondary":       "#E2E8F0",
            "action-secondary-hover": "#CBD5E1",
            "status-info-text":       "#2563EB",
            "dispute-sup-color":      "#1D4ED8",
            "dispute-art-color":      "#059669",
        },
    },
    {
        "name": "Carbon Crimson — Light",
        "description": "Red accent on a crisp white canvas.",
        "tokens": {
            "bg-base":    "#F8FAFC",
            "bg-raised":  "#FFFFFF",
            "bg-sunken":  "#F1F5F9",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F1F5F9",
            "surface-3":  "#E2E8F0",
            "text-primary":   "#0F172A",
            "text-secondary": "#334155",
            "text-muted":     "#64748B",
            "text-inverse":   "#F8FAFC",
            "border-subtle":  "#E2E8F0",
            "border-default": "#CBD5E1",
            "border-strong":  "#94A3B8",
            "action-primary":        "#DC2626",
            "action-primary-hover":  "#B91C1C",
            "action-primary-active": "#991B1B",
            "action-secondary":      "#E2E8F0",
            "action-secondary-hover":"#CBD5E1",
            "accent":                "#DC2626",
            "accent-subtle":         "rgba(220,38,38,.10)",
            "focus-ring":            "rgba(220,38,38,.4)",
            "status-info":           "#DC2626",
            "status-info-bg":        "rgba(220,38,38,.10)",
            "status-info-border":    "rgba(220,38,38,.3)",
            "status-info-text":      "#DC2626",
            "dispute-sup-color":     "#1D4ED8",
            "dispute-art-color":     "#059669",
        },
    },
    {
        "name": "Carbon Emerald — Light",
        "description": "Green accent on a crisp white canvas.",
        "tokens": {
            "bg-base":    "#F8FAFC",
            "bg-raised":  "#FFFFFF",
            "bg-sunken":  "#F1F5F9",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F1F5F9",
            "surface-3":  "#E2E8F0",
            "text-primary":   "#0F172A",
            "text-secondary": "#334155",
            "text-muted":     "#64748B",
            "text-inverse":   "#F8FAFC",
            "border-subtle":  "#E2E8F0",
            "border-default": "#CBD5E1",
            "border-strong":  "#94A3B8",
            "action-primary":        "#059669",
            "action-primary-hover":  "#047857",
            "action-primary-active": "#065F46",
            "action-secondary":      "#E2E8F0",
            "action-secondary-hover":"#CBD5E1",
            "accent":                "#059669",
            "accent-subtle":         "rgba(5,150,105,.10)",
            "focus-ring":            "rgba(5,150,105,.4)",
            "status-info":           "#059669",
            "status-info-bg":        "rgba(5,150,105,.10)",
            "status-info-border":    "rgba(5,150,105,.3)",
            "status-info-text":      "#047857",
            "dispute-sup-color":     "#1D4ED8",
            "dispute-art-color":     "#047857",
        },
    },
    {
        "name": "Midnight — Light",
        "description": "Cool blue-tinted whites — calm, focused, airy.",
        "tokens": {
            "bg-base":    "#F0F4FF",
            "bg-raised":  "#F8FAFF",
            "bg-sunken":  "#E8EEFF",
            "surface-1":  "#F8FAFF",
            "surface-2":  "#EEF2FF",
            "surface-3":  "#E0E7FF",
            "text-primary":   "#0F172A",
            "text-secondary": "#334155",
            "text-muted":     "#64748B",
            "text-inverse":   "#F0F4FF",
            "border-subtle":  "#E0E7FF",
            "border-default": "#C7D2FE",
            "border-strong":  "#A5B4FC",
            "action-secondary":       "#E0E7FF",
            "action-secondary-hover": "#C7D2FE",
            "status-info-text":       "#2563EB",
            "dispute-sup-color":      "#1D4ED8",
            "dispute-art-color":      "#059669",
        },
    },
    {
        "name": "Slate — Light",
        "description": "Warm neutral grey on white — clean, no colour cast.",
        "tokens": {
            "bg-base":    "#F9FAFB",
            "bg-raised":  "#FFFFFF",
            "bg-sunken":  "#F3F4F6",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F3F4F6",
            "surface-3":  "#E5E7EB",
            "text-primary":   "#111827",
            "text-secondary": "#374151",
            "text-muted":     "#6B7280",
            "text-inverse":   "#F9FAFB",
            "border-subtle":  "#E5E7EB",
            "border-default": "#D1D5DB",
            "border-strong":  "#9CA3AF",
            "action-secondary":       "#E5E7EB",
            "action-secondary-hover": "#D1D5DB",
            "status-info-text":       "#2563EB",
            "dispute-sup-color":      "#1D4ED8",
            "dispute-art-color":      "#059669",
        },
    },
    {
        "name": "Amber Workshop — Light",
        "description": "Warm amber on a bright workshop canvas.",
        "tokens": {
            "bg-base":    "#F8FAFC",
            "bg-raised":  "#FFFFFF",
            "bg-sunken":  "#F1F5F9",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F1F5F9",
            "surface-3":  "#E2E8F0",
            "text-primary":   "#0F172A",
            "text-secondary": "#334155",
            "text-muted":     "#64748B",
            "text-inverse":   "#F8FAFC",
            "border-subtle":  "#E2E8F0",
            "border-default": "#CBD5E1",
            "border-strong":  "#94A3B8",
            "action-primary":        "#D97706",
            "action-primary-hover":  "#B45309",
            "action-primary-active": "#92400E",
            "action-secondary":      "#E2E8F0",
            "action-secondary-hover":"#CBD5E1",
            "accent":                "#D97706",
            "accent-subtle":         "rgba(217,119,6,.10)",
            "focus-ring":            "rgba(217,119,6,.4)",
            "status-info":           "#D97706",
            "status-info-bg":        "rgba(217,119,6,.10)",
            "status-info-border":    "rgba(217,119,6,.3)",
            "status-info-text":      "#B45309",
            "dispute-sup-color":     "#1D4ED8",
            "dispute-art-color":     "#059669",
        },
    },
    {
        "name": "High Contrast — Light",
        "description": "Pure white, maximum legibility — bright outdoor use.",
        "tokens": {
            "bg-base":    "#FFFFFF",
            "bg-raised":  "#FAFAFA",
            "bg-sunken":  "#F5F5F5",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F0F0F0",
            "surface-3":  "#E0E0E0",
            "text-primary":   "#000000",
            "text-secondary": "#1A1A1A",
            "text-muted":     "#4A4A4A",
            "text-inverse":   "#FFFFFF",
            "border-subtle":  "#DDDDDD",
            "border-default": "#AAAAAA",
            "border-strong":  "#666666",
            "action-secondary":       "#E0E0E0",
            "action-secondary-hover": "#CCCCCC",
            "status-info-text":       "#2563EB",
            "dispute-sup-color":      "#1D4ED8",
            "dispute-art-color":      "#059669",
        },
    },
    {
        "name": "Ocean — Light",
        "description": "Teal accent on a bright airy canvas.",
        "tokens": {
            "bg-base":    "#F8FAFC",
            "bg-raised":  "#FFFFFF",
            "bg-sunken":  "#F1F5F9",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F1F5F9",
            "surface-3":  "#E2E8F0",
            "text-primary":   "#0F172A",
            "text-secondary": "#334155",
            "text-muted":     "#64748B",
            "text-inverse":   "#F8FAFC",
            "border-subtle":  "#E2E8F0",
            "border-default": "#CBD5E1",
            "border-strong":  "#94A3B8",
            "action-primary":        "#0891B2",
            "action-primary-hover":  "#0E7490",
            "action-primary-active": "#155E75",
            "action-secondary":      "#E2E8F0",
            "action-secondary-hover":"#CBD5E1",
            "accent":                "#0891B2",
            "accent-subtle":         "rgba(8,145,178,.10)",
            "focus-ring":            "rgba(8,145,178,.4)",
            "status-info":           "#0891B2",
            "status-info-bg":        "rgba(8,145,178,.10)",
            "status-info-border":    "rgba(8,145,178,.3)",
            "status-info-text":      "#0E7490",
            "dispute-sup-color":     "#0891B2",
            "dispute-art-color":     "#059669",
        },
    },
    {
        "name": "Twilight — Light",
        "description": "Purple accent on a bright airy canvas.",
        "tokens": {
            "bg-base":    "#F8FAFC",
            "bg-raised":  "#FFFFFF",
            "bg-sunken":  "#F1F5F9",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F1F5F9",
            "surface-3":  "#E2E8F0",
            "text-primary":   "#0F172A",
            "text-secondary": "#334155",
            "text-muted":     "#64748B",
            "text-inverse":   "#F8FAFC",
            "border-subtle":  "#E2E8F0",
            "border-default": "#CBD5E1",
            "border-strong":  "#94A3B8",
            "action-primary":        "#7C3AED",
            "action-primary-hover":  "#6D28D9",
            "action-primary-active": "#5B21B6",
            "action-secondary":      "#E2E8F0",
            "action-secondary-hover":"#CBD5E1",
            "accent":                "#7C3AED",
            "accent-subtle":         "rgba(124,58,237,.10)",
            "focus-ring":            "rgba(124,58,237,.4)",
            "status-info":           "#7C3AED",
            "status-info-bg":        "rgba(124,58,237,.10)",
            "status-info-border":    "rgba(124,58,237,.3)",
            "status-info-text":      "#7C3AED",
            "dispute-sup-color":     "#1D4ED8",
            "dispute-art-color":     "#059669",
        },
    },
    {
        "name": "Forest — Light",
        "description": "Pine green accent on a bright natural canvas.",
        "tokens": {
            "bg-base":    "#F8FAFC",
            "bg-raised":  "#FFFFFF",
            "bg-sunken":  "#F1F5F9",
            "surface-1":  "#FFFFFF",
            "surface-2":  "#F1F5F9",
            "surface-3":  "#E2E8F0",
            "text-primary":   "#0F172A",
            "text-secondary": "#334155",
            "text-muted":     "#64748B",
            "text-inverse":   "#F8FAFC",
            "border-subtle":  "#E2E8F0",
            "border-default": "#CBD5E1",
            "border-strong":  "#94A3B8",
            "action-primary":        "#16A34A",
            "action-primary-hover":  "#15803D",
            "action-primary-active": "#166534",
            "action-secondary":      "#E2E8F0",
            "action-secondary-hover":"#CBD5E1",
            "accent":                "#16A34A",
            "accent-subtle":         "rgba(22,163,74,.10)",
            "focus-ring":            "rgba(22,163,74,.4)",
            "status-info":           "#16A34A",
            "status-info-bg":        "rgba(22,163,74,.10)",
            "status-info-border":    "rgba(22,163,74,.3)",
            "status-info-text":      "#15803D",
            "dispute-sup-color":     "#1D4ED8",
            "dispute-art-color":     "#15803D",
        },
    },
]

def get_presets():
    """Return all curated presets as a list of {name, description, tokens} dicts.

    Each preset's tokens dict is a full token set — CARBON_BLUE_TOKENS merged
    with that preset's overrides. Callers can pass tokens directly to set_active_theme.
    """
    result = []
    for p in _PRESET_OVERRIDES:
        full_tokens = dict(CARBON_BLUE_TOKENS)
        full_tokens.update(p["tokens"])
        result.append({
            "name":        p["name"],
            "description": p["description"],
            "tokens":      full_tokens,
        })
    return result


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

        c.execute('''CREATE TABLE IF NOT EXISTS breakdown_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            breakdown_id INTEGER REFERENCES breakdowns(id),
            dept TEXT NOT NULL,
            mins INTEGER NOT NULL,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

        # ============================================================
        # COMPONENT TRACKING (plugin)
        # ============================================================
        c.execute('''CREATE TABLE IF NOT EXISTS component_categories (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            name                 TEXT NOT NULL UNIQUE,
            description          TEXT,
            is_wear_item         INTEGER DEFAULT 1,
            default_lifetime_days INTEGER,
            created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS equipment_components (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id            INTEGER REFERENCES equipment(id),
            category_id             INTEGER REFERENCES component_categories(id),
            name                    TEXT NOT NULL,
            location_on_machine     TEXT,
            part_number             TEXT,
            is_wear_item            INTEGER DEFAULT 1,
            estimated_lifetime_days INTEGER,
            condition               TEXT DEFAULT 'Unknown',
            estimated_age_days      INTEGER,
            estimated_remaining_days INTEGER,
            confidence_level        TEXT,
            condition_notes         TEXT,
            assessed_by             INTEGER REFERENCES users(id),
            assessed_by_name        TEXT,
            assessment_date         TEXT,
            installation_date       TEXT,
            replacement_count       INTEGER DEFAULT 0,
            failure_count           INTEGER DEFAULT 0,
            last_replacement        TEXT,
            last_failure            TEXT,
            active                  INTEGER DEFAULT 1,
            created_by              INTEGER REFERENCES users(id),
            created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS component_events (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            component_id   INTEGER REFERENCES equipment_components(id),
            event_type     TEXT NOT NULL,
            event_date     TEXT,
            work_order_ref TEXT,
            part_number    TEXT,
            supplier       TEXT,
            notes          TEXT,
            logged_by      INTEGER REFERENCES users(id),
            logged_by_name TEXT,
            logged_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # ============================================================
        # EQUIPMENT HIERARCHY (Phase 1)
        # ============================================================
        c.execute('''CREATE TABLE IF NOT EXISTS plant_nodes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id  INTEGER REFERENCES plant_nodes(id),
            name       TEXT NOT NULL,
            label      TEXT,
            sort_order INTEGER DEFAULT 0,
            active     INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes      TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS plant_node_ancestors (
            ancestor_id   INTEGER NOT NULL REFERENCES plant_nodes(id),
            descendant_id INTEGER NOT NULL REFERENCES plant_nodes(id),
            depth         INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (ancestor_id, descendant_id)
        )''')

        # Records equipment IDs that could not be auto-parsed during migration
        c.execute('''CREATE TABLE IF NOT EXISTS migration_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id TEXT,
            reason       TEXT,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved     INTEGER DEFAULT 0
        )''')

        # Single-row table holding the active theme token set
        # Custom form templates (admin-defined, role-targeted)
        c.execute('''CREATE TABLE IF NOT EXISTS form_templates (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            description  TEXT,
            target_roles TEXT DEFAULT '["admin"]',
            active       INTEGER DEFAULT 1,
            created_by   INTEGER REFERENCES users(id),
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS form_fields (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id   INTEGER NOT NULL REFERENCES form_templates(id),
            field_key     TEXT NOT NULL,
            label         TEXT NOT NULL,
            field_type    TEXT NOT NULL DEFAULT 'number',
            unit          TEXT,
            required      INTEGER DEFAULT 0,
            sort_order    INTEGER DEFAULT 0,
            is_calculated INTEGER DEFAULT 0,
            calc_hint     TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS form_submissions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id       INTEGER NOT NULL REFERENCES form_templates(id),
            submitted_by      INTEGER REFERENCES users(id),
            submitted_by_name TEXT,
            submission_date   DATE NOT NULL,
            submitted_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes             TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS form_values (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL REFERENCES form_submissions(id),
            field_key     TEXT NOT NULL,
            value         TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS theme_settings (
            id         INTEGER PRIMARY KEY CHECK (id = 1),
            theme_name TEXT    NOT NULL DEFAULT 'Carbon Blue',
            tokens     TEXT    NOT NULL,
            updated_at DATETIME,
            updated_by INTEGER REFERENCES users(id)
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
        ("requisitions",    "admin_queried",                  "ALTER TABLE requisitions ADD COLUMN admin_queried INTEGER DEFAULT 0"),
        ("requisitions",    "quote_ref",                      "ALTER TABLE requisitions ADD COLUMN quote_ref TEXT"),
        ("requisitions",    "invoice_ref",                    "ALTER TABLE requisitions ADD COLUMN invoice_ref TEXT"),
        ("requisitions",    "supplier_name",                  "ALTER TABLE requisitions ADD COLUMN supplier_name TEXT"),
        ("stock_movements", "requisition_id",                 "ALTER TABLE stock_movements ADD COLUMN requisition_id INTEGER REFERENCES requisitions(id)"),
        # v10.2 — equipment hierarchy (Phase 1)
        ("equipment",       "node_id",                       "ALTER TABLE equipment ADD COLUMN node_id INTEGER"),
        ("plant_nodes",     "equipment_id",                  "ALTER TABLE plant_nodes ADD COLUMN equipment_id TEXT"),
        # v10.2 — artisan failure type for full cross-party comparison
        ("breakdowns",      "art_failure_type",              "ALTER TABLE breakdowns ADD COLUMN art_failure_type TEXT"),
        ("breakdowns",      "sup_time_end",                  "ALTER TABLE breakdowns ADD COLUMN sup_time_end TEXT"),
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

        # Restore team_leader roles (Decision #0002)
        # Kock Divan (id:8), Strydom Francois (id:7) → team_leader (were manager)
        # Hlophe Given (id:13) → team_leader, Electrician (was artisan)
        try:
            conn.execute("UPDATE users SET role='team_leader' WHERE id IN (7,8,13)")
            conn.commit()
            logger.debug("Team leader roles restored for ids 7, 8, 13")
        except Exception as e:
            logger.debug(f"Team leader role migration: {e}")

        # Seed Boiler Daily Log checklist template
        try:
            existing = conn.execute("SELECT id FROM form_templates WHERE name='Boiler Daily Log'").fetchone()
            if not existing:
                cur = conn.execute(
                    "INSERT INTO form_templates (name, description, target_roles) VALUES (?,?,?)",
                    ("Boiler Daily Log",
                     "Daily boiler operations — TDS readings, condensate & makeup water, salt/softener, lost time.",
                     '["sawshop","admin"]')
                )
                tid = cur.lastrowid
                fields = [
                    ("b1_tds_morning",     "Boiler 1 — TDS Morning",          "number",   "ppm",  1, 0,  0, None),
                    ("b1_tds_night",       "Boiler 1 — TDS Night",            "number",   "ppm",  1, 1,  0, None),
                    ("b1_tds_highest",     "Boiler 1 — Highest TDS",          "number",   "ppm",  0, 2,  1, "max(b1_tds_morning,b1_tds_night)"),
                    ("b1_blowdowns",       "Boiler 1 — Blowdowns",            "number",   "",     1, 3,  0, None),
                    ("b2_tds_morning",     "Boiler 2 — TDS Morning",          "number",   "ppm",  1, 4,  0, None),
                    ("b2_tds_night",       "Boiler 2 — TDS Night",            "number",   "ppm",  1, 5,  0, None),
                    ("b2_tds_highest",     "Boiler 2 — Highest TDS",          "number",   "ppm",  0, 6,  1, "max(b2_tds_morning,b2_tds_night)"),
                    ("b2_blowdowns",       "Boiler 2 — Blowdowns",            "number",   "",     1, 7,  0, None),
                    ("b3_tds_morning",     "Boiler 3 — TDS Morning",          "number",   "ppm",  1, 8,  0, None),
                    ("b3_tds_night",       "Boiler 3 — TDS Night",            "number",   "ppm",  1, 9,  0, None),
                    ("b3_tds_highest",     "Boiler 3 — Highest TDS",          "number",   "ppm",  0, 10, 1, "max(b3_tds_morning,b3_tds_night)"),
                    ("b3_blowdowns",       "Boiler 3 — Blowdowns",            "number",   "",     1, 11, 0, None),
                    ("condensate_reading", "Condensate Meter Reading",         "number",   "m³", 1, 12, 0, None),
                    ("condensate_daily",   "Condensate Daily (calculated)",    "number",   "m³", 0, 13, 1, "condensate_reading - prev_day(condensate_reading)"),
                    ("makeup_reading",     "Makeup Water Meter Reading",       "number",   "m³", 1, 14, 0, None),
                    ("makeup_daily",       "Makeup Daily (calculated)",        "number",   "m³", 0, 15, 1, "makeup_reading - prev_day(makeup_reading)"),
                    ("daily_pct",          "Daily Condensate %",               "number",   "%",    0, 16, 1, "condensate_daily / makeup_daily * 100"),
                    ("rolling_7day",       "7-Day Rolling Average",            "number",   "%",    0, 17, 1, "avg(daily_pct, last 7 submissions)"),
                    ("month_pct",          "Month %",                          "number",   "%",    0, 18, 1, "month condensate / month makeup * 100"),
                    ("softener_day",       "Softener Day",                     "number",   "bags", 1, 19, 0, None),
                    ("softener_night",     "Softener Night",                   "number",   "bags", 1, 20, 0, None),
                    ("salt_bags",          "Salt Bags (50 kg)",                "number",   "bags", 1, 21, 0, None),
                    ("lost_time_mins",     "Lost Time",                        "number",   "mins", 0, 22, 0, None),
                    ("downtime_incident",  "Downtime — Incident & Remedy",     "textarea", "",     0, 23, 0, None),
                    ("operator_comments",  "Operator Comments / Items for Action", "textarea", "", 0, 24, 0, None),
                ]
                conn.executemany(
                    "INSERT INTO form_fields "
                    "(template_id,field_key,label,field_type,unit,required,sort_order,is_calculated,calc_hint) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    [(tid, f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7]) for f in fields]
                )
                conn.commit()
                logger.info("Seeded Boiler Daily Log checklist template")
        except Exception as e:
            logger.debug(f"Boiler checklist seed: {e}")

        # Seed Carbon Blue defaults into theme_settings if the table is empty
        try:
            existing = conn.execute("SELECT id FROM theme_settings WHERE id=1").fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO theme_settings (id, theme_name, tokens, updated_at) VALUES (1, ?, ?, ?)",
                    ("Carbon Blue", json.dumps(CARBON_BLUE_TOKENS), datetime.now().isoformat())
                )
                conn.commit()
                logger.debug("Theme seed: Carbon Blue defaults inserted")
        except Exception as e:
            logger.debug(f"Theme seed: {e}")

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
        ("idx_plant_node_ancestors_desc", "plant_node_ancestors", "descendant_id"),
        ("idx_plant_nodes_parent_id",     "plant_nodes",          "parent_id"),
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

def get_active_theme():
    """Return (theme_name, tokens_dict) for the active theme.

    Falls back to Carbon Blue defaults if the row is missing or tokens
    cannot be parsed — guarantees the caller always gets a usable dict.
    """
    try:
        with get_db_context() as conn:
            row = conn.execute(
                "SELECT theme_name, tokens FROM theme_settings WHERE id=1"
            ).fetchone()
        if row:
            return row['theme_name'], json.loads(row['tokens'])
    except Exception as e:
        logger.error(f"get_active_theme error: {e}", exc_info=True)
    return "Carbon Blue", dict(CARBON_BLUE_TOKENS)

def set_active_theme(theme_name, tokens, updated_by=None):
    """Persist a new theme to theme_settings (single-row upsert).

    Args:
        theme_name: Display name, e.g. 'Carbon Blue'.
        tokens: dict of CSS-property-name → value.
        updated_by: user id of the admin making the change (optional).
    """
    with get_db_context() as conn:
        conn.execute(
            """INSERT INTO theme_settings (id, theme_name, tokens, updated_at, updated_by)
               VALUES (1, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 theme_name = excluded.theme_name,
                 tokens     = excluded.tokens,
                 updated_at = excluded.updated_at,
                 updated_by = excluded.updated_by""",
            (theme_name, json.dumps(tokens), datetime.now().isoformat(), updated_by)
        )
        conn.commit()
    logger.info(f"Theme updated: {theme_name} by user_id={updated_by}")

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

# ============================================================
# EQUIPMENT HIERARCHY HELPERS (Phase 1)
# ============================================================

def add_plant_node(parent_id, name, label=None, equipment_id=None, notes=None):
    """Add a node to the plant hierarchy and update the closure table.

    parent_id=None creates a root node.
    equipment_id links this leaf node to the equipment register (leaf nodes only).
    When equipment_id is provided, equipment.node_id is also updated on that row.
    Returns the new node's integer id.
    """
    with get_db_context() as conn:
        conn.execute(
            "INSERT INTO plant_nodes (parent_id, name, label, equipment_id, notes) "
            "VALUES (?,?,?,?,?)",
            (parent_id, name, label, equipment_id, notes)
        )
        new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Every node is its own descendant at depth 0
        conn.execute(
            "INSERT INTO plant_node_ancestors (ancestor_id, descendant_id, depth) "
            "VALUES (?,?,0)",
            (new_id, new_id)
        )

        # Inherit all ancestors of the parent, each one level deeper
        if parent_id is not None:
            conn.execute("""
                INSERT INTO plant_node_ancestors (ancestor_id, descendant_id, depth)
                SELECT ancestor_id, ?, depth + 1
                FROM plant_node_ancestors
                WHERE descendant_id = ?
            """, (new_id, parent_id))

        # Link from the equipment side as well
        if equipment_id is not None:
            conn.execute(
                "UPDATE equipment SET node_id=? WHERE equipment_id=?",
                (new_id, equipment_id)
            )

        conn.commit()
        return new_id


def get_node_children(node_id):
    """Return direct children of node_id, each with a child_count.

    child_count lets the UI show an expand arrow without a second query per row.
    equipment_id is populated only on leaf nodes that represent a trackable asset.
    """
    with get_db_context() as conn:
        rows = conn.execute("""
            SELECT n.*,
                   (SELECT COUNT(*) FROM plant_nodes c
                    WHERE c.parent_id = n.id AND c.active = 1) AS child_count
            FROM plant_nodes n
            WHERE n.parent_id = ? AND n.active = 1
            ORDER BY n.sort_order, n.name
        """, (node_id,)).fetchall()
        return [dict(r) for r in rows]


def get_node_breadcrumb(node_id):
    """Return the full path from root down to node_id as an ordered list.

    Ordered root-first: [Wetmill, Romeo, Saw Heads, Head 1, Motor].
    Uses the closure table — one fast query regardless of tree depth.
    """
    with get_db_context() as conn:
        rows = conn.execute("""
            SELECT n.id, n.name, n.label, n.equipment_id, a.depth
            FROM plant_nodes n
            JOIN plant_node_ancestors a ON a.ancestor_id = n.id
            WHERE a.descendant_id = ?
            ORDER BY a.depth DESC
        """, (node_id,)).fetchall()
        return [dict(r) for r in rows]


def get_node_ancestors(node_id):
    """Return all ancestor node ids of node_id, excluding the node itself.

    Ordered from immediate parent up to root. Used for permission checks
    and subtree queries.
    """
    with get_db_context() as conn:
        rows = conn.execute("""
            SELECT ancestor_id
            FROM plant_node_ancestors
            WHERE descendant_id = ? AND depth > 0
            ORDER BY depth ASC
        """, (node_id,)).fetchall()
        return [r['ancestor_id'] for r in rows]


def get_equipment_node(equipment_id):
    """Return the plant_node record for a given equipment_id, plus its full breadcrumb.

    Returns a dict with keys: node (the plant_nodes row) and breadcrumb (root → node list).
    Returns None if this equipment has not been placed in the hierarchy yet.
    Used by breakdown forms and PM forms to show equipment context.
    """
    with get_db_context() as conn:
        node = conn.execute(
            "SELECT * FROM plant_nodes WHERE equipment_id=? AND active=1",
            (equipment_id,)
        ).fetchone()
        if not node:
            return None
        breadcrumb = get_node_breadcrumb(node['id'])
        return {'node': dict(node), 'breadcrumb': breadcrumb}


def move_node(node_id, new_parent_id):
    """Move a node and its entire subtree to a new parent.

    Updates plant_node_ancestors correctly for every node in the moved subtree.
    Validates that new_parent_id exists and is not inside the subtree being moved
    (you cannot move a folder into itself).
    Returns True on success, False if validation fails.
    """
    with get_db_context() as conn:
        # Validate new parent exists
        if new_parent_id is not None:
            exists = conn.execute(
                "SELECT id FROM plant_nodes WHERE id=? AND active=1",
                (new_parent_id,)
            ).fetchone()
            if not exists:
                logger.error(f"move_node: new_parent_id {new_parent_id} not found")
                return False
            # Cannot move into own subtree
            is_own_descendant = conn.execute(
                "SELECT 1 FROM plant_node_ancestors "
                "WHERE ancestor_id=? AND descendant_id=?",
                (node_id, new_parent_id)
            ).fetchone()
            if is_own_descendant:
                logger.error(f"move_node: cannot move node {node_id} into its own subtree")
                return False

        # Standard closure table subtree move:
        # Step 1 — delete all links from ancestors-outside-the-subtree
        #           to nodes-inside-the-subtree
        conn.execute("""
            DELETE FROM plant_node_ancestors
            WHERE descendant_id IN (
                SELECT descendant_id FROM plant_node_ancestors WHERE ancestor_id = ?
            )
            AND ancestor_id NOT IN (
                SELECT descendant_id FROM plant_node_ancestors WHERE ancestor_id = ?
            )
        """, (node_id, node_id))

        # Step 2 — update parent_id on the moved node
        conn.execute(
            "UPDATE plant_nodes SET parent_id=? WHERE id=?",
            (new_parent_id, node_id)
        )

        # Step 3 — re-insert links from new parent's ancestors to every node
        #           in the moved subtree
        if new_parent_id is not None:
            conn.execute("""
                INSERT OR IGNORE INTO plant_node_ancestors
                    (ancestor_id, descendant_id, depth)
                SELECT p.ancestor_id, s.descendant_id, p.depth + s.depth + 1
                FROM plant_node_ancestors p
                CROSS JOIN plant_node_ancestors s
                WHERE p.descendant_id = ?
                  AND s.ancestor_id   = ?
            """, (new_parent_id, node_id))

        conn.commit()
        return True


def parse_compound_id(compound_id):
    """Try to split a compound equipment ID into meaningful hierarchy segments.

    Expects a pure dash-separated hierarchical code like WM-ROM-SH1-MOT-001.
    Returns a list of segment strings on success.
    Returns None (and does NOT raise) if the format looks like a dual-reference
    code (e.g. 'BDS-001 - BE-004') or cannot be confidently parsed.

    Examples:
        'WM-ROM-SH1-MOT-001'  → ['WM', 'ROM', 'SH1', 'MOT', '001']
        'BDS-001 - BE-004'    → None   (dual-reference, not hierarchical)
        'BLR-001'             → None   (too short to imply a path)
    """
    import re
    if not compound_id:
        return None
    cid = compound_id.strip()

    # Dual-reference format contains ' - ' — not a hierarchical path
    if ' - ' in cid:
        return None

    parts = cid.split('-')
    # Need at least 3 segments to imply a meaningful path
    if len(parts) < 3:
        return None

    # Last segment should be a numeric sequence (001, 002 …)
    if not re.match(r'^\d+$', parts[-1]):
        return None

    # All non-numeric segments must look like short uppercase codes
    for p in parts[:-1]:
        if not re.match(r'^[A-Z][A-Z0-9]{0,5}$', p):
            return None

    return parts


def migrate_existing_equipment():
    """Best-effort, idempotent migration: link equipment records into the hierarchy.

    For each unlinked equipment record:
    - If compound_id parses cleanly → builds plant_nodes path and links equipment.node_id
    - If compound_id cannot be parsed → writes to migration_log, leaves node_id NULL

    Safe to call multiple times — skips records where node_id is already set.
    Prints a plain-English summary on completion.
    """
    placed = 0
    flagged = 0

    with get_db_context() as conn:
        records = conn.execute(
            "SELECT id, equipment_id, compound_id, name, area "
            "FROM equipment WHERE node_id IS NULL AND active=1"
        ).fetchall()

        if not records:
            msg = "migrate_existing_equipment: all equipment already linked"
            logger.info(msg)
            print(msg)
            return

        # Cache (parent_id, name) → node_id to avoid duplicate navigation nodes
        node_cache = {}

        def get_or_create_nav_node(parent_id, seg_name):
            """Return existing nav node id or create a new one."""
            key = (parent_id, seg_name)
            if key in node_cache:
                return node_cache[key]
            existing = conn.execute(
                "SELECT id FROM plant_nodes WHERE parent_id IS ? AND name=? "
                "AND equipment_id IS NULL",
                (parent_id, seg_name)
            ).fetchone()
            if existing:
                node_cache[key] = existing['id']
                return existing['id']
            conn.execute(
                "INSERT INTO plant_nodes (parent_id, name) VALUES (?,?)",
                (parent_id, seg_name)
            )
            nid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT OR IGNORE INTO plant_node_ancestors "
                "(ancestor_id, descendant_id, depth) VALUES (?,?,0)",
                (nid, nid)
            )
            if parent_id is not None:
                conn.execute("""
                    INSERT INTO plant_node_ancestors (ancestor_id, descendant_id, depth)
                    SELECT ancestor_id, ?, depth + 1
                    FROM plant_node_ancestors WHERE descendant_id = ?
                """, (nid, parent_id))
            conn.commit()
            node_cache[key] = nid
            return nid

        for rec in records:
            cid = rec['compound_id'] or rec['equipment_id'] or ''
            segments = parse_compound_id(cid)

            if segments is None:
                conn.execute(
                    "INSERT INTO migration_log (equipment_id, reason) VALUES (?,?)",
                    (cid,
                     f"'{cid}' does not follow the parseable hierarchy format "
                     f"(expected e.g. WM-ROM-SH1-MOT-001). Place manually via admin UI.")
                )
                conn.commit()
                flagged += 1
                continue

            # Build navigation nodes for all segments except the last (sequence number)
            parent_id = None
            for seg in segments[:-1]:
                parent_id = get_or_create_nav_node(parent_id, seg)

            # Create the leaf node linked to this equipment record
            conn.execute(
                "INSERT INTO plant_nodes (parent_id, name, equipment_id) VALUES (?,?,?)",
                (parent_id, rec['name'], cid)
            )
            leaf_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT OR IGNORE INTO plant_node_ancestors "
                "(ancestor_id, descendant_id, depth) VALUES (?,?,0)",
                (leaf_id, leaf_id)
            )
            if parent_id is not None:
                conn.execute("""
                    INSERT INTO plant_node_ancestors (ancestor_id, descendant_id, depth)
                    SELECT ancestor_id, ?, depth + 1
                    FROM plant_node_ancestors WHERE descendant_id = ?
                """, (leaf_id, parent_id))

            conn.execute(
                "UPDATE equipment SET node_id=? WHERE id=?",
                (leaf_id, rec['id'])
            )
            conn.commit()
            placed += 1

    print(f"Successfully placed: {placed} equipment records")
    if flagged:
        print(f"Flagged for review: {flagged} equipment records — see migration_log table")
    logger.info(f"migrate_existing_equipment: placed={placed}, flagged={flagged}")


if __name__ == '__main__':
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    init_db()
    seed_data()
