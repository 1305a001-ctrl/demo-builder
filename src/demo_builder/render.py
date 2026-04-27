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
    template = env.get_template(f"{spec.template}/index.html.j2")
    html = template.render(**spec.model_dump())

    (out_dir / "index.html").write_text(html, encoding="utf-8")
    log.info("Rendered %s → %s/index.html", spec.slug, out_dir)
    return out_dir
