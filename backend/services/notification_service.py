import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

GMAIL_SENDER = os.getenv('GMAIL_SENDER')
# Strip spaces from app password — Google app passwords are displayed with spaces
# but must be sent without them (e.g. "krbm wwzj aweg rjmw" → "krbmwwzjawerrjmw")
_raw_password = os.getenv('GMAIL_PASSWORD', '')
GMAIL_PASSWORD = _raw_password.replace(' ', '')

SMTP_WORKING = None  # None = untested, True = working, False = unavailable


def _test_smtp():
    """Lazy-test SMTP connectivity (called on first send, not at import time)."""
    global SMTP_WORKING
    if SMTP_WORKING is not None:
        return SMTP_WORKING
    try:
        if not GMAIL_SENDER or not GMAIL_PASSWORD:
            logger.warning("Gmail credentials not configured. Using simulation mode.")
            SMTP_WORKING = False
            return False
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(GMAIL_SENDER, GMAIL_PASSWORD)
        server.quit()
        SMTP_WORKING = True
        logger.info("✓ Gmail SMTP connected successfully")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.warning(
            f"⚠️ Gmail SMTP authentication failed: {e}\n"
            "Fix: Make sure you are using a Gmail App Password (not your regular password).\n"
            "Generate one at: https://myaccount.google.com/apppasswords\n"
            "Falling back to simulation mode."
        )
        SMTP_WORKING = False
        return False
    except Exception as e:
        logger.warning(f"⚠️ Gmail SMTP unavailable: {e}. Using simulation mode.")
        SMTP_WORKING = False
        return False


class NotificationService:
    def send_delay_alert(self, shipment, delay_hours):
        """Send delay alert via email or simulation"""
        if not _test_smtp():
            logger.info(f"📧 [SIM] Delay alert for {shipment.id}: {delay_hours}h")
            return {'success': True, 'simulated': True}

        try:
            subject = f"⚠️ ShipTrack Alert: Shipment {shipment.id} Delayed"
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <div style="border: 2px solid #ff6b6b; padding: 20px; border-radius: 8px;">
                  <h2 style="color: #ff6b6b;">⚠️ Shipment Delay Alert</h2>
                  <table style="width: 100%; margin: 15px 0;">
                    <tr><td style="font-weight: bold;">Shipment ID:</td><td>{shipment.id}</td></tr>
                    <tr><td style="font-weight: bold;">Route:</td><td>{shipment.origin_port_code} → {shipment.destination_port_code}</td></tr>
                    <tr><td style="font-weight: bold;">Cargo:</td><td>{shipment.cargo_type}</td></tr>
                    <tr><td style="font-weight: bold;">Delay:</td><td style="color: #ff6b6b;"><strong>{delay_hours} hours</strong></td></tr>
                    <tr><td style="font-weight: bold;">Status:</td><td>{shipment.current_status}</td></tr>
                    <tr><td style="font-weight: bold;">Original ETA:</td><td>{shipment.initial_eta}</td></tr>
                    <tr><td style="font-weight: bold;">Updated ETA:</td><td>{shipment.current_eta}</td></tr>
                  </table>
                  <p style="color: #27ae60;">✓ <strong>Action Taken:</strong> Route reoptimization triggered automatically.</p>
                  <p style="color: #7f8c8d; font-size: 12px;">ShipTrack AI System | Automated Alert</p>
                </div>
              </body>
            </html>
            """

            msg = MIMEMultipart('alternative')
            msg['From'] = GMAIL_SENDER
            msg['To'] = GMAIL_SENDER
            msg['Subject'] = subject
            msg.attach(MIMEText(html_body, 'html'))

            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_SENDER, GMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            logger.info(f"✓ Email sent for shipment {shipment.id}")
            return {'success': True, 'sent': True}
        except Exception as e:
            logger.error(f"Email failed: {e}. Using simulation mode.")
            logger.info(f"📧 [SIM] Delay alert for {shipment.id}: {delay_hours}h")
            return {'success': True, 'simulated': True, 'error': str(e)}
