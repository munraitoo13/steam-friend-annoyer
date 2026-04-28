"""Steam client service with thread-safe operations."""

import logging
import random
import threading
from typing import Any, Callable, Dict, Optional, Set

from steam.client import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg

from src.persistence.storage import StorageManager

logger = logging.getLogger(__name__)


class SteamService:
    """
    Thread-safe Steam client wrapper.
    Runs in background thread, communicates via callbacks.
    """

    def __init__(self, storage: StorageManager):
        self._storage = storage
        self._client: Optional[SteamClient] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._latest_login_key: Optional[str] = None

        # State tracking
        self._friend_game_ids: Dict[
            int, Optional[int]
        ] = {}  # friend_id -> current_game_id
        self._sent_messages: Set[int] = (
            set()
        )  # set of friend_ids we've sent message to in current session

        # Callbacks
        self._cb_on_connected: Optional[Callable] = None
        self._cb_on_disconnected: Optional[Callable] = None
        self._cb_on_friend_state_changed: Optional[
            Callable[[int, Optional[int]], Any]
        ] = None
        self._cb_on_message_sent: Optional[Callable[[int, str], Any]] = None
        self._cb_on_error: Optional[Callable[[str], Any]] = None

    def set_on_connected(self, callback: Callable):
        """Set connection callback."""
        self._cb_on_connected = callback

    def set_on_disconnected(self, callback: Callable):
        """Set disconnection callback."""
        self._cb_on_disconnected = callback

    def set_on_friend_state_changed(
        self, callback: Callable[[int, Optional[int]], Any]
    ):
        """Set friend state change callback (friend_id, game_id)."""
        self._cb_on_friend_state_changed = callback

    def set_on_message_sent(self, callback: Callable[[int, str], Any]):
        """Set message sent callback (friend_id, message)."""
        self._cb_on_message_sent = callback

    def set_on_error(self, callback: Callable[[str], Any]):
        """Set error callback."""
        self._cb_on_error = callback

    def start(
        self,
        username: str,
        password: str,
        session: Optional[Dict[str, Any]] = None,
        guard_code: Optional[str] = None,
    ) -> bool:
        """
        Start Steam client in background thread.
        Returns True if started, False if already running or error.
        """
        with self._lock:
            if self._running:
                logger.debug(
                    "SteamService.start ignored because service is already running"
                )
                return False

            logger.debug(
                "SteamService.start requested for username=%s session_cached=%s guard_code=%s",
                username,
                bool(session),
                bool(guard_code),
            )
            self._running = True
            self._thread = threading.Thread(
                target=self._run_client,
                args=(username, password, session, guard_code),
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self):
        """Stop Steam client."""
        logger.debug("SteamService.stop requested")
        with self._lock:
            self._running = False

        if self._client is not None:
            try:
                self._client.disconnect()
            except Exception:
                pass

        if self._thread:
            self._thread.join(timeout=5)

    def is_running(self) -> bool:
        """Check if service is running."""
        with self._lock:
            return self._running and self._client is not None and self._client.connected

    def _run_client(
        self,
        username: str,
        password: str,
        session: Optional[Dict[str, Any]],
        guard_code: Optional[str],
    ):
        """Run the Steam client (called in background thread)."""
        try:
            logger.debug("Creating SteamClient instance in background thread")
            # SteamClient/gevent objects must be created and used in the same thread.
            self._client = SteamClient()

            self._client.on(self._client.EVENT_NEW_LOGIN_KEY, self._on_new_login_key)

            # Setup event handlers
            self._client.on(self._client.EVENT_LOGGED_ON, self._on_logged_on)
            self._client.on(
                self._client.EVENT_DISCONNECTED, self._on_client_disconnected
            )
            self._client.on(EMsg.ClientPersonaState, self._handle_persona_state)
            self._client.friends.on(
                self._client.friends.EVENT_READY, self._on_friends_ready
            )

            # Attempt login using GUI-provided credentials and optional guard code.
            if session and session.get("login_key"):
                logger.debug("Attempting Steam login using cached login key")
                result = self._client.login(username, login_key=session["login_key"])
            else:
                logger.debug(
                    "Attempting Steam login using username/password; guard_code_present=%s",
                    bool(guard_code),
                )
                result = self._client.login(
                    username,
                    password,
                    two_factor_code=guard_code or None,
                )

            # If Steam requested email code instead of mobile 2FA, retry with auth_code.
            if result == EResult.AccountLogonDenied and guard_code:
                result = self._client.login(
                    username,
                    password,
                    auth_code=guard_code,
                )

            if result != EResult.OK:
                logger.error("Steam login failed with result %s", result)
                self._call_error(f"Login failed: {result}")
                return

            # Save session for future logins
            logger.debug("Steam login succeeded; persisting session data")
            session_data = {
                "username": username,
                "password": password,
                "steamid": str(self._client.user.steam_id),
            }

            if self._latest_login_key:
                session_data["login_key"] = self._latest_login_key

            self._storage.set_session(session_data)

            self._call_connected()
            self._update_all_friends()

            # Run gevent loop until disconnected.
            self._client.run_forever()

        except Exception as e:
            self._call_error(f"Steam client error: {str(e)}")
        finally:
            with self._lock:
                self._running = False

            try:
                if self._client is not None:
                    self._client.disconnect()
            except Exception:
                pass

            self._client = None

            self._call_disconnected()

    def _on_logged_on(self):
        """Called when logged on event is emitted."""
        logger.debug("Steam logged_on event received")
        self._call_connected()
        self._update_all_friends()

    def _on_client_disconnected(self):
        """Called when disconnected event is emitted."""
        logger.debug("Steam disconnected event received")
        self._call_disconnected()

    def _on_friends_ready(self):
        """Called when friends cache is ready; sync initial game state."""
        logger.debug("Steam friends cache is ready")
        self._update_all_friends()

    def _on_new_login_key(self, login_key):
        """Persist the latest Steam login key for future runs."""
        try:
            logger.debug("Received new Steam login key")
            self._latest_login_key = login_key
            session = self._storage.get_session() or {}
            session["login_key"] = login_key
            self._storage.set_session(session)
        except Exception as exc:
            self._call_error(f"Failed to store login key: {exc}")

    def _handle_persona_state(self, message):
        """Handle persona state updates."""
        try:
            monitored_friends = self._storage.get_friends()
            logger.debug(
                "Persona state update received for %d friends",
                len(message.body.friends),
            )

            for friend_data in message.body.friends:
                friend_id = int(friend_data.friendid)

                if friend_id not in monitored_friends:
                    continue

                game_id = self._extract_game_id(friend_data)

                with self._lock:
                    old_game_id = self._friend_game_ids.get(friend_id)

                    # Friend stopped playing
                    if game_id is None:
                        if old_game_id is not None:
                            logger.debug("Friend %s stopped playing", friend_id)
                            self._friend_game_ids[friend_id] = None
                            self._sent_messages.discard(friend_id)
                            self._call_friend_state_changed(friend_id, None)

                    # Friend started playing
                    elif game_id != old_game_id:
                        logger.debug("Friend %s started game %s", friend_id, game_id)
                        self._friend_game_ids[friend_id] = game_id
                        self._sent_messages.discard(friend_id)
                        self._send_message_to_friend(friend_id)
                        self._call_friend_state_changed(friend_id, game_id)

        except Exception as e:
            self._call_error(f"Persona state error: {str(e)}")

    def _update_all_friends(self):
        """Poll all monitored friends for current state."""
        try:
            monitored_friends = self._storage.get_friends()
            logger.debug(
                "Polling %d monitored friends for initial state", len(monitored_friends)
            )

            for friend_id in monitored_friends:
                try:
                    friend = self._client.get_user(friend_id, fetch_persona_state=True)
                    if friend:
                        game_id = self._extract_game_id(friend)

                        with self._lock:
                            old_game_id = self._friend_game_ids.get(friend_id)

                            if game_id and game_id != old_game_id:
                                logger.debug(
                                    "Initial poll found friend %s in game %s",
                                    friend_id,
                                    game_id,
                                )
                                self._friend_game_ids[friend_id] = game_id
                                self._sent_messages.discard(friend_id)
                                self._send_message_to_friend(friend_id)

                except Exception:
                    continue

        except Exception as e:
            self._call_error(f"Friend update error: {str(e)}")

    def _send_message_to_friend(self, friend_id: int):
        """Send random message to friend (call only with lock held)."""
        if friend_id in self._sent_messages:
            logger.debug(
                "Skipping message for friend %s because it was already sent", friend_id
            )
            return

        messages = self._storage.get_messages()
        if not messages:
            logger.debug("No messages configured; skipping send to %s", friend_id)
            return

        try:
            friend = self._client.get_user(friend_id, fetch_persona_state=True)
            if not friend:
                logger.debug("Could not resolve friend object for %s", friend_id)
                return

            message = random.choice(messages)
            logger.debug("Sending message to %s: %s", friend_id, message)
            friend.send_message(message)

            self._sent_messages.add(friend_id)
            self._call_message_sent(friend_id, message)

        except Exception as e:
            logger.error("Failed to send message to %s: %s", friend_id, e)
            self._call_error(f"Failed to send message to {friend_id}: {str(e)}")

    @staticmethod
    def _extract_game_id(friend_data: Any) -> Optional[int]:
        """Extract game_id from friend data."""
        candidates = (
            getattr(friend_data, "gameid", None),
            getattr(friend_data, "game_id", None),
            getattr(friend_data, "game_played_app_id", None),
            getattr(friend_data, "current_game_appid", None),
            getattr(friend_data, "app_id", None),
            getattr(friend_data, "appid", None),
        )

        for value in candidates:
            if value not in (None, 0, "", False):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    continue

        if hasattr(friend_data, "get_ps"):
            for field_name in ("gameid", "appid", "game_played_app_id"):
                try:
                    value = friend_data.get_ps(field_name, False)
                except Exception:
                    continue

                if value not in (None, 0, "", False):
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        continue

        return None

    # --- Callback invocations ---

    def _call_connected(self):
        if self._cb_on_connected:
            try:
                self._cb_on_connected()
            except Exception:
                pass

    def _call_disconnected(self):
        if self._cb_on_disconnected:
            try:
                self._cb_on_disconnected()
            except Exception:
                pass

    def _call_friend_state_changed(self, friend_id: int, game_id: Optional[int]):
        if self._cb_on_friend_state_changed:
            try:
                self._cb_on_friend_state_changed(friend_id, game_id)
            except Exception:
                pass

    def _call_message_sent(self, friend_id: int, message: str):
        if self._cb_on_message_sent:
            try:
                self._cb_on_message_sent(friend_id, message)
            except Exception:
                pass

    def _call_error(self, message: str):
        if self._cb_on_error:
            try:
                self._cb_on_error(message)
            except Exception:
                pass
