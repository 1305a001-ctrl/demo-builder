"""Render a DemoSpec into a static HTML file."""
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from demo_builder.models import DemoSpec
from demo_builder.settings import settings

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_to_dir(spec: DemoSpec, output_root: str | None = None) -> Path:
    """Render `spec` and write `index.html` to `<output_root>/<slug>/`. Returns the dir."""
    root = Path(output_root or settings.output_root)
    out_dir = root / spec.slug
    out_dir.mkdir(parents=True, exist_ok=True)

    env = _env()
    # Variant lookup: e.g. restaurant/bold.html.j2; falls back to classic if missing
    variant_path = f"{spec.template}/{spec.variant}.html.j2"
    classic_path = f"{spec.template}/classic.html.j2"
    legacy_path = f"{spec.template}/index.html.j2"  # v0.1 default
    for path in (variant_path, classic_path, legacy_path):
        try:
            template = env.get_template(path)
            break
        except Exception:  # noqa: BLE001
            continue
    else:
        raise RuntimeError(f"no template found for {spec.template}/{spec.variant}")

    html = template.render(**spec.model_dump())

    (out_dir / "index.html").write_text(html, encoding="utf-8")
    log.info("Rendered %s → %s/index.html", spec.slug, out_dir)
    return out_dir
