from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from bot.config import bot


async def process_dell_text_msg(message: Message, state: FSMContext):
    data = await state.get_data()
    last_msg_id = data.get('last_msg_id')

    try:
        if last_msg_id:
            await bot.delete_message(chat_id=message.from_user.id, message_id=last_msg_id)
        else:
            logger.warning("Ошибка: Не удалось найти идентификатор последнего сообщения для удаления.")
        await message.delete()

    except Exception as e:
        logger.error(f"Произошла ошибка при удалении сообщения: {str(e)}")
