import asyncio
from app.core.database import engine
from sqlalchemy import text

async def update_enums():
    async with engine.begin() as conn:
        for val in ['LOGIN', 'CONFIG_CHANGE', 'MERGE_APPROVE', 'MERGE_REJECT', 'MANUAL_MERGE', 'UNMERGE', 'OPPORTUNITY_UPDATE', 'DATA_INGEST', 'MATCHING_RUN', 'REVIEW_CREATED']:
            try:
                await conn.execute(text(f"ALTER TYPE auditaction ADD VALUE IF NOT EXISTS '{val}'"))
                print(f"Added/verified: {val}")
            except Exception as e:
                print(f"Error on {val}:", e)

if __name__ == "__main__":
    asyncio.run(update_enums())
