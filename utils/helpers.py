from typing import Optional, Tuple

from aiogram import Bot, types

from config import ADMIN_IDS


def get_file_id(message: types.Message) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the best quality file_id from a message.
    Returns: (file_id, file_type ['photo'|'document'|None])
    """
    if message.document:
        return message.document.file_id, "document"
    elif message.photo:
        # message.photo is a list of PhotoSize, last one is the largest
        return message.photo[-1].file_id, "photo"
    return None, None


async def notify_admins(bot: Bot, text: str, reply_markup=None, parse_mode="Markdown"):
    """
    Sends a message to the defined administrator(s).
    """
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to notify admin {admin_id}: {e}")
