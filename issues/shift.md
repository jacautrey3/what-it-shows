**Reports covered: 5** of the 412 merged into #4471.

In these the day and month are correct, but the whole date moves by one day. The desk had already marked them as one-day moves (`desk-notes.json` → `oneDayMove`: R-41202, R-41209, R-41236, R-41344, R-41620), but the kb still counted them under the parser. A day/month swap can't produce them.

- "Invite says Tuesday 12 May. Calendar says Monday 11 May."
- "Every booking in June is one day off. Only June."
- "Client in Lisbon got Tuesday. Client in Toronto got Monday. Same meeting."
- "The invite arrived before I made the booking."
- "Tuesday 6 October showed as Monday."

Tenants: 5 · seen 2026-04-02 → 2026-10-04 · all tagged `parser` by intake. These point to time zones (a date stored or sent as midnight local and read in another zone) or the summer-time change. Neither the parser fix nor the hint fix will close them.

Counts: `src/routes/kb/incidents/4471/problems/+page.svx`, rendered in `rendered/kb/incidents/4471/problems/index.html`.
