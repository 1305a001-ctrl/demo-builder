"""Pydantic types — one per concept."""
from typing import Literal

from pydantic import BaseModel, Field

NicheTemplate = Literal["restaurant", "clinic"]

# Variant within a niche. Each is a separate Jinja2 file under templates/<niche>/<variant>.html.j2.
#   classic  — clean, conservative, single-page brochure
#   bold     — large imagery, AOS scroll animations, gallery scroll-snap
#   premium  — parallax hero, animated stat counters, testimonial cards
TemplateVariant = Literal["classic", "bold", "premium"]


class DemoSpec(BaseModel):
    """Inputs to the renderer. Decoupled from `leads` row shape so we can
    add LLM-generated copy / scraped photos in v0.2 without touching the
    template authors.
    """
    # Identity
    slug: str  # URL-safe; used for output dir + public URL
    template: NicheTemplate
    variant: TemplateVariant = "classic"
    lead_id: str | None = None

    # Business
    name: str
    address: str | None = None
    phone: str | None = None
    city: str | None = None
    rating: float | None = None
    review_count: int | None = None
    google_maps_url: str | None = None

    # Niche-specific copy (overridable per template)
    tagline: str | None = None
    services: list[str] = Field(default_factory=list)  # used by clinic template
    cuisine_tags: list[str] = Field(default_factory=list)  # used by restaurant template
    hours: dict = Field(default_factory=dict)  # day → "09:00-22:00"

    # Brand
    primary_color: str = "#0f766e"  # default teal
    accent_color: str = "#fb923c"   # default orange

    # Hero photo URL (Unsplash placeholder for v0.1; real photo via v0.2 photo scraper)
    hero_image: str | None = None
    # Additional photos available for galleries (relative paths after photo scraping)
    gallery_images: list[str] = Field(default_factory=list)

    # Generated metadata
    booking_url: str | None = None  # placeholder; will be a Cal.com link in v0.2
