# TODO

## Pending — Next Session

### Stores / Procurement
- [ ] **Requisition sub-tabs (Active vs History)** — Delivered orders currently show in the main working view alongside open ones. Add two sub-tabs inside the Requisitions tab: "Active" (submitted through partially_received) and "Delivered" (delivered — visible to stores_admin and admin only).
- [ ] **Team leader dashboard notification** — When a storeman receives stock linked to a requisition, the team leader or manager who raised that PR should see a card on their dashboard showing: order arrived, supplier name, what was received, quote ref and invoice number.

### Boiler Operations
- [ ] **Boiler operator daily job card** — Build a structured daily checklist for boiler operators based on the "Boiler operations" sheet in `templates/Equipment_availability_template.xlsx`. Fields with units (ppm for TDS, bags for salt/softener, minutes for downtime, cumulative m³ for meter readings). Calculated fields (highest TDS, daily condensate %, 7-day rolling average, month %) shown read-only after submission. Stores to existing `boiler_readings` table.

### Housekeeping
- [ ] **Confirm and remove duplicate user** — "Steven Coetser [storeman]" (id:31) appears to be a test duplicate. Confirm with Roelof before removing.
- [ ] **Link PR line items to stock items** — When Steven marks a requisition as "Ordered", allow him to link each line item to an existing stock record (stores_stock.id). This enables the storeman receive flow to auto-update qty_on_hand per item. Currently only items with a pre-existing stock_id link update stock on receipt.

---

## Completed

- [x] Activity log color coding — green/amber/red/blue badges based on action_type; underscores removed from display text
- [x] Req. Handling tab exclamation badge — red pill counter (❗N) on tab when queried PRs exist; bold red ❗ on queried cards
- [x] Store staff navigation fix — picker board tabs now route correctly via showScreen() prefix map
- [x] Stores tab restored to admin dashboard — Roelof/Raymond can access 🏪 Stores from their admin nav
- [x] Role system overhaul (stores_admin, team_leader, picker, storeman)
- [x] Steven's board — Req. Handling tab with aging, queried flags, status update modal
- [x] PR status states — Pending Approval, Pending Quotation, Ordered, Declined, Delivered, Partially Received
- [x] Quote ref (QT-YYYY-NNNNNN) auto-generated when ordered; supplier name captured
- [x] Invoice ref captured at delivery; searchable by storeman
- [x] Storeman receive tab — search by QT ref or PR number, full/partial delivery confirmation
- [x] Declined status with reason visible in red to requester
- [x] Admin can query/flag a PR (shows purple "Queried by Admin" badge for Steven)
- [x] Motivation reminder text on all PR forms (bold amber, CSS-driven)
- [x] Store Staff login group (pickers/storemen — purple role card)
- [x] Millwright removed from artisan sub-role filter
- [x] Color convention — Admin=red, Store=purple, Team Leader=brown
- [x] Admin board nav tab restoration fix (Roelof/Raymond no longer broken after Steven logs in)
- [x] Artisan breakdown history showing artisan name
