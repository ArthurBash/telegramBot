"""
Configuración de base de datos con SQLAlchemy asíncrono.
Gestiona conexiones, sesiones y creación de tablas.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)

from app.config import config
from app.models import Base
from app.utils import LoggerConfig


logger = LoggerConfig.setup_logger(__name__)


class DatabaseManager:
    """
    Gestor centralizado de la base de datos.
    Maneja el engine, sesiones y ciclo de vida de conexiones.
    """
    
    def __init__(self):
        self.engine: AsyncEngine = create_async_engine(
            config.database_url,
            echo=config.log_level == "DEBUG",
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("DatabaseManager inicializado correctamente")
    
    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tablas de base de datos creadas/verificadas")
    
    async def drop_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("Todas las tablas han sido eliminadas")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        session = self.async_session_factory()
        try:
            yield session
        except Exception as error:
            await session.rollback()
            logger.error(f"Error en sesión de base de datos: {error}")
            raise
        finally:
            await session.close()
    
    async def close(self):
        await self.engine.dispose()
        logger.info("Conexiones de base de datos cerradas")
    
    async def check_connection(self) -> bool:
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as error:
            logger.error(f"Error al verificar conexión: {error}")
            return False