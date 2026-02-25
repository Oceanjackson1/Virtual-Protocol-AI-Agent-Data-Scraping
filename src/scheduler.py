"""
Scheduler: runs the scraper at configured intervals.
"""

import asyncio
import logging
import time

import schedule

from .scraper import load_config
from .main import run_once

logger = logging.getLogger("acp-scheduler")


def _job(config: dict):
    logger.info("Scheduled scrape starting...")
    try:
        filepath = asyncio.run(run_once(config))
        logger.info("Scheduled scrape complete: %s", filepath)
    except Exception as e:
        logger.error("Scheduled scrape failed: %s", e, exc_info=True)


def start_scheduler():
    config = load_config()
    sched_cfg = config.get("schedule", {})

    if not sched_cfg.get("enabled", False):
        logger.info("Scheduler is disabled in config. Running once.")
        _job(config)
        return

    interval_hours = sched_cfg.get("interval_hours", 24)
    run_at = sched_cfg.get("run_at", "08:00")

    if interval_hours == 24:
        schedule.every().day.at(run_at).do(_job, config)
        logger.info("Scheduled daily at %s", run_at)
    else:
        schedule.every(interval_hours).hours.do(_job, config)
        logger.info("Scheduled every %d hours", interval_hours)

    logger.info("Running initial scrape now...")
    _job(config)

    logger.info("Scheduler running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    start_scheduler()
