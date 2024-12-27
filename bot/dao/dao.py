from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict

from loguru import logger
from sqlalchemy import select, func, case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.dao.base import BaseDAO
from bot.dao.models import User, Purchase, Category, Product


class UserDAO(BaseDAO[User]):
    model = User

    @classmethod
    async def get_purchase_statistics(cls, session: AsyncSession, telegram_id: int) -> Optional[Dict[str, int]]:
        try:
            # Запрос для получения общего числа покупок и общей суммы
            result = await session.execute(
                select(
                    func.count(Purchase.id).label('total_purchases'),
                    func.sum(Purchase.price).label('total_amount')
                ).join(User).filter(User.telegram_id == telegram_id)
            )
            stats = result.one_or_none()

            if stats is None:
                return None

            total_purchases, total_amount = stats
            return {
                'total_purchases': total_purchases,
                'total_amount': total_amount or 0  # Обработка случая, когда сумма может быть None
            }

        except SQLAlchemyError as e:
            # Обработка ошибок при работе с базой данных
            print(f"Ошибка при получении статистики покупок пользователя: {e}")
            return None

    @classmethod
    async def get_purchased_products(cls, session: AsyncSession, telegram_id: int) -> Optional[List[Purchase]]:
        try:
            # Запрос для получения пользователя с его покупками и связанными продуктами
            result = await session.execute(
                select(User)
                .options(
                    selectinload(User.purchases).selectinload(Purchase.product)
                )
                .filter(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user is None:
                return None

            return user.purchases

        except SQLAlchemyError as e:
            # Обработка ошибок при работе с базой данных
            print(f"Ошибка при получении информации о покупках пользователя: {e}")
            return None


    @classmethod
    async def get_statistics(cls, session: AsyncSession):
        try:
            now = datetime.now(UTC)

            query = select(
                func.count().label('total_users'),
                func.sum(case((cls.model.created_at >= now - timedelta(days=1), 1), else_=0)).label('new_today'),
                func.sum(case((cls.model.created_at >= now - timedelta(days=7), 1), else_=0)).label('new_week'),
                func.sum(case((cls.model.created_at >= now - timedelta(days=30), 1), else_=0)).label('new_month')
            )

            result = await session.execute(query)
            stats = result.fetchone()

            statistics = {
                'total_users': stats.total_users,
                'new_today': stats.new_today,
                'new_week': stats.new_week,
                'new_month': stats.new_month
            }

            logger.info(f"Статистика успешно получена: {statistics}")
            return statistics
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            raise


class PurchaseDao(BaseDAO[Purchase]):
    model = Purchase

    @classmethod
    async def get_payment_stats(cls, session: AsyncSession) -> str:
        query = select(
            cls.model.payment_type,
            func.sum(cls.model.price).label('total_price')
        ).group_by(cls.model.payment_type)

        result = await session.execute(query)
        stats = result.all()

        # Словарь для хранения результатов
        totals: Dict[str, float] = {
            'yukassa': 0,
            'robocassa': 0,
            'stars': 0
        }

        # Заполняем словарь результатами запроса
        for payment_type, total in stats:
            totals[payment_type] = total or 0

        # Форматируем результат
        formatted_stats = (
            f"💳 Юкасса: {totals['yukassa']:.2f} ₽\n"
            f"🤖 Робокасса: {totals['robocassa']:.2f} ₽\n"
            f"⭐ STARS: {totals['stars']:.0f}\n\n"
            f"Статистика актуальна на данный момент."
        )

        return formatted_stats

    @classmethod
    async def get_full_summ(cls, session: AsyncSession) -> int:
        query = select(func.sum(cls.model.price).label('total_price'))
        result = await session.execute(query)
        total_price = result.scalars().one_or_none()
        return total_price if total_price is not None else 0

    @classmethod
    async def get_next_id(cls, session: AsyncSession) -> int:
        """
        Возвращает следующий свободный ID для новой записи.

        :param session: Асинхронная сессия базы данных
        :return: Следующий свободный ID
        """
        query = select(func.coalesce(func.max(cls.model.id) + 1, 1))
        result = await session.execute(query)
        return result.scalar()


class CategoryDao(BaseDAO[Category]):
    model = Category


class ProductDao(BaseDAO[Product]):
    model = Product
