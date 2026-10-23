import asyncio
from database import init_db
import admin_bot, shop_bot

async def main():
    init_db()
    await asyncio.gather(
        admin_bot.dp.start_polling(admin_bot.bot),
        shop_bot.dp.start_polling(shop_bot.bot),
    )

if __name__ == "__main__":
    asyncio.run(main())
