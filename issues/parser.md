**Reports covered: 379** of the 412 merged into #4471 (the desk's own view, `CauseTable` as exported).

The shared parser reads every date month first. All 11 tenants on file write dates day first (en-GB, en-IE, nl-NL, cs-CZ, it-IT, fr-FR, pl-PL, pt-PT, da-DK, de-DE, es-ES), so their day and month come out swapped: "Booked for 2 July. The invite says 7 February."

- Tenants: 11 · seen 2026-04-01 → 2026-10-04
- Placed by tenant locale and channel (`src/lib/kb/causes.ts`), not by intake tag: intake tagged 356 of these `parser` and 23 `hint`. The 23 came from en-US browsers at day-first tenants.
- Excludes the 33 `hint` reports (#2). Includes the 5 reports the desk read as one-day moves, as the desk files them by tenant; that problem is #3.

This is the bug the queued #4471 fix is for. It does not fix the other two.

Counts: `src/routes/kb/incidents/4471/problems/+page.svx`, rendered in `rendered/kb/incidents/4471/problems/index.html`.
