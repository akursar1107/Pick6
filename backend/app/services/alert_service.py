"""Alert service for sending notifications to administrators"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service for sending alerts to administrators.

    Supports:
    - Email alerts (when configured)
    - Logged alerts (always)
    - Future: Slack, Discord, SMS, etc.

    Requirements: 13.4
    """

    def __init__(self):
        self.smtp_host = getattr(settings, "SMTP_HOST", None)
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", None)
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        self.admin_emails = getattr(settings, "ADMIN_EMAILS", [])
        self.from_email = getattr(settings, "FROM_EMAIL", "noreply@first6.app")

        # Check if email is configured
        self.email_enabled = all(
            [self.smtp_host, self.smtp_user, self.smtp_password, self.admin_emails]
        )

        if not self.email_enabled:
            logger.warning(
                "Email alerts not configured. Set SMTP_HOST, SMTP_USER, "
                "SMTP_PASSWORD, and ADMIN_EMAILS in environment to enable."
            )

    async def send_alert(
        self,
        subject: str,
        message: str,
        severity: str = "error",
        context: Optional[dict] = None,
    ) -> bool:
        """
        Send an alert to administrators.

        Args:
            subject: Alert subject line
            message: Alert message body
            severity: Alert severity (info, warning, error, critical)
            context: Additional context data

        Returns:
            True if alert was sent successfully, False otherwise
        """
        # Always log the alert
        log_level = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }.get(severity, logging.ERROR)

        context_str = f" - Context: {context}" if context else ""
        logger.log(log_level, f"ADMIN ALERT: {subject} - {message}{context_str}")

        # Send email if configured
        if self.email_enabled:
            try:
                return await self._send_email_alert(subject, message, severity, context)
            except Exception as e:
                logger.error(f"Failed to send email alert: {str(e)}", exc_info=True)
                return False

        return True  # Alert was logged successfully

    async def _send_email_alert(
        self, subject: str, message: str, severity: str, context: Optional[dict]
    ) -> bool:
        """
        Send email alert to administrators.

        Args:
            subject: Email subject
            message: Email body
            severity: Alert severity
            context: Additional context

        Returns:
            True if email sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[First6 Alert - {severity.upper()}] {subject}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.admin_emails)

            # Create email body
            timestamp = datetime.utcnow().isoformat()

            text_body = f"""
First6 Alert
============

Severity: {severity.upper()}
Time: {timestamp}

{message}
"""

            if context:
                text_body += f"\n\nContext:\n{self._format_context(context)}"

            html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: #f44336; color: white; padding: 10px; }}
        .content {{ padding: 20px; }}
        .context {{ background-color: #f5f5f5; padding: 10px; margin-top: 20px; }}
        .severity-info {{ background-color: #2196F3; }}
        .severity-warning {{ background-color: #FF9800; }}
        .severity-error {{ background-color: #f44336; }}
        .severity-critical {{ background-color: #9C27B0; }}
    </style>
</head>
<body>
    <div class="header severity-{severity}">
        <h2>First6 Alert - {severity.upper()}</h2>
    </div>
    <div class="content">
        <p><strong>Time:</strong> {timestamp}</p>
        <p>{message}</p>
"""

            if context:
                html_body += f"""
        <div class="context">
            <h3>Context</h3>
            <pre>{self._format_context(context)}</pre>
        </div>
"""

            html_body += """
    </div>
</body>
</html>
"""

            # Attach parts
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email alert sent to {len(self.admin_emails)} administrators")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            return False

    def _format_context(self, context: dict) -> str:
        """Format context dictionary for display"""
        lines = []
        for key, value in context.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    async def send_job_failure_alert(
        self, job_name: str, error: Exception, duration: float
    ) -> bool:
        """
        Send alert for scheduled job failure.

        Args:
            job_name: Name of the failed job
            error: Exception that caused the failure
            duration: Job execution duration in seconds

        Returns:
            True if alert sent successfully
        """
        return await self.send_alert(
            subject=f"Scheduled Job Failed: {job_name}",
            message=f"The scheduled job '{job_name}' failed with error: {str(error)}",
            severity="error",
            context={
                "job_name": job_name,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "duration_seconds": f"{duration:.2f}",
            },
        )

    async def send_api_failure_alert(
        self, service: str, method: str, error: Exception, retries: int
    ) -> bool:
        """
        Send alert for API call failure after retries.

        Args:
            service: Name of the service (e.g., "nflreadpy")
            method: Method that failed
            error: Exception that caused the failure
            retries: Number of retries attempted

        Returns:
            True if alert sent successfully
        """
        return await self.send_alert(
            subject=f"API Call Failed: {service}.{method}",
            message=(
                f"API call to {service}.{method} failed after {retries} retries. "
                f"Error: {str(error)}"
            ),
            severity="error",
            context={
                "service": service,
                "method": method,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "retries": retries,
            },
        )

    async def send_validation_error_alert(
        self, entity_type: str, entity_id: str, errors: List[str]
    ) -> bool:
        """
        Send alert for data validation error.

        Args:
            entity_type: Type of entity (e.g., "game", "player")
            entity_id: ID of the entity
            errors: List of validation errors

        Returns:
            True if alert sent successfully
        """
        return await self.send_alert(
            subject=f"Data Validation Error: {entity_type}",
            message=(
                f"Data validation failed for {entity_type} {entity_id}. "
                f"Errors: {', '.join(errors)}"
            ),
            severity="warning",
            context={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "errors": errors,
            },
        )


# Global alert service instance
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """Get or create the global alert service instance"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
