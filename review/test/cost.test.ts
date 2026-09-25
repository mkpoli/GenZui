// Every statement the Worker runs must reach its rows through an index, except
// the few listed in SCANS. Plans are checked offline against the migrated
// schema, so the test holds regardless of how many forms the database has.
import { Database } from 'bun:sqlite';
import { expect, test } from 'bun:test';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { SCANS, SQL } from '../src/queries';

const root = join(import.meta.dir, '..');

function schema() {
  const db = new Database(':memory:');
  for (const f of readdirSync(join(root, 'migrations')).sort()) db.exec(readFileSync(join(root, 'migrations', f), 'utf8'));
  return db;
}

function plan(db: Database, sql: string): string[] {
  const bind = Array.from({ length: Math.max(0, ...[...sql.matchAll(/\?(\d+)/g)].map(m => Number(m[1]))) }, () => 'x');
  return db.query(`EXPLAIN QUERY PLAN ${sql}`).all(...bind).map((r: any) => r.detail as string);
}

const bad = (detail: string) =>
  /USE TEMP B-TREE FOR ORDER BY/.test(detail) || (/^SCAN /.test(detail) && !/USING (COVERING )?INDEX/.test(detail) && !/^SCAN (json_each|CONSTANT ROW)/.test(detail));

for (const [name, sql] of Object.entries(SQL)) {
  test(`${name} reads through an index`, () => {
    const details = plan(schema(), sql);
    const problems = details.filter(bad);
    if (name in SCANS) expect(problems.length).toBeGreaterThan(0); // keep the allowance honest
    else expect(problems).toEqual([]);
  });
}

test('the Worker runs no SQL outside queries.ts', () => {
  const src = readFileSync(join(root, 'src/index.ts'), 'utf8');
  expect(src).not.toMatch(/\b(SELECT|INSERT|UPDATE|DELETE)\s/);
});

test('dropping forms_kana makes kanaForms fail', () => {
  const db = schema();
  db.exec('DROP INDEX forms_kana');
  expect(plan(db, SQL.kanaForms).some(bad)).toBe(true);
});
