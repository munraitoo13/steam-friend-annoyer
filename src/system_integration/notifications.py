"""Windows toast notifications."""

import logging

logger = logging.getLogger(__name__)


def send_notification(title: str, message: str, app_id: str = "SteamFriendAnnoyer"):
    """
    Send Windows toast notification.

    Args:
        title: Notification title
        message: Notification body
        app_id: Application ID (used for grouping)
    """
    try:
        from win10toast import ToastNotifier

        toaster = ToastNotifier()
        toaster.show_toast(
            title=title,
            msg=message,
            duration=5,
            threaded=True,
        )
    except ImportError:
        logger.warning("win10toast not available, skipping notification")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
