"""Validation utilities for Steam IDs and URLs."""

import re
from functools import lru_cache
from typing import Optional

import requests


def parse_steam_id(input_str: str) -> Optional[int]:
    """
    Parse Steam ID from various formats.
    Accepts:
    - SteamID64 (17-digit number)
    - Steam profile URLs
    Returns SteamID64 as int, or None if invalid.
    """
    input_str = input_str.strip()

    # Try direct SteamID64 (17 digits)
    if input_str.isdigit() and len(input_str) == 17:
        return int(input_str)

    # Try to extract from URL patterns
    # https://steamcommunity.com/profiles/76561198XXXXXXXXX
    # https://steamcommunity.com/gid/[U:1:XXXXXXXXX]
    # https://steamcommunity.com/user/USERNAME

    profile_match = re.search(r"profiles/(\d{17})", input_str)
    if profile_match:
        return int(profile_match.group(1))

    vanity_id = _resolve_vanity_profile_to_id64(input_str)
    if vanity_id is not None:
        return vanity_id

    return None


@lru_cache(maxsize=256)
def _resolve_vanity_profile_to_id64(input_str: str) -> Optional[int]:
    """Resolve a Steam vanity profile URL (/id/<username>) to SteamID64."""
    vanity_match = re.search(r"steamcommunity\.com/id/([^/?#]+)/?", input_str)
    if vanity_match is None:
        return None

    vanity_name = vanity_match.group(1)
    xml_url = f"https://steamcommunity.com/id/{vanity_name}/?xml=1"

    try:
        response = requests.get(xml_url, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return None

    id64_match = re.search(r"<steamID64>(\d{17})</steamID64>", response.text)
    if id64_match is None:
        return None

    return int(id64_match.group(1))


def is_valid_steam_id(steam_id: int) -> bool:
    """Validate that a number is a valid SteamID64."""
    if not isinstance(steam_id, int):
        return False

    # Steam ID64 should be 17 digits (76561190000000000 to 76561219999999999 approximately)
    steam_id_str = str(steam_id)

    # Check length
    if len(steam_id_str) != 17:
        return False

    # Check if it starts with known prefix (765611 or 765612 for public universe)
    if not steam_id_str.startswith(("765611", "765612")):
        return False

    return True


def normalize_message(message: str) -> str:
    """Clean and normalize a message."""
    return message.strip()


def is_valid_message(message: str) -> bool:
    """Validate that a message is non-empty."""
    return len(normalize_message(message)) > 0
