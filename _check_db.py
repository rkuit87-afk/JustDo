import sqlite3
conn = sqlite3.connect("mill.db")
conn.row_factory = sqlite3.Row
print("=== ALL PM TASKS ===")
rows = conn.execute("SELECT id, title, status, recurring, assigned_to FROM pm_tasks ORDER BY id").fetchall()
for r in rows:
    print("  id=" + str(r["id"]) + " status=" + str(r["status"]) + " recurring=" + str(r["recurring"]) + " title=" + str(r["title"]))

print("\n=== BREAKDOWNS ===")
rows = conn.execute("SELECT id, status, equip_name, log_date FROM breakdowns ORDER BY id").fetchall()
for r in rows:
    print("  id=" + str(r["id"]) + " status=" + str(r["status"]) + " equip=" + str(r["equip_name"]) + " date=" + str(r["log_date"]))

print("\n=== REORDER ===")
rows = conn.execute("SELECT id, part_desc, source FROM reorder ORDER BY id").fetchall()
for r in rows:
    print("  id=" + str(r["id"]) + " part=" + str(r["part_desc"]) + " source=" + str(r["source"]))
conn.close()
