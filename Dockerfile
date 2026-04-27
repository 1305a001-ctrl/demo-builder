FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

# Default command builds demos for all 'qualified' or 'new' leads in DB
# Override via `docker compose run --rm demo-builder python -m demo_builder.cli build --slug=...`
CMD ["python", "-m", "demo_builder.main"]
