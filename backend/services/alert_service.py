import logging
from flask import current_app
from services.inventory_service import get_expiring_soon, get_low_stock
from utils.email_utils import send_low_stock_alert, send_expiry_alert

logger = logging.getLogger(__name__)


def run_stock_and_expiry_check():
    """
    Main entry point for scheduled alert job.
    Queries expiring/low-stock items and dispatches email alerts.
    """
    expiry_days = current_app.config.get("EXPIRY_ALERT_DAYS", 30)

    # ── Expiry check ──────────────────────────────────────────────────────────
    expiring = get_expiring_soon(days=expiry_days)
    if expiring:
        items_payload = [
            {
                "medicine_name": inv.medicine.name if inv.medicine else "N/A",
                "branch_name": inv.branch.name if inv.branch else "N/A",
                "batch_number": inv.batch_number,
                "expiry_date": inv.expiry_date.isoformat() if inv.expiry_date else "",
                "days_to_expiry": inv.days_to_expiry,
                "quantity": inv.quantity,
            }
            for inv in expiring
        ]
        logger.warning(f"EXPIRY ALERT: {len(expiring)} item(s) expiring within {expiry_days} days.")
        send_expiry_alert(items_payload)
    else:
        logger.info("No expiring medicines found.")

    # ── Low stock check ───────────────────────────────────────────────────────
    low_stock = get_low_stock()
    if low_stock:
        items_payload = [
            {
                "medicine_name": inv.medicine.name if inv.medicine else "N/A",
                "branch_name": inv.branch.name if inv.branch else "N/A",
                "quantity": inv.quantity,
                "low_stock_threshold": inv.low_stock_threshold,
            }
            for inv in low_stock
        ]
        logger.warning(f"LOW STOCK ALERT: {len(low_stock)} item(s) below threshold.")
        send_low_stock_alert(items_payload)
    else:
        logger.info("All medicines within acceptable stock levels.")
