"""Google Places photo scraping.

Two-step flow:
  1. /place/details/json with fields=photos → list of photo_reference strings
  2. /place/photo with photo_reference + maxwidth → image bytes (JPEG)

The Place Photo endpoint redirects to a signed Googleusercontent URL; we
follow redirects and read the binary response.

Costs: each /details call costs 1 SKU; each /photo call costs 1 SKU. With
$200/mo free credit on Maps Platform that's ~10k photos free.

Docs:
  https://developers.google.com/maps/documentation/places/web-service/details
  https://developers.google.com/maps/documentation/places/web-service/photos
"""
import logging

import httpx

from demo_builder.settings import settings

log = logging.getLogger(__name__)

PLACES_BASE = "https://maps.googleapis.com/maps/api/place"


async def fetch_photo_refs(google_place_id: str, max_refs: int = 5) -> list[str]:
    """Return up to max_refs photo_reference strings for a place. [] on any error."""
    if not settings.google_maps_api_key or not google_place_id:
        return []
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(
                f"{PLACES_BASE}/details/json",
                params={
                    "key": settings.google_maps_api_key,
                    "place_id": google_place_id,
                    "fields": "photos",
                },
            )
            r.raise_for_status()
            data = r.json()
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            log.warning("place_photos details %s: %s", google_place_id, data.get("status"))
            return []
        photos = (data.get("result") or {}).get("photos") or []
        return [p["photo_reference"] for p in photos[:max_refs] if p.get("photo_reference")]
    except Exception as exc:  # noqa: BLE001
        log.warning("place_photos fetch_refs %s: %s", google_place_id, exc)
        return []


async def download_photo(photo_reference: str, max_width: int = 1600) -> bytes | None:
    """Download a single photo. Returns JPEG bytes, or None on error."""
    if not settings.google_maps_api_key or not photo_reference:
        return None
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as c:
            r = await c.get(
                f"{PLACES_BASE}/photo",
                params={
                    "key": settings.google_maps_api_key,
                    "photoreference": photo_reference,
                    "maxwidth": max_width,
                },
            )
            r.raise_for_status()
            return r.content
    except Exception as exc:  # noqa: BLE001
        log.warning("place_photos download: %s", exc)
        return None
