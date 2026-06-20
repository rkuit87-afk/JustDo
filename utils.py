"""
utils.py - Shared utility functions used across app.py, reports.py, and template_report.py.

Consolidates duplicated patterns:
- Time string parsing and downtime calculation
- Parts-to-reorder recording
- Breakdown dispute detection
- Breakdown downtime SQL updates
- Dynamic UPDATE SQL builder
- Excel report helpers (header/data row writing, date grouping)
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================
# TIME / DOWNTIME HELPERS
# ============================================================

def time_str_to_minutes(time_str):
    """Convert an HH:MM time string to total minutes since midnight.

    Returns None if the string is empty or unparseable.
    """
    if not time_str:
        return None
    try:
        parts = str(time_str).split(':')[:2]
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return None


def time_str_to_excel(time_str):
    """Convert an HH:MM time string to an Excel time fraction (0..1).

    Returns None if the string is empty or unparseable.
    """
    mins = time_str_to_minutes(time_str)
    if mins is None:
        return None
    return mins / 1440


def calc_downtime_mins(breakdown):
    """Compute downtime minutes from a breakdown dict's start/end fields.

    Checks final → artisan → supervisor fields in priority order.
    Handles midnight crossing (negative duration wraps by +1440).
    Returns None if either time is missing or unparseable.
    """
    start = (breakdown.get('final_time_start')
             or breakdown.get('art_time_start')
             or breakdown.get('sup_time_start'))
    end = (breakdown.get('final_time_end')
           or breakdown.get('art_time_end')
           or breakdown.get('sup_time_end'))
    s = time_str_to_minutes(start)
    e = time_str_to_minutes(end)
    if s is None or e is None:
        return None
    dur = e - s
    if dur < 0:
        dur += 1440
    return dur


# ============================================================
# DISPUTE DETECTION
# ============================================================

def detect_time_dispute(art_start, art_end, sup_start, sup_end):
    """Compare artisan and supervisor times; return (disputed, dispute_field).

    All arguments are HH:MM strings (or empty/None).
    Returns:
        (False, None) if times match or both sides are empty.
        (True, comma-separated field names) if any mismatch.
    """
    disputed = False
    fields = []
    if art_start and sup_start and art_start != sup_start:
        disputed = True
        fields.append('time_start')
    if art_end and sup_end and art_end != sup_end:
        disputed = True
        fields.append('time_end')
    return disputed, ', '.join(fields) if fields else None


# ============================================================
# PARTS / REORDER RECORDING
# ============================================================

def record_parts_and_reorder(conn, parts, source_table, source_id,
                             logged_by='artisan'):
    """Insert parts used into the appropriate parts table and add to the reorder list.

    ``source_table`` is either ``'pm'`` or ``'breakdown'``.
    ``parts`` is a list of dicts with at least ``desc`` and optionally ``qty``,
    ``is_other``, ``other_note``.
    """
    for p in (parts or []):
        desc = p.get('desc')
        if not desc:
            continue
        qty = p.get('qty', 1)
        try:
            if source_table == 'pm':
                conn.execute(
                    "INSERT INTO pm_parts (task_id, part_desc, qty) VALUES (?,?,?)",
                    (source_id, desc, qty)
                )
            elif source_table == 'breakdown':
                is_other = 1 if p.get('is_other') else 0
                other_note = p.get('other_note', '')
                conn.execute(
                    "INSERT INTO breakdown_parts "
                    "(breakdown_id, part_desc, qty, logged_by, is_other, other_note) "
                    "VALUES (?,?,?,?,?,?)",
                    (source_id, desc, qty, logged_by, is_other, other_note)
                )

            # Add to reorder list (skip "other" parts that aren't stock items)
            if not p.get('is_other'):
                source_label = (f'PM Task #{source_id}' if source_table == 'pm'
                                else f'Breakdown #{source_id}')
                conn.execute(
                    "INSERT INTO reorder (part_desc, qty, source) VALUES (?,?,?)",
                    (desc, qty, source_label)
                )
        except Exception as e:
            logger.warning(f"Failed to record part '{desc}': {e}")


# ============================================================
# BREAKDOWN DOWNTIME UPDATE
# ============================================================

def build_downtime_update_params(downtime, failure_type):
    """Return the repeated parameter tuple needed by the breakdown UPDATE
    statements that split downtime into production vs maintenance columns.

    The SQL pattern is:
        production_downtime_mins  = CASE WHEN ?='Production' THEN ? ELSE 0 END,
        maintenance_downtime_mins = CASE WHEN ?='Production' THEN 0 ELSE ? END

    Returns a 4-element tuple: (ftype, downtime, ftype, downtime).
    """
    return (failure_type, downtime, failure_type, downtime)


# ============================================================
# DYNAMIC UPDATE BUILDER
# ============================================================

def build_dynamic_update(data, allowed_fields, int_fields=None):
    """Build a partial SET clause and parameter list from *data*.

    ``allowed_fields`` — iterable of column names accepted as text.
    ``int_fields`` — iterable of column names that should be cast to int.

    Returns (fields_list, params_list) where fields_list contains
    strings like ``"name=?"`` and params_list the corresponding values.
    Both lists are empty if no matching keys are present in *data*.
    """
    fields = []
    params = []
    for col in (allowed_fields or []):
        if col in data:
            fields.append(f"{col}=?")
            params.append(data[col])
    for col in (int_fields or []):
        if col in data:
            fields.append(f"{col}=?")
            params.append(int(data[col]))
    return fields, params


# ============================================================
# EXCEL REPORT HELPERS
# ============================================================

def write_header_row(ws, row, headers, style_fn=None):
    """Write a list of header values into *ws* at *row* and optionally style them.

    ``style_fn`` is called as ``style_fn(ws, row, len(headers))`` — this
    matches the signature of ``style_header`` in reports.py.

    Returns ``row + 1`` (the next available row).
    """
    for i, h in enumerate(headers, 1):
        ws.cell(row=row, column=i, value=h)
    if style_fn:
        style_fn(ws, row, len(headers))
    return row + 1


def write_data_row(ws, row, values, num_cols=None, fill=None, style_fn=None):
    """Write a list of values into *ws* at *row* and optionally style.

    ``style_fn`` is called as ``style_fn(ws, row, num_cols, fill)`` — this
    matches the signature of ``style_row`` in reports.py.

    Returns ``row + 1``.
    """
    num_cols = num_cols or len(values)
    for i, v in enumerate(values, 1):
        ws.cell(row=row, column=i, value=v if v is not None else '')
    if style_fn:
        style_fn(ws, row, num_cols, fill)
    return row + 1


def group_readings_by_date(readings, id_field='boiler_id'):
    """Group a list of DB rows by ``log_date`` and a secondary *id_field*.

    Returns a ``defaultdict(dict)`` mapping
    ``date_str -> { id_value: dict(row), ... }``.
    """
    by_date = defaultdict(dict)
    for r in readings:
        row_dict = dict(r) if not isinstance(r, dict) else r
        by_date[row_dict['log_date']][row_dict[id_field]] = row_dict
    return by_date
