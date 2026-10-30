<script lang="ts">
  import reports from '#lib/data/reports-4471.json';
  import notes from '#lib/data/desk-notes.json';
  import { groupByCause, readAs, uniqueById, type CauseGroup, type Report } from '#lib/kb/causes';
  import { tenantOf } from '#lib/kb/locales';

  // One row per problem in the ticket, each pointing at the issue filed for it. Counts are the desk's
  // view (causes.ts as is); the desk's one-day moves stay counted under the cause they are filed by.
  type Problem = CauseGroup['cause'] | 'shift';
  let { ticket, issues }: { ticket: number; issues: Partial<Record<Problem, string>> } = $props();

  const WHAT: Record<Problem, string> = {
    parser: 'The shared parser reads the date month first; the tenant wrote it day first.',
    hint: 'booking-v3 prints MM/DD/YYYY under the date field, then reads what people type day first.',
    shift: 'Day and month are right; the whole date moves by one day.',
    unplaced: 'No tenant on file, or the tenant writes the month first: not placed.',
  };

  const all = $derived(uniqueById(reports as Report[]));
  const merged = $derived(all.filter((r) => r.mergedInto === ticket));
  const groups = $derived(groupByCause(merged, tenantOf));
  const rows = $derived([
    ...groups.map((g) => ({ problem: g.cause as Problem, count: g.reports.length, g, within: null as string | null })),
    ...groups
      .filter((g) => readAs(g, notes.oneDayMove))
      .map((g) => ({ problem: 'shift' as Problem, count: readAs(g, notes.oneDayMove), g: null, within: g.cause })),
  ]);
  const tags = (g: CauseGroup) =>
    Object.entries(g.taggedAs)
      .sort((a, b) => b[1] - a[1])
      .map(([tag, n]) => `${tag} ×${n}`)
      .join(' · ');
  const issueNo = (url: string) => `#${url.split('/').pop()}`;
</script>

<p class="sum">
  <strong>{(reports as Report[]).length}</strong> rows in the export ·
  <strong>{merged.length}</strong> reports once each ·
  <strong>{rows.length}</strong>
  {rows.length === 1 ? 'problem' : 'problems'}
</p>

<table>
  <thead>
    <tr><th>problem</th><th>reports</th><th>what goes wrong</th><th>tagged as</th><th>tenants</th><th>seen</th><th>issue</th></tr>
  </thead>
  <tbody>
    {#each rows as row (row.problem)}
      <tr>
        <td><code>{row.problem}</code></td>
        <td><strong>{row.count}</strong></td>
        <td>{WHAT[row.problem]}{#if row.within} <span class="tags">Already counted under <code>{row.within}</code>.</span>{/if}</td>
        <td class="tags">{row.g ? tags(row.g) : ''}</td>
        <td>{row.g ? row.g.tenants : ''}</td>
        <td>{row.g ? `${row.g.firstSeen} → ${row.g.lastSeen}` : ''}</td>
        <td>{#if issues[row.problem]}<a href={issues[row.problem]}>{issueNo(issues[row.problem]!)}</a>{:else}<span class="none">none yet</span>{/if}</td>
      </tr>
    {/each}
  </tbody>
</table>

<style>
  .sum { font-size: 1.1rem; }
  .tags { color: var(--muted); font-size: 0.85em; }
  .none { color: var(--warn); font-weight: 600; }
  table { display: block; overflow-x: auto; }
</style>
