# Katakana form review

A shared page at `https://atlas.mkpo.li/kata/` for sorting the katakana forms
cut from the kana-form plates of 築島裕『平安時代訓點本論考 ヲコト點圖假名字體表』
(1986) into shape families. Reviewers select forms, move them between
families, mark faint or badly cut crops, rename families, and open any form on
its original plate.

The crops come from a book in copyright. They are never committed; they are
built locally and published only behind Cloudflare Access, to the people the
Access policy lists.

## How it works

- **Worker** (`src/index.ts`) on the route `atlas.mkpo.li/kata*`. It runs in
  front of the Worker that owns `atlas.mkpo.li`, so nothing else on that host
  changes. API calls are under `/kata/api/`; everything else is a static asset.
- **Access.** The Worker checks the Cloudflare Access token on every API call
  and records the reviewer by the email in it. Without `ACCESS_TEAM` and
  `ACCESS_AUD` it answers 503.
- **D1** holds the current state (`forms`, `labels`, `kana_counts`) and an
  append-only log (`batches`, `events`). Every change states the revision the
  reviewer saw; a change made on stale data is refused with 409. A batch sent
  twice is stored once. Undo writes the inverse changes as a new batch and
  reverses only the reviewer's own latest action.
- **Assets** (`build/kata-review/`): the page, one sprite sheet and index per
  kana, reduced plate images and the plate register.

`test/cost.test.ts` checks the query plan of every statement in
`src/queries.ts` against the migrated schema.

## Build

```sh
uv run scripts/tsukishima_plates.py             # crops, plate images, manifest
uv run scripts/katakana_review_build.py         # assets and build/kata-review-seed.sql
```

`katakana_review_build.py --history <file>` replays earlier decisions (a JSON
list of `{batch, target, field, old, new, at}`) into the seed.

## Run locally

```sh
cd review
bun install
cp .dev.vars.example .dev.vars                  # DEV_ACTOR stands in for Access
bunx wrangler d1 migrations apply katakana-review --local
bunx wrangler d1 execute katakana-review --local --file ../build/kata-review-seed.sql
devrun bunx wrangler dev --port 4191
```

Then open `http://127.0.0.1:4191/kata/`.

## Deploy

1. Create a Cloudflare Access application (Zero Trust → Access → Applications
   → Add → Self-hosted) for the domain `atlas.mkpo.li` with the path `kata`,
   and an Allow policy that lists the reviewers' emails. Keep the default
   One-time PIN login unless another identity provider is configured.
2. Copy the application's **Application Audience (AUD) Tag** and the team name
   (the `<team>` in `<team>.cloudflareaccess.com`, under Settings → Custom
   Pages or the team domain), and set them in `wrangler.jsonc` under `vars`.
3. Seed the database once:
   `bunx wrangler d1 migrations apply katakana-review --remote`, then
   `bunx wrangler d1 execute katakana-review --remote --file ../build/kata-review-seed.sql`.
   The seed replaces all rows; do not run it again after reviewing has started.
4. From a clean checkout of `main`: build the assets, then `bun run deploy`.

`GET /kata/api/export` returns the whole state and log as JSON; the page's
footer has a download link.
