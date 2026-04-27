"""demo-builder — render static demos for given lead IDs.

Usage (one-shot):
    python -m demo_builder.main <lead_id> [<lead_id> ...]

Output:
    {OUTPUT_ROOT}/<slug>/index.html for each lead
    {OUTPUT_ROOT}/<slug>/photos/[hero.jpg, photo-2.jpg, ...] when GOOGLE_MAPS_API_KEY is set
"""
import asyncio
import logging
import sys

import sentry_sdk

from demo_builder import place_photos
from demo_builder.db import db
from demo_builder.render import render_to_dir
from demo_builder.settings import settings
from demo_builder.spec import lead_to_spec

log = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.0)


async def build_for_ids(lead_ids: list[str]) -> list[str]:
    """Render demos for the given lead IDs. Returns list of public URLs."""
    leads = await db.get_leads_by_ids(lead_ids)
    if len(leads) < len(lead_ids):
        missing = set(lead_ids) - {str(lead["id"]) for lead in leads}
        log.warning("Missing leads: %s", missing)

    urls: list[str] = []
    for lead in leads:
        spec = lead_to_spec(lead)
        out_dir = render_to_dir(spec)

        # Try to fetch real photos from Google Places — replace stock hero if it works
        if lead.get("google_place_id") and settings.google_maps_api_key:
            try:
                refs = await place_photos.fetch_photo_refs(
                    lead["google_place_id"], max_refs=settings.photos_per_demo,
                )
                photos_dir = out_dir / "photos"
                photos_dir.mkdir(exist_ok=True)
                for i, ref in enumerate(refs):
                    img = await place_photos.download_photo(ref, max_width=1600)
                    if img:
                        path = photos_dir / ("hero.jpg" if i == 0 else f"photo-{i + 1}.jpg")
                        path.write_bytes(img)
                if (photos_dir / "hero.jpg").exists():
                    spec.hero_image = "photos/hero.jpg"
                    render_to_dir(spec)  # re-render with the real hero path
                    log.info("Replaced hero for %s with real Google photo", spec.slug)
            except Exception:
                log.exception("photo enrich failed for %s — keeping stock hero", spec.slug)

        url = f"{settings.public_base_url}/{spec.slug}/"
        urls.append(url)
        log.info("Demo ready: %s", url)
    return urls


async def main() -> None:
    _setup_logging()
    if len(sys.argv) < 2:
        log.error("Usage: python -m demo_builder.main <lead_id> [<lead_id> ...]")
        sys.exit(1)
    lead_ids = sys.argv[1:]
    log.info("Building demos for %d lead(s) → %s", len(lead_ids), settings.output_root)
    await db.connect()
    try:
        urls = await build_for_ids(lead_ids)
        print()
        print("Done. URLs:")
        for u in urls:
            print(f"  {u}")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
