import logging
from flask_apscheduler import APScheduler

logger = logging.getLogger(__name__)
scheduler = APScheduler()


def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()
    logger.info("Scheduler started.")


# ── Job definitions ────────────────────────────────────────────────────────────

@scheduler.task("cron", id="check_expiry_and_stock", hour=8, minute=0, misfire_grace_time=600)
def check_expiry_and_stock_job():
    """Daily job: detect expiring/low-stock medicines and send alerts."""
    from flask import current_app
    with scheduler.app.app_context():
        try:
            from services.alert_service import run_stock_and_expiry_check
            run_stock_and_expiry_check()
        except Exception as exc:
            logger.error(f"Scheduled job 'check_expiry_and_stock' failed: {exc}", exc_info=True)


@scheduler.task("cron", id="cleanup_old_prescriptions", hour=2, minute=0, day_of_week="sun")
def cleanup_old_prescriptions_job():
    """Weekly job: clean up orphan temp files (optional)."""
    with scheduler.app.app_context():
        logger.info("Running weekly prescription cleanup job.")
        # Extend here: delete old unlinked prescription files, etc.
