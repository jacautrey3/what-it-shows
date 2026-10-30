<script lang="ts">
  import reports from '#lib/data/reports-4471.json';
  import notes from '#lib/data/desk-notes.json';
  import { groupByCause, uniqueById, type CauseGroup, type Report } from '#lib/kb/causes';
  import { tenantOf } from '#lib/kb/locales';

  // One row per problem in the ticket, each pointing at the issue filed for it.
  let { ticket, issues }: { ticket: number; issues: Partial<Record<CauseGroup['cause'], string>> } = $props();

  const WHAT: Record<CauseGroup['cause'], string> = {
    parser: 'The shared parser reads the date month first; the tenant wrote it day first.',
    hint: 'booking-v3 prints MM/DD/YYYY under the date field, then reads what people type day first.',
    shift: 'Day and month are right; the whole date moves by one day.',
    unplaced: 'No tenant on file, or the tenant writes the month first: not placed.',
  };

  const all = $derived(uniqueById(reports as Report[]));
  const merged = $derived(all.filter((r) => r.mergedInto === ticket));
  const groups = $derived(groupByCause(merged, tenantOf, notes.oneDayMove));
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
  <strong>{groups.length}</strong>
  {groups.length === 1 ? 'problem' : 'problems'}
</p>

<table>
  <thead>
    <tr><th>problem</th><th>reports</th><th>what goes wrong</th><th>tagged as</th><th>tenants</th><th>seen</th><th>issue</th></tr>
  </thead>
  <tbody>
    {#each groups as g (g.cause)}
      <tr>
        <td><code>{g.cause}</code></td>
        <td><strong>{g.reports.length}</strong></td>
        <td>{WHAT[g.cause]}</td>
        <td class="tags">{tags(g)}</td>
        <td>{g.tenants}</td>
        <td>{g.firstSeen} → {g.lastSeen}</td>
        <td>{#if issues[g.cause]}<a href={issues[g.cause]}>{issueNo(issues[g.cause]!)}</a>{:else}<span class="none">none yet</span>{/if}</td>
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
