"""
scheduler.py - Improved version with error handling and logging
"""

import logging
from datetime import date, timedelta
from database import get_db_context

logger = logging.getLogger(__name__)

def get_week_start(d=None):
    """Get the Monday of the current or specified week."""
    d = d or date.today()
    return d - timedelta(days=d.weekday())

# Minimum weeks between generations per frequency label
_FREQ_WEEKS = {
    'weekly': 1,
    '2weekly': 2, 'biweekly': 2,
    '3weekly': 3,
    'monthly': 4, '4weekly': 4,
    'quarterly': 13, '3monthly': 13,
    '6monthly': 26, 'semiannual': 26,
    'annual': 52, 'yearly': 52,
}

def _due_this_week(sched, week_start_date):
    """Return True if this schedule should generate a task this week."""
    freq = (sched['frequency'] or 'weekly').lower().strip()
    min_weeks = _FREQ_WEEKS.get(freq, 1)
    last = sched['last_generated']
    if not last:
        return True
    try:
        last_date = date.fromisoformat(last)
        return (week_start_date - last_date).days >= (min_weeks * 7)
    except Exception:
        return True

def generate_weekly_tasks():
    """Generate PM tasks for the current week, respecting each schedule's frequency."""
    try:
        logger.info("Generating weekly PM tasks...")

        with get_db_context() as conn:
            week_start = get_week_start()
            week_start_iso = week_start.isoformat()

            # Get all active PM schedules
            schedules = conn.execute(
                "SELECT * FROM pm_schedule WHERE active=1"
            ).fetchall()

            tasks_created = 0
            for sched in schedules:
                try:
                    # Skip if not due this week based on frequency
                    if not _due_this_week(sched, week_start):
                        continue

                    # Skip if already generated for this week
                    already = conn.execute(
                        "SELECT id FROM pm_tasks WHERE schedule_id=? AND week_start=?",
                        (sched['id'], week_start_iso)
                    ).fetchone()
                    if already:
                        continue

                    # Create task from schedule
                    conn.execute("""
                        INSERT INTO pm_tasks
                        (schedule_id, title, equipment_id, assigned_to, week_start,
                         due_date, status, task_type)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending', 'pm')
                    """, (
                        sched['id'],
                        sched['title'],
                        sched['equipment_id'],
                        sched['assigned_to'],
                        week_start_iso,
                        (week_start + timedelta(days=6)).isoformat()
                    ))

                    # Update last_generated
                    conn.execute(
                        "UPDATE pm_schedule SET last_generated=? WHERE id=?",
                        (week_start_iso, sched['id'])
                    )

                    # Add checklist items if template exists
                    if sched['checklist_template_id']:
                        task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                        template_items = conn.execute(
                            "SELECT * FROM checklist_templates WHERE task_type=? ORDER BY sort_order",
                            (sched['title'],)
                        ).fetchall()
                        for i, item in enumerate(template_items):
                            conn.execute("""
                                INSERT INTO pm_checklist_items
                                (task_id, item, sort_order)
                                VALUES (?, ?, ?)
                            """, (task_id, item['item'], i))

                    tasks_created += 1
                    logger.debug(f"Created task: {sched['title']} for week {week_start_iso}")

                except Exception as e:
                    logger.error(f"Failed to create task from schedule {sched['id']}: {e}", exc_info=True)
                    continue

            conn.commit()
            logger.info(f"Weekly task generation complete: {tasks_created} tasks created")
    
    except Exception as e:
        logger.error(f"Weekly task generation failed: {e}", exc_info=True)

def get_tasks_for_artisan(user_id):
    """Get all tasks assigned to an artisan for the current week."""
    try:
        with get_db_context() as conn:
            week_start = get_week_start().isoformat()
            
            tasks = conn.execute("""
                SELECT t.*, e.name as equip_name, e.area, e.section
                FROM pm_tasks t
                LEFT JOIN equipment e ON e.id = t.equipment_id
                WHERE t.assigned_to=? AND t.week_start=? AND t.status != 'done'
                ORDER BY t.title
            """, (user_id, week_start)).fetchall()
            
            result = []
            for t in tasks:
                td = dict(t)
                
                # Get checklist items for this task
                items = conn.execute(
                    "SELECT * FROM pm_checklist_items WHERE task_id=? ORDER BY sort_order",
                    (t['id'],)
                ).fetchall()
                td['checklist'] = [dict(i) for i in items]
                result.append(td)
            
            logger.debug(f"Retrieved {len(result)} tasks for user {user_id}")
            return result
    
    except Exception as e:
        logger.error(f"Error getting tasks for artisan {user_id}: {e}", exc_info=True)
        return []

def mark_task_done(task_id, completed_by, outcome, condition, notes, parts, checklist_states):
    """Mark a PM task as complete and record checklist/parts data."""
    try:
        from datetime import datetime
        
        logger.info(f"Marking task {task_id} as done (completed by user {completed_by})")
        
        with get_db_context() as conn:
            # Update main task
            conn.execute("""
                UPDATE pm_tasks 
                SET status='done', completed_by=?, completed_at=?,
                    outcome=?, condition_found=?, notes=? 
                WHERE id=?
            """, (
                completed_by, 
                datetime.now().isoformat(), 
                outcome, 
                condition, 
                notes, 
                task_id
            ))
            
            # Update checklist items
            for item_id, checked in checklist_states.items():
                try:
                    conn.execute(
                        "UPDATE pm_checklist_items SET checked=? WHERE id=?",
                        (1 if checked else 0, int(item_id))
                    )
                except Exception as e:
                    logger.warning(f"Failed to update checklist item {item_id}: {e}")
            
            # Add parts used
            for p in parts:
                if p.get('desc'):
                    try:
                        conn.execute(
                            "INSERT INTO pm_parts (task_id, part_desc, qty) VALUES (?,?,?)",
                            (task_id, p['desc'], p.get('qty', 1))
                        )
                        
                        # Add to reorder list
                        conn.execute(
                            "INSERT INTO reorder (part_desc, qty, source) VALUES (?,?,?)",
                            (p['desc'], p.get('qty', 1), f'PM Task #{task_id}')
                        )
                    except Exception as e:
                        logger.warning(f"Failed to record part {p.get('desc')}: {e}")
            
            conn.commit()
            logger.info(f"Task {task_id} marked as done successfully")
    
    except Exception as e:
        logger.error(f"Error marking task {task_id} as done: {e}", exc_info=True)
        raise

def get_tasks_for_week(week_start=None):
    """Get all PM tasks for a specific week."""
    try:
        week_start = (week_start or get_week_start()).isoformat()
        
        with get_db_context() as conn:
            tasks = conn.execute("""
                SELECT t.*, u.name as assigned_to_name, e.name as equip_name
                FROM pm_tasks t
                LEFT JOIN users u ON u.id = t.assigned_to
                LEFT JOIN equipment e ON e.id = t.equipment_id
                WHERE t.week_start=?
                ORDER BY t.assigned_to, t.title
            """, (week_start,)).fetchall()
            
            return [dict(t) for t in tasks]
    
    except Exception as e:
        logger.error(f"Error getting tasks for week {week_start}: {e}", exc_info=True)
        return []

def get_task_completion_rate(week_start=None):
    """Get completion statistics for a week."""
    try:
        week_start = (week_start or get_week_start()).isoformat()
        
        with get_db_context() as conn:
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as completed,
                    COUNT(DISTINCT assigned_to) as artisans
                FROM pm_tasks
                WHERE week_start=?
            """, (week_start,)).fetchone()
            
            if stats and stats['total'] > 0:
                completion_rate = (stats['completed'] / stats['total']) * 100
                return {
                    'total': stats['total'],
                    'completed': stats['completed'],
                    'pending': stats['total'] - stats['completed'],
                    'completion_rate': round(completion_rate, 1),
                    'artisans': stats['artisans']
                }
            else:
                return {
                    'total': 0,
                    'completed': 0,
                    'pending': 0,
                    'completion_rate': 0,
                    'artisans': 0
                }
    
    except Exception as e:
        logger.error(f"Error getting completion rate: {e}", exc_info=True)
        return None
