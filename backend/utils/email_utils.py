import logging
from flask import current_app
from flask_mail import Message

logger = logging.getLogger(__name__)


def send_email(subject: str, recipients: list, html_body: str, text_body: str = None):
    """Send an email using Flask-Mail. Fails silently in dev if not configured."""
    try:
        from extensions import mail
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=text_body or subject,
        )
        mail.send(msg)
        logger.info(f"Email sent to {recipients}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}: {e}")
        return False


def send_low_stock_alert(low_stock_items: list):
    """Send low stock alert email."""
    if not low_stock_items:
        return

    recipients = current_app.config.get("ALERT_RECIPIENTS", [])
    if not recipients:
        logger.warning("No ALERT_RECIPIENTS configured — skipping low stock email.")
        return

    rows = "".join(
        f"<tr><td>{i['medicine_name']}</td><td>{i['branch_name']}</td>"
        f"<td>{i['quantity']}</td><td>{i['low_stock_threshold']}</td></tr>"
        for i in low_stock_items
    )
    html = f"""
    <h2>⚠️ Low Stock Alert</h2>
    <p>The following medicines are running low and need to be restocked:</p>
    <table border='1' cellpadding='6' style='border-collapse:collapse;'>
      <tr><th>Medicine</th><th>Branch</th><th>Current Qty</th><th>Threshold</th></tr>
      {rows}
    </table>
    <p>Please reorder immediately.</p>
    """
    send_email("Low Stock Alert — Action Required", recipients, html)


def send_expiry_alert(expiring_items: list):
    """Send expiry alert email."""
    if not expiring_items:
        return

    recipients = current_app.config.get("ALERT_RECIPIENTS", [])
    if not recipients:
        logger.warning("No ALERT_RECIPIENTS configured — skipping expiry email.")
        return

    rows = "".join(
        f"<tr><td>{i['medicine_name']}</td><td>{i['branch_name']}</td>"
        f"<td>{i['batch_number']}</td><td>{i['expiry_date']}</td>"
        f"<td>{i['days_to_expiry']}</td><td>{i['quantity']}</td></tr>"
        for i in expiring_items
    )
    html = f"""
    <h2>🕒 Medicine Expiry Alert</h2>
    <p>The following medicines are expiring within 30 days:</p>
    <table border='1' cellpadding='6' style='border-collapse:collapse;'>
      <tr><th>Medicine</th><th>Branch</th><th>Batch</th>
          <th>Expiry Date</th><th>Days Left</th><th>Qty</th></tr>
      {rows}
    </table>
    <p>Please take action to remove or return these items.</p>
    """
    send_email("Expiry Alert — Medicines Expiring Soon", recipients, html)
