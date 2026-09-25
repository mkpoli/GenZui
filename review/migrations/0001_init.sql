-- Current state: one row per form crop, one per named family, one per kana.
CREATE TABLE forms (
  id TEXT PRIMARY KEY,          -- crop file stem, e.g. a-036-ka-1
  kana TEXT NOT NULL,           -- romanised kana key, e.g. ka
  family TEXT NOT NULL,         -- family id; '?' unsorted, 'x' not a form
  flag TEXT,                    -- 'bad-crop' | 'faint' | NULL
  revision INTEGER NOT NULL DEFAULT 0,
  by TEXT,
  at TEXT
);
CREATE INDEX forms_kana ON forms(kana);

CREATE TABLE labels (
  id TEXT PRIMARY KEY,          -- family id
  kana TEXT NOT NULL,
  name TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 0,
  by TEXT,
  at TEXT
);
CREATE INDEX labels_kana ON labels(kana);

-- 48 rows, kept in step with forms so the tab bar never counts the forms table.
CREATE TABLE kana_counts (
  kana TEXT PRIMARY KEY,
  forms INTEGER NOT NULL,
  unsorted INTEGER NOT NULL
);

-- Append-only log. A batch is one reviewer action; undo is a new batch of
-- inverse events pointing at the batch it reverses.
CREATE TABLE batches (
  id TEXT PRIMARY KEY,
  actor TEXT NOT NULL,
  undo_of TEXT,
  undone INTEGER NOT NULL DEFAULT 0,
  at TEXT NOT NULL
);
CREATE INDEX batches_actor ON batches(actor, at);

CREATE TABLE events (
  id INTEGER PRIMARY KEY,
  batch TEXT NOT NULL,
  target TEXT NOT NULL,
  field TEXT NOT NULL,          -- 'family' | 'flag' | 'label'
  old TEXT,
  new TEXT,
  revision INTEGER NOT NULL,    -- target's revision after this event
  at TEXT NOT NULL
);
CREATE INDEX events_batch ON events(batch);
CREATE INDEX events_target ON events(target, id);
