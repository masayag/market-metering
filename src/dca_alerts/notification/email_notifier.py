"""Email notifier using SMTP."""

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import EmailConfig
from ..models import Report

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sends report via SMTP."""

    def __init__(self, config: EmailConfig):
        """
        Initialize the email notifier.

        Args:
            config: Email configuration
        """
        self._config = config

    def send(self, report: Report) -> bool:
        """
        Send the report via email.

        Args:
            report: The report to send

        Returns:
            True if successful, False on error
        """
        try:
            msg = self._build_message(report)
            self._send_smtp(msg)
            logger.info("Email sent to %s", self._config.recipient_email)
            return True
        except smtplib.SMTPException as e:
            logger.error("SMTP error: %s", e)
            return False
        except OSError as e:
            logger.error("Network error sending email: %s", e)
            return False

    def _build_message(self, report: Report) -> MIMEMultipart:
        """Build the email message."""
        msg = MIMEMultipart("alternative")

        subject_prefix = "[ACTION]" if report.has_buy_signals else "[INFO]"
        msg["Subject"] = (
            f"{subject_prefix} DCA Market Alert - {report.market_date.strftime('%Y-%m-%d')}"
        )
        msg["From"] = self._config.sender_email
        msg["To"] = self._config.recipient_email

        text_part = MIMEText(self._get_plain_text(report), "plain")
        html_part = MIMEText(report.to_html(), "html")

        msg.attach(text_part)
        msg.attach(html_part)

        return msg

    def _get_plain_text(self, report: Report) -> str:
        """Get plain text version without ANSI color codes for email."""
        # Create plain text version by reconstructing the report format manually
        lines = [
            f"=== DCA Market Alert - {report.market_date.strftime('%Y-%m-%d')} ===",
            "",
        ]

        for result in report.results:
            lines.extend([
                f"{result.symbol.display_name} ({result.symbol.value})",
                f"  ATH:     ${result.ath_value:,.2f} ({result.ath_date.strftime('%Y-%m-%d')})",
                f"  Current: ${result.current_price:,.2f}",
                f"  Gap:     {result.gap_percent:+.2f}%",
                f"  {result.format_recommendation_plain()}",
                "",
            ])

        # Format final action message
        if report.has_buy_signals:
            lines.append("ACTION REQUIRED: One or more indices have buy signals.")
        else:
            lines.append("No action required at this time.")

        return "\n".join(lines)

    def _send_smtp(self, msg: MIMEMultipart) -> None:
        """Send message via SMTP."""
        if self._config.use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self._config.smtp_user, self._config.smtp_password)
                server.sendmail(
                    self._config.sender_email,
                    self._config.recipient_email,
                    msg.as_string(),
                )
        else:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as server:
                server.login(self._config.smtp_user, self._config.smtp_password)
                server.sendmail(
                    self._config.sender_email,
                    self._config.recipient_email,
                    msg.as_string(),
                )
