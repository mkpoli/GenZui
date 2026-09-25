// Shared review of the katakana form crops at atlas.mkpo.li/kata.
//
// Cloudflare Access sits in front of the whole path; the Worker still checks
// the Access token on every API call and takes the reviewer's identity from it.
// Static files (page, sprites, plate register) are served as assets.
import { createRemoteJWKSet, jwtVerify } from 'jose';
import { SQL } from './queries';

export interface Env {
  DB: D1Database;
  ASSETS: Fetcher;
  ACCESS_TEAM?: string;   // team name, as in <team>.cloudflareaccess.com
  ACCESS_AUD?: string;    // the Access application's audience tag
  DEV_ACTOR?: string;     // local development only (.dev.vars); ignored once Access is configured
}

const MAX_CHANGES = 100;
const BASE = '/kata/api';
const FLAGS = new Set(['bad-crop', 'faint']);
const FORM_ID = /^[ab]-\d{3}-([a-z]{1,2})-\d{1,2}$/;
const FAMILY_ID = /^(?:\?|x|[KH]:.|([a-z]{1,2})\.[a-z0-9-]{1,24}\??)$/u;

class Problem extends Error {
  constructor(readonly status: number, message: string) { super(message); }
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex' },
  });

let jwks: ReturnType<typeof createRemoteJWKSet> | undefined;

async function reviewer(request: Request, env: Env): Promise<string> {
  if (!env.ACCESS_TEAM || !env.ACCESS_AUD) {
    // Local development only: with Access configured, DEV_ACTOR is ignored.
    if (env.DEV_ACTOR) return env.DEV_ACTOR;
    throw new Problem(503, 'Access is not configured for this Worker.');
  }
  const token = request.headers.get('cf-access-jwt-assertion');
  if (!token) throw new Problem(401, 'Sign in through Cloudflare Access.');
  const issuer = `https://${env.ACCESS_TEAM}.cloudflareaccess.com`;
  jwks ??= createRemoteJWKSet(new URL(`${issuer}/cdn-cgi/access/certs`));
  try {
    const { payload } = await jwtVerify(token, jwks, { issuer, audience: env.ACCESS_AUD });
    if (typeof payload.email !== 'string') throw new Error('no email');
    return payload.email;
  } catch {
    throw new Problem(401, 'The Access sign-in could not be verified.');
  }
}

// One change as the client saw it. For a form, `seen` is the form's whole
// state; for a family name, its revision (null when the family is new) and name.
export type Change =
  | { field: 'family' | 'flag'; target: string; seen: { revision: number; family: string; flag: string | null }; new: string | null }
  | { field: 'label'; target: string; seen: { revision: number | null; name: string | null }; new: string | null };

const isName = (v: unknown) => typeof v === 'string' && v.trim() !== '' && v.length <= 40;

function validate(c: Change): string {
  if (c?.field === 'label') {
    const m = FAMILY_ID.exec(c.target);
    if (!m?.[1]) throw new Problem(400, `bad family id ${c.target}`);
    const s = c.seen;
    if (!s || !(s.revision === null || Number.isInteger(s.revision)) || !(s.name === null || typeof s.name === 'string'))
      throw new Problem(400, 'missing family state');
    if (c.new !== null && !isName(c.new)) throw new Problem(400, 'a family name needs 1–40 characters');
    return m[1];
  }
  if (c?.field !== 'family' && c?.field !== 'flag') throw new Problem(400, 'bad field');
  const m = FORM_ID.exec(c.target);
  if (!m) throw new Problem(400, `bad form id ${c.target}`);
  const s = c.seen;
  if (!s || !Number.isInteger(s.revision) || typeof s.family !== 'string' || !(s.flag === null || typeof s.flag === 'string'))
    throw new Problem(400, 'missing form state');
  if (c.field === 'family' && !(typeof c.new === 'string' && FAMILY_ID.test(c.new))) throw new Problem(400, 'bad family');
  if (c.field === 'flag' && c.new !== null && !FLAGS.has(c.new)) throw new Problem(400, 'bad flag');
  return m[1];
}

// Guard, log and write for one change.
function statements(db: D1Database, batch: string, actor: string, at: string, c: Change, kana: string) {
  if (c.field === 'label') {
    const rev = c.seen.revision;
    return [
      db.prepare(SQL.guardLabel).bind(c.target, rev ?? -1, c.seen.name),
      db.prepare(SQL.logEvent).bind(batch, c.target, 'label', c.seen.name, c.new, (rev ?? 0) + 1, at),
      c.new === null ? db.prepare(SQL.dropLabel).bind(c.target)
        : db.prepare(SQL.setLabel).bind(c.target, kana, c.new.trim(), actor, at),
    ];
  }
  const { revision, family, flag } = c.seen;
  const old = c.field === 'family' ? family : flag;
  const out = [
    db.prepare(SQL.guardForm).bind(c.target, revision, family, flag),
    db.prepare(SQL.logEvent).bind(batch, c.target, c.field, old, c.new, revision + 1, at),
    db.prepare(c.field === 'family' ? SQL.setFamily : SQL.setFlag).bind(c.target, c.new, actor, at),
  ];
  const delta = c.field === 'family' ? Number(c.new === '?') - Number(family === '?') : 0;
  if (delta) out.push(db.prepare(SQL.countUnsorted).bind(kana, delta));
  return out;
}

async function commit(env: Env, batch: string, actor: string, changes: Change[], undoOf: string | null = null) {
  if (!/^[\w:-]{8,80}$/.test(batch)) throw new Problem(400, 'bad batch id');
  if (!Array.isArray(changes) || !changes.length) throw new Problem(400, 'no changes');
  if (changes.length > MAX_CHANGES) throw new Problem(400, `at most ${MAX_CHANGES} changes per batch`);
  if (changes.filter(c => c?.field === 'label').length > 1) throw new Problem(400, 'one family name per batch');
  if (new Set(changes.map(c => c?.target)).size !== changes.length) throw new Problem(400, 'one change per target per batch');
  const at = new Date().toISOString();
  const db = env.DB;
  const stmts = [db.prepare(SQL.openBatch).bind(batch, actor, undoOf, at)];
  for (const c of changes) stmts.push(...statements(db, batch, actor, at, c, validate(c)));
  if (undoOf) stmts.push(db.prepare(SQL.markUndone).bind(undoOf));
  try {
    await db.batch(stmts);
  } catch (e) {
    const msg = String((e as Error).message);
    if (/UNIQUE constraint failed: batches\.id/.test(msg)) {
      const owner = await db.prepare(SQL.batchOwner).bind(batch).first<{ actor: string }>();
      if (owner?.actor === actor) return { ok: true, duplicate: true };
      throw new Problem(409, 'batch id already used');
    }
    if (/malformed JSON/.test(msg)) throw new Problem(409, '他の人が先に変更しました。再読み込みしてください。');
    throw e;
  }
  return { ok: true, at };
}

// Reverse this reviewer's latest action. It succeeds only while every row it
// touched still carries that action's revision.
async function undo(env: Env, actor: string, batch: string) {
  const last = await env.DB.prepare(SQL.lastBatch).bind(actor).first<{ id: string }>();
  if (!last) return { ok: true, undone: 0 };
  const { results: events } = await env.DB.prepare(SQL.batchEvents).bind(last.id)
    .all<{ target: string; field: Change['field']; old: string | null; new: string | null; revision: number }>();
  const formIds = events.filter(e => e.field !== 'label').map(e => e.target);
  const { results: rows } = await env.DB.prepare(SQL.formsById).bind(JSON.stringify(formIds))
    .all<{ id: string; family: string; flag: string | null; revision: number }>();
  const forms = new Map(rows.map(r => [r.id, r]));
  const changes: Change[] = [];
  for (const e of events) {
    if (e.field === 'label') {
      const row = await env.DB.prepare(SQL.labelById).bind(e.target).first<{ name: string; revision: number }>();
      if (!row || row.revision !== e.revision) throw new Problem(409, 'その後に他の変更があったため取り消せません。');
      changes.push({ field: 'label', target: e.target, seen: { revision: row.revision, name: row.name }, new: e.old });
    } else {
      const row = forms.get(e.target);
      if (!row || row.revision !== e.revision) throw new Problem(409, 'その後に他の変更があったため取り消せません。');
      changes.push({ field: e.field, target: e.target, seen: row, new: e.old });
    }
  }
  const result = await commit(env, batch, actor, changes, last.id);
  return { ...result, undone: changes.length };
}

async function body(request: Request) {
  if (Number(request.headers.get('content-length') ?? 0) > 200_000) throw new Problem(413, 'request too large');
  try { return await request.json<any>(); } catch { throw new Problem(400, 'invalid JSON'); }
}

async function api(request: Request, env: Env, path: string): Promise<Response> {
  const actor = await reviewer(request, env);
  const db = env.DB;
  if (request.method === 'GET' && path === '/summary') {
    const { results } = await db.prepare(SQL.summary).all<{ kana: string; forms: number; unsorted: number }>();
    return json({ me: actor, kana: Object.fromEntries(results.map(r => [r.kana, { forms: r.forms, unsorted: r.unsorted }])) });
  }
  const m = /^\/kana\/([a-z]{1,2})$/.exec(path);
  if (request.method === 'GET' && m) {
    const [forms, labels] = await db.batch([db.prepare(SQL.kanaForms).bind(m[1]), db.prepare(SQL.kanaLabels).bind(m[1])]);
    return json({ kana: m[1], forms: forms.results, labels: labels.results });
  }
  if (request.method === 'POST' && path === '/batch') {
    const b = await body(request);
    return json(await commit(env, String(b.batch), actor, b.changes));
  }
  if (request.method === 'POST' && path === '/undo') {
    const b = await body(request);
    return json(await undo(env, actor, String(b.batch)));
  }
  if (request.method === 'GET' && path === '/export') {
    const [forms, labels, events] = await db.batch([
      db.prepare(SQL.exportForms), db.prepare(SQL.exportLabels), db.prepare(SQL.exportEvents),
    ]);
    return json({ exported: new Date().toISOString(), by: actor, forms: forms.results, labels: labels.results, events: events.results });
  }
  throw new Problem(404, 'not found');
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname.startsWith(BASE + '/')) {
      try {
        return await api(request, env, url.pathname.slice(BASE.length));
      } catch (e) {
        if (e instanceof Problem) return json({ error: e.message }, e.status);
        console.error(e);
        return json({ error: 'internal error' }, 500);
      }
    }
    return env.ASSETS.fetch(request);
  },
} satisfies ExportedHandler<Env>;
