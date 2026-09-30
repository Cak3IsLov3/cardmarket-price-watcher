import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import CHECK_INTERVAL_HOURS
from app.services.checker import run_price_check
from app.services.price_guide import PriceGuideError

logger = logging.getLogger(__name__)


async def scheduled_price_check() -> None:
    try:
        result = await run_price_check()
    except PriceGuideError as exc:
        logger.error("Scheduled price check failed: %s", exc)
        return
    logger.info(
        "Price check done: checked=%d skipped=%d missing=%s alerts_sent=%d",
        result.checked,
        result.skipped,
        result.missing,
        result.alerts_sent,
    )


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        scheduled_price_check,
        "interval",
        hours=CHECK_INTERVAL_HOURS,
        next_run_time=datetime.now(timezone.utc),
        id="price_check",
        max_instances=1,
        coalesce=True,
    )
    return scheduler
