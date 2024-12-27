import datetime

from aiohttp import web
from aiogram.types import Update
from loguru import logger
from bot.app.utils import check_signature_result
from bot.config import bot, dp, settings
from bot.dao.database import async_session_maker
from bot.user.utils import successful_payment_logic


async def handle_webhook(request: web.Request):
    try:
        update = Update(**await request.json())
        await dp.feed_update(bot, update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}")
        return web.Response(status=500)


# Функция для обработки запроса на эндпоинт "Hello, World!"
async def home_page(request: web.Request) -> web.Response:
    """
    Обработчик для отображения главной страницы с информацией о сервисе.
    """
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>aiohttp Демонстрация</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
            h1 {{ color: #333; }}
            .info {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>Привет, меня зовут Яковенко Алексей</h1>
        <p>Тут вы видите то, что aiohttp способен вполне себе рендерить и HTML странички.</p>
        <div class="info">
            <p>Через aiohttp в данном проекте обрабатываются:</p>
            <ul>
                <li>Хуки от телеграмм бота</li>
                <li>Хуки для обработки ответов от робокассы</li>
            </ul>
        </div>
        <p>Текущее время сервера: {current_time}</p>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')


async def robokassa_result(request: web.Request) -> web.Response:
    """
    Обрабатывает запрос от Робокассы на ResultURL.

    :param request: HTTP-запрос
    :return: Текстовый ответ с результатами проверки
    """
    logger.success("Получен ответ от Робокассы!")
    data = await request.post()

    # Извлекаем параметры из запроса
    signature = data.get('SignatureValue')
    out_sum = data.get('OutSum')
    inv_id = data.get('InvId')
    user_id = data.get('Shp_user_id')
    user_telegram_id = data.get('Shp_user_telegram_id')
    product_id = data.get('Shp_product_id')

    # Проверяем подпись
    if check_signature_result(
        out_sum=out_sum,
        inv_id=inv_id,
        received_signature=signature,
        password=settings.MRH_PASS_2,
        user_id=user_id,
        user_telegram_id=user_telegram_id,
        product_id=product_id
    ):
        result = f"OK{inv_id}"
        logger.info(f"Успешная проверка подписи для InvId: {inv_id}")

        payment_data = {
            'user_id': int(user_id),
            'payment_id': signature,
            'price': int(out_sum),
            'product_id': int(product_id),
            'payment_type': "robocassa"
        }
        async with async_session_maker() as session:
            await successful_payment_logic(
                session=session,
                payment_data=payment_data,
                currency="₽",
                user_tg_id=int(user_telegram_id),
                bot=bot
            )
            await session.commit()
    else:
        result = "bad sign"
        logger.warning(f"Неверная подпись для InvId: {inv_id}")

    logger.info(f"Ответ: {result}")
    return web.Response(text=result)


async def robokassa_fail(request):
    # Получаем параметры из GET-запроса
    inv_id = request.query.get('InvId')
    out_sum = request.query.get('OutSum')
    print(f"Неудачный платеж: сумма {out_sum}, ID {inv_id}")
    return web.Response(text="Платеж не удался", content_type='text/html')
