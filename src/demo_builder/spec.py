"""Build a DemoSpec from a leads row.

v0.1: direct mapping + niche-derived defaults. v0.2 will plug in Claude for
LLM-rewritten copy and the photo scraper for hero images.
"""
import re
from typing import Any

from demo_builder.models import DemoSpec, NicheTemplate

# Stock hero images by niche — Unsplash queries that look professional.
# Real photos from Google Places will replace these in v0.2.
STOCK_HEROES = {
    "restaurant": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1600",
    "clinic_dental": "https://images.unsplash.com/photo-1606811971618-4486d14f3f99?w=1600",
    "clinic_medical": "https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=1600",
    "clinic_beauty": "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?w=1600",
}

# Brand palettes per niche — clean, modern. v0.2 will derive from photo extraction.
PALETTES = {
    "restaurant":      {"primary": "#7c2d12", "accent": "#f59e0b"},  # warm
    "clinic_dental":   {"primary": "#0e7490", "accent": "#06b6d4"},  # clean cyan
    "clinic_medical":  {"primary": "#0f766e", "accent": "#10b981"},  # calm teal
    "clinic_beauty":   {"primary": "#9d174d", "accent": "#ec4899"},  # rose
}

# Default service lists per clinic sub-niche. Lead-specific overrides come later.
DEFAULT_SERVICES = {
    "clinic_dental": [
        "General check-up & cleaning",
        "Teeth whitening",
        "Braces & Invisalign",
        "Root canal therapy",
        "Implants",
        "Cosmetic dentistry",
    ],
    "clinic_medical": [
        "General consultation",
        "Health screening",
        "Vaccinations",
        "Minor surgery",
        "24-hour emergency",
        "Telemedicine",
    ],
    "clinic_beauty": [
        "Facial treatments",
        "Laser therapy",
        "Skin rejuvenation",
        "Body contouring",
        "Anti-ageing",
        "Hair removal",
    ],
}

DEFAULT_CUISINE_TAGS = ["Local favourite", "Traditional", "Halal-friendly", "Family-friendly"]

DEFAULT_HOURS_RESTAURANT = {
    "Mon-Fri": "10:00 — 22:00",
    "Sat-Sun": "09:00 — 23:00",
}
DEFAULT_HOURS_CLINIC = {
    "Mon-Fri": "09:00 — 18:00",
    "Sat":     "09:00 — 13:00",
    "Sun":     "Closed",
}


def slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s[:60] or "demo"


def lead_to_spec(lead: dict[str, Any]) -> DemoSpec:
    """Map a leads row dict to a DemoSpec, filling niche-aware defaults."""
    niche = lead["niche"]
    template: NicheTemplate = "restaurant" if niche == "restaurant" else "clinic"
    palette = PALETTES.get(niche, PALETTES["clinic_medical"])

    services = DEFAULT_SERVICES.get(niche, []) if template == "clinic" else []
    cuisine_tags = DEFAULT_CUISINE_TAGS if template == "restaurant" else []
    hours = DEFAULT_HOURS_RESTAURANT if template == "restaurant" else DEFAULT_HOURS_CLINIC

    name = lead["business_name"]
    tagline = _default_tagline(niche, name)

    google_maps_url = None
    if lead.get("google_place_id"):
        google_maps_url = (
            f"https://www.google.com/maps/place/?q=place_id:{lead['google_place_id']}"
        )

    return DemoSpec(
        slug=slugify(name),
        template=template,
        lead_id=str(lead.get("id") or ""),
        name=name,
        address=lead.get("business_address"),
        phone=lead.get("business_phone"),
        city=lead.get("geo_city"),
        rating=lead.get("business_rating"),
        review_count=lead.get("business_review_count"),
        google_maps_url=google_maps_url,
        tagline=tagline,
        services=services,
        cuisine_tags=cuisine_tags,
        hours=hours,
        primary_color=palette["primary"],
        accent_color=palette["accent"],
        hero_image=STOCK_HEROES.get(niche),
        booking_url="#booking",  # placeholder until Cal.com is wired
    )


def _default_tagline(niche: str, name: str) -> str:
    """Conservative niche taglines. v0.2 replaces with LLM-rewritten copy."""
    if niche == "restaurant":
        return "Bringing you the flavours you love, freshly prepared every day."
    if niche == "clinic_dental":
        return "Modern dental care, gentle touch, lasting smiles."
    if niche == "clinic_medical":
        return "Your trusted family clinic — quality care without the wait."
    if niche == "clinic_beauty":
        return "Look your best. Feel your best. We make it effortless."
    return f"Welcome to {name}."
