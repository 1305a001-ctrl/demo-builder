# demo-builder

Phase 6c v0.1 — turns a lead row into a viewable preview website. One-shot, idempotent.

For system context: [`infra-core/docs/PHASE-6-PLAN.md`](https://github.com/1305a001-ctrl/infra-core/blob/main/docs/PHASE-6-PLAN.md).

## What it does

```
lead row (Postgres)
   │  spec.lead_to_spec()
   ▼
DemoSpec (Pydantic — name/address/palette/services/etc.)
   │  render.render_to_dir()
   ▼
/srv/data/demos/<slug>/index.html        (single-file static HTML, Tailwind via CDN)
   │  (mounted into Nginx container)
   ▼
https://demos.the2357.com/<slug>/        (publicly viewable — no Access)
```

## Templates

Two for v0.1:

| Template | Niches | Style |
|---|---|---|
| `restaurant/index.html.j2` | restaurant | Warm, food-photo hero, menu grid, reservation CTA |
| `clinic/index.html.j2`     | clinic_dental, clinic_medical, clinic_beauty | Clean, professional, services grid, Cal.com placeholder |

Both: mobile-first, Tailwind-via-CDN, Google Fonts, demo banner across the top, footer link to `the2357.com`. No build step — single HTML file per demo.

Beauty/medical/dental all use the clinic template with palette + services swapped at the spec layer.

## v0.2 deltas (next session)

- Claude API rewrites tagline + about + service descriptions from existing site / Google reviews
- Google Places photo scraper → real hero photos
- Palette extraction from photos (replace hard-coded palettes)
- Cal.com embed instead of placeholder
- Cloudflare Pages deploy automation (instead of Nginx)
- Triggered from `/leads/[id]` "Build demo" button

## Module map

```
src/demo_builder/
├── main.py          # CLI: python -m demo_builder.main <lead_id> [...]
├── settings.py      # AICORE_DB_URL, OUTPUT_ROOT, PUBLIC_BASE_URL
├── db.py            # asyncpg pool + JSONB codec; reads leads
├── models.py        # DemoSpec pydantic type
├── spec.py          # PURE — lead row → DemoSpec, niche-aware defaults
├── render.py        # Jinja2 + StrictUndefined → /srv/data/demos/<slug>/
└── templates/
    ├── restaurant/index.html.j2
    └── clinic/index.html.j2
```

## Tests

```bash
pip install -e '.[dev]'
pytest -q
```

Covers: slugify edge cases, niche → template mapping, spec passthrough, render outputs, palette in CSS, Strict undefined catches missing template vars.

## Run

```bash
docker compose -f infra-core/compose/demo-builder/docker-compose.yml run --rm demo-builder \
  python -m demo_builder.main <lead-id-1> <lead-id-2> ...
```

Output URLs print to stdout once builds complete.
