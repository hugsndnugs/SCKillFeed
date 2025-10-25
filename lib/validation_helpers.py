"""Validation helpers extracted from the GUI.

These functions are pure or best-effort and can be used by the GUI
without depending on the full GUI instance.
"""

import os
import logging

logger = logging.getLogger(__name__)


def validate_file_path(file_path: str) -> bool:
    """Validate a candidate log file path.

    Returns True if the path is acceptable for monitoring. This mirrors the
    original GUI validation but is implemented as a standalone function so
    it can be reused and tested independently.
    """
    if not file_path or not isinstance(file_path, str):
        logger.warning("Invalid file path: empty or not a string")
        return False

    try:
        file_path = file_path.strip()

        if len(file_path) < 3:
            logger.warning("File path too short")
            return False

        suspicious_patterns = ["..", "~", "$", "`", "|", "&", ";", "(", ")", "<", ">"]
        for pattern in suspicious_patterns:
            if pattern in file_path:
                logger.warning(f"Suspicious pattern '{pattern}' found in file path")
                return False

        normalized_path = os.path.normpath(file_path)
        resolved_path = os.path.abspath(normalized_path)

        if len(resolved_path) > 260:
            logger.warning("File path too long")
            return False

        if not os.path.exists(resolved_path):
            logger.warning(f"File does not exist: {resolved_path}")
            return False

        if not resolved_path.lower().endswith(".log"):
            logger.warning("File is not a .log file")
            return False

        if not os.path.isfile(resolved_path):
            logger.warning("Path is not a file")
            return False

        file_size = os.path.getsize(resolved_path)
        if file_size > 100 * 1024 * 1024:
            logger.warning(f"Log file is very large: {file_size / (1024*1024):.1f}MB")

        logger.debug(f"File path validated successfully: {resolved_path}")
        return True

    except (OSError, ValueError) as e:
        logger.error(f"Error validating file path: {e}")
        return False


def validate_player_name(player_name: str) -> bool:
    """Validate a player name (ingame name) string.

    Returns True if name is acceptable.
    """
    if not player_name or not isinstance(player_name, str):
        logger.warning("Invalid player name: empty or not a string")
        return False

    player_name = player_name.strip()
    if len(player_name) < 1 or len(player_name) > 50:
        logger.warning(f"Player name length invalid: {len(player_name)}")
        return False

    suspicious_chars = ["<", ">", "&", '"', "'", "\\", "/", "|", ";", "`", "$"]
    for ch in suspicious_chars:
        if ch in player_name:
            logger.warning(f"Suspicious character '{ch}' found in player name")
            return False

    logger.debug(f"Player name validated successfully: {player_name}")
    return True
