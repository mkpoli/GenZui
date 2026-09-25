// Every SQL statement the Worker runs. test/cost.test.ts runs EXPLAIN QUERY
// PLAN over each one, so a statement added elsewhere escapes that check.

export const SQL = {
  summary: 'SELECT kana, forms, unsorted FROM kana_counts',
  kanaForms: 'SELECT id, family, flag, revision, by, at FROM forms WHERE kana = ?1',
  kanaLabels: 'SELECT id, name, revision FROM labels WHERE kana = ?1',

  // Batch writes. A guard raises "malformed JSON" when the row is not in the
  // state the client saw, which rolls back the whole D1 batch.
  openBatch: 'INSERT INTO batches (id, actor, undo_of, at) VALUES (?1, ?2, ?3, ?4)',
  guardForm:
    "SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM forms WHERE id = ?1 AND revision = ?2 AND family IS ?3 AND flag IS ?4) THEN json_extract('conflict', '$') END",
  guardLabel:
    "SELECT CASE WHEN COALESCE((SELECT revision FROM labels WHERE id = ?1), -1) IS NOT ?2 THEN json_extract('conflict', '$') END",
  logEvent: 'INSERT INTO events (batch, target, field, old, new, revision, at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)',
  setFamily: 'UPDATE forms SET family = ?2, revision = revision + 1, by = ?3, at = ?4 WHERE id = ?1',
  setFlag: 'UPDATE forms SET flag = ?2, revision = revision + 1, by = ?3, at = ?4 WHERE id = ?1',
  countUnsorted: 'UPDATE kana_counts SET unsorted = unsorted + ?2 WHERE kana = ?1',
  setLabel:
    'INSERT INTO labels (id, kana, name, revision, by, at) VALUES (?1, ?2, ?3, 1, ?4, ?5) ' +
    'ON CONFLICT (id) DO UPDATE SET name = excluded.name, revision = labels.revision + 1, by = excluded.by, at = excluded.at',
  dropLabel: 'DELETE FROM labels WHERE id = ?1',

  batchOwner: 'SELECT actor FROM batches WHERE id = ?1',
  // The reviewer's latest action still in force.
  lastBatch: 'SELECT id FROM batches WHERE actor = ?1 AND undo_of IS NULL AND undone = 0 ORDER BY at DESC LIMIT 1',
  batchEvents: 'SELECT target, field, old, new, revision FROM events WHERE batch = ?1 ORDER BY id DESC',
  markUndone: 'UPDATE batches SET undone = 1 WHERE id = ?1',
  // Current rows for an undo; ?1 is a JSON array of at most MAX_CHANGES ids.
  formsById: 'SELECT id, family, flag, revision FROM forms WHERE id IN (SELECT value FROM json_each(?1))',
  labelById: 'SELECT id, name, revision FROM labels WHERE id = ?1',

  // Export of the whole state; one full read of each table by design.
  exportForms: 'SELECT id, family, flag, revision, by, at FROM forms',
  exportLabels: 'SELECT id, name, revision, by, at FROM labels',
  exportEvents:
    'SELECT e.id, e.batch, b.actor, b.undo_of, e.target, e.field, e.old, e.new, e.at FROM events e JOIN batches b ON b.id = e.batch ORDER BY e.id',
} as const;

// Statements allowed to scan a table, with the reason.
export const SCANS: Record<string, string> = {
  summary: 'kana_counts has one row per kana (48)',
  exportForms: 'full export on request',
  exportLabels: 'full export on request',
  exportEvents: 'full export on request',
};
