"""Read leads from Postgres."""
import json
import logging

import asyncpg

from demo_builder.settings import settings

log = logging.getLogger(__name__)


class DB:
    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("DB not connected — call connect() first")
        return self._pool

    async def connect(self) -> None:
        if not settings.aicore_db_url:
            raise RuntimeError("AICORE_DB_URL not set")
        self._pool = await asyncpg.create_pool(
            settings.aicore_db_url, min_size=1, max_size=3, init=_init_connection,
        )

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def get_lead(self, lead_id: str) -> dict | None:
        row = await self.pool.fetchrow(
            "SELECT * FROM leads WHERE id = $1::uuid",
            lead_id,
        )
        return dict(row) if row else None

    async def get_leads_by_ids(self, lead_ids: list[str]) -> list[dict]:
        rows = await self.pool.fetch(
            "SELECT * FROM leads WHERE id = ANY($1::uuid[])",
            lead_ids,
        )
        return [dict(r) for r in rows]


async def _init_connection(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


db = DB()
