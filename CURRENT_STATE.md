# CURRENT_STATE.md

## Project

**JustDo — Mill Maintenance Terminal**
Version: 10.1 (current working folder)

---

## Guiding Principle

**The Truth Comes First.**

The system exists to reveal reality objectively. It does not protect any role or hierarchy. Accountability should fall where responsibility belongs. Every decision is evaluated against this principle.

*(Decision #0001: "The Truth Comes First" replaced "The Artisan Comes First" as the primary guiding principle — see DECISIONS.md)*

---

## Project Status

Stage: **Active Development — Core System Operational**

The backend and frontend are built and running. The system is a working Flask web application served locally on port 5000.

---

## What Exists

### Backend (`app.py` — 2,556 lines)

Full Flask REST API with routes covering:

- **Users & Auth** — user list, PIN set/verify, add/deactivate/update user
- **Equipment** — CRUD, area management, hierarchy, activate/deactivate
- **PM Tasks / Jobs** — allocate, complete, suspend/unsuspend, history, checklist management
- **Breakdowns** — v10.1 flow (supervisor logs → artisan completes) + v10.2 flow (supervisor marks complete → artisan reviews times, silent dispute)
- **Job Requests** — supervisor/manager raises → admin actions
- **Dashboard** — weekly aggregate: PM compliance by area, top downtime machines, open/disputed breakdown counts, PM gauges (day/week/month)
- **Activity Log** — full audit trail
- **Recurring PM Schedule** — add/toggle/delete scheduled tasks
- **Checklist Templates** — save/load/delete named templates
- **Boiler Readings** — daily TDS, blowdowns, meter readings
- **Utility Readings** — substation hour meters, fuel, diesel
- **Reorder List** — auto-populated from parts used on tasks/breakdowns; manual add; bulk clear
- **Stores** — stock register with auto stock codes (SITE-PREFIX-DEPT-NNNNNN), movements (issue/receive/adjust/return), dept codes, import from reorder list
- **Equipment Spares** — add/delete spares per machine; export supplier-ready Excel template; import populated template
- **Suppliers** — add/deactivate supplier list
- **Requisitions (PRs)** — role-gated creation (manager/supervisor/admin), line items with planned install dates, stores_admin actions, status history, RFQ Excel export
- **Reports** — weekly Excel report (download/email), monthly archive (download/email), weekly preview data, background scheduler (Monday 06:00 task gen, 06:30 report)

### Supporting Modules
- `database.py` — SQLite schema, seed data, context manager
- `scheduler.py` — weekly PM task generation, week-start logic
- `reports.py` — weekly/monthly report generation and email
- `template_report.py` — template-based availability report

### Frontend
- `static/index.html` — single-page app (full UI)

### Data
- `mill.db` — SQLite database (live)
- `mill.log` — application log

### Infrastructure
- `requirements.txt` — Python dependencies
- `reports/` — generated Excel output files
- `templates/` — Excel templates

---

## Roles

| Role | Description | Color |
|------|-------------|-------|
| `admin` | Full system access, resolves disputes, can query/flag PRs | Red |
| `manager` | Dashboard, job requests, requisitions — sees own PR status | Amber |
| `supervisor` | Logs breakdowns, marks complete, raises job requests/PRs | Blue |
| `artisan` | Receives tasks, completes jobs, reviews breakdown times | Green |
| `sawshop` | Artisan variant | Cyan |
| `team_leader` | Appears on artisan login (brown), submits PRs, sees own status | Brown |
| `stores_admin` | Actions requisitions (4 status states), sees Req. Handling tab | Purple |
| `picker` | Store Staff login, no requisition access | Blue |
| `storeman` | Store Staff login, no requisition access | Blue |

## Requisition Status Flow

1. **submitted** — Created by manager/supervisor/team_leader
2. **pending_approval** — Stores admin set; awaiting management sign-off
3. **pending_quotation** — Stores admin set; awaiting supplier quote
4. **ordered** — Placed with supplier
5. **arrived** — Goods received in store

Admin can "Query" a PR to flag it (sets `admin_queried=1`). Queried PRs are highlighted purple in Steven's Req. Handling tab.

---

## In Progress / Known Gaps

- `TODO.md` is empty — no formal task list exists yet
- `VISION.md` is empty
- Background shift emails are commented out in the scheduler
- Dispute resolution in the v10.1 breakdown flow is functional but the v10.2 flow (artisan-review) runs in parallel — these two flows coexist and may need consolidation
- No automated tests exist
- "Steven Coetser [storeman]" (id:31) appears to be a duplicate test user — confirm with Roelof before removing

---

## How to Run

```
python app.py
```

Serves on `http://localhost:5000` (also accessible on `http://192.168.2.11:5000` on the local network).

---

## Architecture Decision Log

See `DECISIONS.md` for logged decisions.

Decision #0001 — The Truth Comes First (replaces The Artisan Comes First)
