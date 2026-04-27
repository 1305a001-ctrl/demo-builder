"""demo-builder — render static demos for given lead IDs.

Usage (one-shot):
    python -m demo_builder.main <lead_id> [<lead_id> ...]

Output:
    {OUTPUT_ROOT}/<slug>/index.html for each lead
"""
import asyncio
import logging
import sys

import sentry_sdk

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
        render_to_dir(spec)
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
