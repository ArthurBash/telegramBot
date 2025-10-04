"""
Punto de entrada principal de la aplicación.
Inicializa FastAPI, bot de Telegram y crea tablas de base de datos.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import config
from app.database import DatabaseManager
from app.bot.categorizer import MessageCategorizer
from app.bot.handlers import (
    TelegramMessageHandler,
    CategoryManagementHandler,
    StatisticsHandler,
    ExportHandler
)
from app.utils import LoggerConfig


logger = LoggerConfig.setup_logger(__name__)


class TelegramBotApplication:
    """
    Aplicación principal del bot de Telegram.
    Gestiona la inicialización y configuración de todos los handlers.
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.categorizer = MessageCategorizer()
        self.telegram_app = None
        
        self.message_handler = TelegramMessageHandler(
            categorizer=self.categorizer,
            db_session_factory=self.db_manager.get_session
        )
        
        self.category_handler = CategoryManagementHandler(
            db_session_factory=self.db_manager.get_session
        )
        
        self.stats_handler = StatisticsHandler(
            db_session_factory=self.db_manager.get_session
        )
        
        self.export_handler = ExportHandler(
            db_session_factory=self.db_manager.get_session
        )
    
    async def initialize(self):
        logger.info("Inicializando base de datos...")
        await self.db_manager.create_tables()
        logger.info("Base de datos inicializada correctamente")
        
        logger.info("Inicializando bot de Telegram...")
        self.telegram_app = Application.builder().token(config.telegram_bot_token).build()
        
        self._register_handlers()
        logger.info("Handlers registrados correctamente")
    
    def _register_handlers(self):
        self.telegram_app.add_handler(
            CommandHandler(["add_category", "ac"], self.category_handler.handle_add_category)
        )
        
        self.telegram_app.add_handler(
            CommandHandler(["list_categories", "lc"], self.category_handler.handle_list_categories)
        )
        
        self.telegram_app.add_handler(
            CommandHandler(["delete_category", "dc"], self.category_handler.handle_delete_category)
        )
        
        self.telegram_app.add_handler(
            CommandHandler(["stats", "s"], self.stats_handler.handle_stats)
        )
        
        self.telegram_app.add_handler(
            CommandHandler("export_categories", self.export_handler.handle_export_categories)
        )
        
        self.telegram_app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler.handle_message)
        )
    
    async def start_polling(self):
        logger.info("Iniciando polling del bot...")
        await self.telegram_app.initialize()
        await self.telegram_app.start()
        await self.telegram_app.updater.start_polling(drop_pending_updates=False)
        logger.info(f"Bot iniciado correctamente: @{self.telegram_app.bot.username}")
    
    async def stop(self):
        logger.info("Deteniendo bot...")
        if self.telegram_app:
            await self.telegram_app.updater.stop()
            await self.telegram_app.stop()
            await self.telegram_app.shutdown()
        await self.db_manager.close()
        logger.info("Bot detenido correctamente")


bot_application = TelegramBotApplication()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicación...")
    await bot_application.initialize()
    
    asyncio.create_task(bot_application.start_polling())
    
    yield
    
    logger.info("Cerrando aplicación...")
    await bot_application.stop()


app = FastAPI(
    title="Telegram Categorizer",
    description="Bot de Telegram para categorización automática de mensajes",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "telegram-categorizer",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "bot": "active"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Iniciando servidor FastAPI...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=config.log_level.lower()
    )