import hashlib
from urllib import parse
from urllib.parse import urlparse
from bot.config import settings


def calculate_signature(login, cost, inv_id, password, user_id, user_telegram_id, product_id, is_result=False):
    if is_result:
        base_string = f"{cost}:{inv_id}:{password}"  # Для Result URL
    else:
        base_string = f"{login}:{cost}:{inv_id}:{password}"  # Для initital URL и Success URL

    additional_params = {
        'Shp_user_id': user_id,
        'Shp_user_telegram_id': user_telegram_id,
        'Shp_product_id': product_id
    }
    for key, value in sorted(additional_params.items()):
        base_string += f":{key}={value}"

    return hashlib.md5(base_string.encode('utf-8')).hexdigest()


def generate_payment_link(cost: float, number: int, description: str,
                          user_id: int, user_telegram_id: int, product_id: int,
                          is_test=1, robokassa_payment_url='https://auth.robokassa.ru/Merchant/Index.aspx') -> str:
    """
    Генерирует ссылку для оплаты через Robokassa с обязательными параметрами.

    :param cost: Стоимость товара
    :param number: Номер заказа
    :param description: Описание заказа
    :param user_id: ID пользователя
    :param user_telegram_id: Telegram ID пользователя
    :param product_id: ID товара
    :param is_test: Флаг тестового режима (1 - тест, 0 - боевой режим)
    :param robokassa_payment_url: URL для оплаты Robokassa
    :return: Ссылка на страницу оплаты
    """
    signature = calculate_signature(
        settings.MRH_LOGIN,
        cost,
        number,
        settings.MRH_PASS_1,
        user_id,
        user_telegram_id,
        product_id
    )

    data = {
        'MerchantLogin': settings.MRH_LOGIN,
        'OutSum': cost,
        'InvId': number,
        'Description': description,
        'SignatureValue': signature,
        'IsTest': is_test,
        'Shp_user_id': user_id,
        'Shp_user_telegram_id': user_telegram_id,
        'Shp_product_id': product_id
    }

    return f'{robokassa_payment_url}?{parse.urlencode(data)}'


def parse_response(request: str) -> dict:
    """
    Разбирает строку запроса на параметры.

    :param request: Строка запроса
    :return: Словарь с параметрами
    """
    return dict(parse.parse_qsl(urlparse(request).query))


def check_signature_result(out_sum, inv_id, received_signature, password, user_id, user_telegram_id, product_id) -> bool:
    signature = calculate_signature(
        settings.MRH_LOGIN,
        out_sum,
        inv_id,
        password,
        user_id,
        user_telegram_id,
        product_id,
        is_result=True  # Важный флаг для Result URL
    )
    return signature.lower() == received_signature.lower()


def result_payment(request: str) -> str:
    """
    Обрабатывает результат оплаты (ResultURL).

    :param request: Строка запроса с параметрами оплаты
    :return: 'OK' + номер заказа, если оплата прошла успешно, иначе 'bad sign'
    """
    params = parse_response(request)
    out_sum = params['OutSum']
    inv_id = params['InvId']
    signature = params['SignatureValue']
    user_id = params['Shp_user_id']
    user_telegram_id = params['Shp_user_telegram_id']
    product_id = params['Shp_product_id']

    if check_signature_result(out_sum, inv_id, signature, settings.MRH_PASS_2, user_id, user_telegram_id, product_id):
        return f'OK{inv_id}'
    return "bad sign"


def check_success_payment(request: str) -> str:
    """
    Проверяет успешность оплаты (SuccessURL).

    :param request: Строка запроса с параметрами оплаты
    :return: Сообщение об успешной оплате или 'bad sign' при неверной подписи
    """
    params = parse_response(request)
    out_sum = params['OutSum']
    inv_id = params['InvId']
    signature = params['SignatureValue']
    user_id = params['Shp_user_id']
    user_telegram_id = params['Shp_user_telegram_id']
    product_id = params['Shp_product_id']

    if check_signature_result(out_sum, inv_id, signature, settings.MRH_PASS_1, user_id, user_telegram_id, product_id):
        return "Thank you for using our service"
    return "bad sign"
