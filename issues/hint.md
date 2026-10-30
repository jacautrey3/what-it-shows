**Reports covered: 33** of the 412 merged into #4471.

`booking-v3` prints `MM/DD/YYYY` under its date field. People at day-first tenants type what the hint says, month first, and the form reads the value the tenant's way, day first, so the date is swapped. This path is the form, not the shared parser, so the parser fix queued for #4471 does not reach it.

- Tenants: 3, all on booking-v3 (alder.physio, copper.studio, pale.harbour) · channel `form` only · seen 2026-04-17 → 2026-09-22
- Intake tagged 18 of these `hint` and 15 `parser`.

Fix: print the hint in the order the form reads (`DD/MM/YYYY` for day-first tenants, as booking-v2 does), or read the order it prints.

Counts: `src/routes/kb/incidents/4471/problems/+page.svx`, rendered in `rendered/kb/incidents/4471/problems/index.html`.
