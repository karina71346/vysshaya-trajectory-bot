async def create_db_pool():
    """
    Создаём пул подключений к PostgreSQL.
    Приводим postgres:// к формату postgresql://, если нужно.
    """
    db_url = DATABASE_URL
    if not db_url:
        raise RuntimeError("Не задан DATABASE_URL в окружении (DATABASE_URL).")

    # для совместимости с Render / другими сервисами
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    pool = await asyncpg.create_pool(dsn=db_url)
    return pool
