from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def make_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    """
    Creates reply-keyboard with one row
    """
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True, one_time_keyboard=True)