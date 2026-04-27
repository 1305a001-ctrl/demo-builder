"""Tests for spec generation + render. Pure-function, no DB."""
import tempfile
from pathlib import Path

import pytest

from demo_builder.models import DemoSpec
from demo_builder.render import render_to_dir
from demo_builder.spec import lead_to_spec, slugify


def _lead(**ov) -> dict:
    base = {
        "id": "abc-123",
        "niche": "restaurant",
        "business_name": "Kedai Makanan Nam Heong",
        "business_address": "2, Jalan Bandar Timah, 30000 Ipoh, Perak",
        "business_phone": "+60 5-254 2999",
        "geo_city": "Ipoh",
        "business_rating": 4.0,
        "business_review_count": 5016,
        "google_place_id": "ChIJabc123",
    }
    base.update(ov)
    return base


# ─── Slugify ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name,expected", [
    ("Kedai Makanan Nam Heong", "kedai-makanan-nam-heong"),
    ("Restoran New Holly Wood", "restoran-new-holly-wood"),
    ("Klinik Pergigian K Dental 牙科诊所", "klinik-pergigian-k-dental"),
    ("AAA - Cafe & Bar", "aaa-cafe-bar"),
    ("", "demo"),
])
def test_slugify(name, expected):
    assert slugify(name) == expected


# ─── Spec generation ──────────────────────────────────────────────────────────


def test_restaurant_spec_uses_restaurant_template():
    spec = lead_to_spec(_lead())
    assert spec.template == "restaurant"
    assert spec.cuisine_tags  # populated
    assert not spec.services  # not relevant for restaurant


def test_dental_spec_uses_clinic_template_with_dental_services():
    spec = lead_to_spec(_lead(niche="clinic_dental", business_name="Chin Dental Clinic"))
    assert spec.template == "clinic"
    assert "Teeth whitening" in spec.services
    assert spec.primary_color == "#0e7490"  # dental cyan
    assert not spec.cuisine_tags


def test_beauty_spec_uses_clinic_template_with_beauty_services():
    spec = lead_to_spec(_lead(niche="clinic_beauty", business_name="Believe Face & Body Center"))
    assert spec.template == "clinic"
    assert "Facial treatments" in spec.services
    assert spec.primary_color == "#9d174d"  # beauty rose


def test_spec_passes_through_ratings_and_address():
    spec = lead_to_spec(_lead())
    assert spec.rating == 4.0
    assert spec.review_count == 5016
    assert "Ipoh" in (spec.address or "")
    assert "google.com/maps" in (spec.google_maps_url or "")


def test_spec_handles_missing_optional_fields():
    spec = lead_to_spec(_lead(
        business_address=None, business_phone=None,
        business_rating=None, business_review_count=None,
        google_place_id=None,
    ))
    assert spec.address is None
    assert spec.phone is None
    assert spec.rating is None
    assert spec.google_maps_url is None  # no place_id → no maps URL


# ─── Render ───────────────────────────────────────────────────────────────────


def test_render_restaurant_writes_index_html():
    with tempfile.TemporaryDirectory() as d:
        spec = lead_to_spec(_lead())
        out = render_to_dir(spec, output_root=d)
        index = out / "index.html"
        assert index.exists()
        html = index.read_text()
        assert "Kedai Makanan Nam Heong" in html
        assert "Ipoh" in html
        assert "+60 5-254 2999" in html
        assert "5,016" in html  # formatted review count
        assert "reviews" in html
        assert "4.0" in html
        # Tagline + CTAs present
        assert "Book a table" in html
        # Sanity: HTML well-formed shape
        assert html.startswith("<!DOCTYPE html>")


def test_render_clinic_writes_services_html():
    with tempfile.TemporaryDirectory() as d:
        spec = lead_to_spec(_lead(niche="clinic_dental", business_name="Chin Dental Clinic"))
        out = render_to_dir(spec, output_root=d)
        html = (out / "index.html").read_text()
        assert "Chin Dental Clinic" in html
        assert "Teeth whitening" in html
        assert "Book an appointment" in html


def test_render_writes_into_slug_directory():
    with tempfile.TemporaryDirectory() as d:
        spec = lead_to_spec(_lead())
        out = render_to_dir(spec, output_root=d)
        assert out == Path(d) / "kedai-makanan-nam-heong"


def test_render_uses_brand_palette_in_css():
    with tempfile.TemporaryDirectory() as d:
        spec = lead_to_spec(_lead(
            niche="clinic_beauty",
            business_name="Believe Face & Body Center",
        ))
        html = render_to_dir(spec, output_root=d).joinpath("index.html").read_text()
        assert "#9d174d" in html  # beauty primary
        assert "#ec4899" in html  # beauty accent


def test_render_strict_undefined_raises_on_missing_var():
    """If we add a template var that doesn't exist on DemoSpec, the test must blow up."""
    bad_spec = DemoSpec(
        slug="x", template="restaurant", name="x",
    )
    # Direct render must succeed because all template vars are mapped on DemoSpec
    with tempfile.TemporaryDirectory() as d:
        render_to_dir(bad_spec, output_root=d)
