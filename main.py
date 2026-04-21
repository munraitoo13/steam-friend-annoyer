import os
from typing import Optional

from dotenv import load_dotenv
from steam.client import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
MESSAGE = os.getenv("MESSAGE") or "pode fechar"
TARGET_FRIEND_ID64 = int(x) if (x := os.getenv("TARGET_FRIEND_ID64")) else None

client = SteamClient()

last_notified_game_id: Optional[int] = None


def get_target_friend():
    if TARGET_FRIEND_ID64 is None:
        return None

    return client.get_user(TARGET_FRIEND_ID64, False)


def get_game_id(friend) -> Optional[int]:
    if friend is None:
        return None

    candidates = (
        getattr(friend, "gameid", None),
        getattr(friend, "game_id", None),
        getattr(friend, "game_played_app_id", None),
        getattr(friend, "current_game_appid", None),
        getattr(friend, "app_id", None),
        getattr(friend, "appid", None),
    )

    for value in candidates:
        if value not in (None, 0, "", False):
            return int(value)

    if hasattr(friend, "get_ps"):
        for field_name in ("gameid", "appid", "game_played_app_id"):
            try:
                value = friend.get_ps(field_name, False)
            except AttributeError:
                continue

            if value not in (None, 0, "", False):
                return int(value)

    return None


def send_message(game_id: int):
    global last_notified_game_id

    if last_notified_game_id == game_id:
        return

    friend = get_target_friend()
    if friend is None:
        print("amigo não encontrado")
        return

    friend.send_message(MESSAGE)
    last_notified_game_id = game_id
    print(f"mensagem enviada para {TARGET_FRIEND_ID64} porque entrou no jogo {game_id}")


def sync_target_friend_state():
    friend = get_target_friend()
    if friend is None:
        print("amigo não encontrado")
        return

    friend.refresh(wait=True)
    game_id = get_game_id(friend)

    if game_id is None:
        return

    send_message(game_id)


def handle_persona_state(message):
    global last_notified_game_id

    for friend in message.body.friends:
        if int(friend.friendid) != TARGET_FRIEND_ID64:
            continue

        game_id = get_game_id(friend)
        if game_id is None:
            last_notified_game_id = None
            return

        send_message(game_id)
        return


def on_logged_on():
    print("logado")


def on_friends_ready():
    sync_target_friend_state()


def main():
    if not USERNAME or not PASSWORD:
        print("faltando USERNAME/PASSWORD")
        return

    if TARGET_FRIEND_ID64 is None:
        print("faltando TARGET_FRIEND_ID64")
        return

    client.on("logged_on", on_logged_on)
    client.on(EMsg.ClientPersonaState, handle_persona_state)
    client.friends.on(client.friends.EVENT_READY, on_friends_ready)

    res = client.cli_login(USERNAME, PASSWORD)
    if res != EResult.OK:
        print("erro login:", res)
        return

    client.run_forever()


if __name__ == "__main__":
    main()
