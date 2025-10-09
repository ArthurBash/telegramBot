"""
Handlers para todas las interacciones con Telegram.
Procesa mensajes y comandos administrativos del bot.
"""

import csv
import io
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.models import Message, Category, MessageStatistics
from app.bot.categorizer import MessageCategorizer
from app.utils import LoggerConfig, StringHelper, FormatterHelper, ValidationHelper
from app.config import config


class TelegramMessageHandler:
    """
    Handler para procesar mensajes normales de Telegram.
    Categoriza y guarda mensajes en la base de datos.
    """
    
    def __init__(self, categorizer: MessageCategorizer, db_session_factory):
        self.categorizer = categorizer
        self.db_session_factory = db_session_factory
        self.logger = LoggerConfig.setup_logger(__name__)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return
        
        message_text = update.message.text
        telegram_user_id = update.message.from_user.id
        telegram_chat_id = update.message.chat_id
        username = update.message.from_user.username
        chat_type = update.message.chat.type
        
        async with self.db_session_factory() as session:
            categories = await self._get_all_categories(session)
            
            if not categories:
                await update.message.reply_text(
                    "⚠️ No hay categorías configuradas. Usa /add_category para crear una."
                )
                return
            
            result = self.categorizer.categorize_message(message_text, categories)
            
            new_message = Message(
                telegram_chat_id=telegram_chat_id,
                telegram_user_id=telegram_user_id,
                username=username,
                chat_type=chat_type,
                message_text=message_text,
                category=result['category'],
                confidence_score=result['confidence_score']
            )
            
            session.add(new_message)
            await session.commit()
            
            self.logger.info(
                f"Mensaje guardado: user={telegram_user_id}, "
                f"category={result['category']}, score={result['confidence_score']:.2f}"
            )
            
            confidence_text = FormatterHelper.format_confidence_score(result['confidence_score'])
            await update.message.reply_text(
                f"✅ Categorizado como: *{result['category']}*\n"
                f"🎯 Confianza: {confidence_text}",
                parse_mode='Markdown'
            )
    
    async def _get_all_categories(self, session: AsyncSession) -> list[Category]:
        result = await session.execute(select(Category))
        return result.scalars().all()


class CategoryManagementHandler:
    """
    Handler para comandos de gestión de categorías.
    Permite agregar, listar y eliminar categorías.
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.logger = LoggerConfig.setup_logger(__name__)
    
    async def handle_add_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: /add_category <nombre> <palabra1, palabra2, ...>\n"
                "Ejemplo: /add_category trabajo reunión, meeting, oficina"
            )
            return
        
        category_name = context.args[0].lower()
        keywords_text = " ".join(context.args[1:])
        keywords = StringHelper.string_to_keywords(keywords_text)
        
        if not ValidationHelper.is_valid_category_name(category_name):
            await update.message.reply_text(
                "❌ Nombre de categoría inválido. Solo letras, números, guiones y guiones bajos."
            )
            return
        
        if not keywords:
            await update.message.reply_text("❌ Debes proporcionar al menos una palabra clave.")
            return
        
        async with self.db_session_factory() as session:
            existing = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            if existing.scalar_one_or_none():
                await update.message.reply_text(
                    f"❌ La categoría '{category_name}' ya existe. Usa /delete_category primero."
                )
                return
            
            new_category = Category(
                name=category_name,
                keywords=keywords
            )
            session.add(new_category)
            await session.commit()
            
            self.logger.info(f"Categoría creada: {category_name} con {len(keywords)} keywords")
            
            formatted_info = FormatterHelper.format_category_info(category_name, keywords)
            await update.message.reply_text(
                f"✅ Categoría creada exitosamente:\n\n{formatted_info}"
            )
    
    async def handle_list_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async with self.db_session_factory() as session:
            result = await session.execute(select(Category))
            categories = result.scalars().all()
            
            if not categories:
                await update.message.reply_text("📭 No hay categorías configuradas.")
                return
            
            response_lines = ["📚 *Categorías configuradas:*\n"]
            
            for category in categories:
                formatted = FormatterHelper.format_category_info(category.name, category.keywords)
                response_lines.append(formatted)
                response_lines.append("")
            
            await update.message.reply_text(
                "\n".join(response_lines),
                parse_mode='Markdown'
            )
    
    async def handle_delete_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Uso: /delete_category <nombre>\n"
                "Ejemplo: /delete_category trabajo"
            )
            return
        
        category_name = context.args[0].lower()
        
        if category_name == config.default_category:
            await update.message.reply_text(
                f"❌ No puedes eliminar la categoría por defecto '{config.default_category}'."
            )
            return
        
        async with self.db_session_factory() as session:
            result = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                await update.message.reply_text(f"❌ La categoría '{category_name}' no existe.")
                return
            
            await session.execute(
                delete(Category).where(Category.name == category_name)
            )
            await session.commit()
            
            self.logger.info(f"Categoría eliminada: {category_name}")
            await update.message.reply_text(f"✅ Categoría '{category_name}' eliminada exitosamente.")


class StatisticsHandler:
    """
    Handler para comandos de estadísticas.
    Genera reportes de mensajes categorizados.
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.logger = LoggerConfig.setup_logger(__name__)
    
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async with self.db_session_factory() as session:
            total_result = await session.execute(select(func.count(Message.id)))
            total_messages = total_result.scalar()
            
            if total_messages == 0:
                await update.message.reply_text("📭 No hay mensajes registrados aún.")
                return
            
            category_result = await session.execute(
                select(Message.category, func.count(Message.id))
                .group_by(Message.category)
            )
            category_counts = dict(category_result.all())
            
            stats_text = FormatterHelper.format_message_stats(total_messages, category_counts)
            
            avg_confidence_result = await session.execute(
                select(Message.category, func.avg(Message.confidence_score))
                .group_by(Message.category)
            )
            avg_confidences = dict(avg_confidence_result.all())
            
            confidence_lines = ["\n📈 *Confianza promedio por categoría:*"]
            for category_name, avg_score in sorted(avg_confidences.items()):
                if avg_score is not None:
                    formatted_score = FormatterHelper.format_confidence_score(avg_score)
                    confidence_lines.append(f"  • {category_name}: {formatted_score}")
            
            full_stats = stats_text + "\n" + "\n".join(confidence_lines)
            
            await update.message.reply_text(full_stats, parse_mode='Markdown')


class ExportHandler:
    """
    Handler para exportar datos.
    Genera archivos CSV con categorías.
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.logger = LoggerConfig.setup_logger(__name__)
    
    async def handle_export_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async with self.db_session_factory() as session:
            result = await session.execute(select(Category))
            categories = result.scalars().all()
            
            if not categories:
                await update.message.reply_text("📭 No hay categorías para exportar.")
                return
            
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            csv_writer.writerow(['name', 'keywords'])
            
            for category in categories:
                keywords_str = StringHelper.keywords_to_string(category.keywords)
                csv_writer.writerow([category.name, keywords_str])
            
            csv_buffer.seek(0)
            csv_bytes = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))
            csv_bytes.name = f"categories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            await update.message.reply_document(
                document=csv_bytes,
                filename=csv_bytes.name,
                caption="📄 Exportación de categorías"
            )
            
            self.logger.info("Categorías exportadas a CSV")


"""
Handler especializado para gestión de palabras clave.
Agregar esta clase completa al archivo handlers.py
"""

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from app.models import Category
from app.utils import LoggerConfig, StringHelper, FormatterHelper, ValidationHelper


class KeywordManagementHandler:
    """
    Handler para gestión avanzada de palabras clave.
    Permite agregar, actualizar y modificar keywords de categorías.
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.logger = LoggerConfig.setup_logger(__name__)
    
    async def handle_add_keywords(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Agrega palabras clave a una categoría existente o crea una nueva.
        Uso: /ak <nombre_categoria> <palabra1, palabra2, ...>
        """
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ *Uso incorrecto*\n\n"
                "`/ak <categoria> <palabra1, palabra2, ...>`\n\n"
                "*Ejemplos:*\n"
                "• `/ak trabajo reunión, meeting, oficina`\n"
                "• `/ak personal familia, amigos, casa`\n\n"
                "💡 Si la categoría existe, agrega las palabras clave\n"
                "💡 Si no existe, crea la categoría automáticamente",
                parse_mode='Markdown'
            )
            return
        
        category_name = context.args[0].lower()
        keywords_text = " ".join(context.args[1:])
        new_keywords = StringHelper.string_to_keywords(keywords_text)
        
        # Validaciones
        if not ValidationHelper.is_valid_category_name(category_name):
            await update.message.reply_text(
                "❌ Nombre de categoría inválido.\n"
                "Solo se permiten: letras, números, guiones y guiones bajos."
            )
            return
        
        if not new_keywords:
            await update.message.reply_text(
                "❌ Debes proporcionar al menos una palabra clave."
            )
            return
        
        async with self.db_session_factory() as session:
            result = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            existing_category = result.scalar_one_or_none()
            
            if existing_category:
                # Actualizar categoría existente
                await self._update_existing_category(
                    update, session, existing_category, new_keywords
                )
            else:
                # Crear nueva categoría
                await self._create_new_category(
                    update, session, category_name, new_keywords
                )
    
    async def _update_existing_category(
        self, 
        update: Update, 
        session, 
        category: Category, 
        new_keywords: list[str]
    ):
        """Actualiza una categoría existente agregando nuevas keywords."""
        current_keywords = set(category.keywords)
        keywords_added = []
        keywords_duplicated = []
        
        for keyword in new_keywords:
            if keyword not in current_keywords:
                current_keywords.add(keyword)
                keywords_added.append(keyword)
            else:
                keywords_duplicated.append(keyword)
        
        if not keywords_added:
            await update.message.reply_text(
                f"ℹ️ *Categoría:* `{category.name}`\n\n"
                f"Todas las palabras clave ya existen.\n\n"
                f"🔄 Duplicadas: {', '.join(keywords_duplicated)}",
                parse_mode='Markdown'
            )
            return
        
        # Actualizar la categoría
        category.keywords = list(current_keywords)
        # Solo actualiza updated_at si tu modelo lo tiene
        if hasattr(category, 'updated_at'):
            category.updated_at = datetime.utcnow()
        
        await session.commit()
        
        self.logger.info(
            f"Keywords agregadas a '{category.name}': "
            f"{len(keywords_added)} nuevas, {len(keywords_duplicated)} duplicadas"
        )
        
        # Construir respuesta
        response = [
            f"✅ *Categoría actualizada:* `{category.name}`\n",
            f"🆕 *Agregadas ({len(keywords_added)}):*",
            f"   {', '.join(keywords_added)}\n"
        ]
        
        if keywords_duplicated:
            response.append(f"⚠️ *Ya existían ({len(keywords_duplicated)}):*")
            response.append(f"   {', '.join(keywords_duplicated)}\n")
        
        response.append(f"📊 *Total de palabras clave:* {len(current_keywords)}")
        
        await update.message.reply_text(
            "\n".join(response),
            parse_mode='Markdown'
        )
    
    async def _create_new_category(
        self, 
        update: Update, 
        session, 
        category_name: str, 
        keywords: list[str]
    ):
        """Crea una nueva categoría con las palabras clave proporcionadas."""
        new_category = Category(
            name=category_name,
            keywords=keywords
        )
        session.add(new_category)
        await session.commit()
        
        self.logger.info(
            f"Categoría creada via /ak: {category_name} con {len(keywords)} keywords"
        )
        
        formatted_info = FormatterHelper.format_category_info(category_name, keywords)
        
        await update.message.reply_text(
            f"✨ *Nueva categoría creada*\n\n{formatted_info}",
            parse_mode='Markdown'
        )
    
    async def handle_remove_keywords(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Elimina palabras clave de una categoría existente.
        Uso: /rk <nombre_categoria> <palabra1, palabra2, ...>
        """
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ *Uso incorrecto*\n\n"
                "`/rk <categoria> <palabra1, palabra2, ...>`\n\n"
                "*Ejemplo:*\n"
                "• `/rk trabajo reunión, meeting`",
                parse_mode='Markdown'
            )
            return
        
        category_name = context.args[0].lower()
        keywords_text = " ".join(context.args[1:])
        keywords_to_remove = StringHelper.string_to_keywords(keywords_text)
        
        async with self.db_session_factory() as session:
            result = await session.execute(
                select(Category).where(Category.name == category_name)
            )
            category = result.scalar_one_or_none()
            
            if not category:
                await update.message.reply_text(
                    f"❌ La categoría `{category_name}` no existe.",
                    parse_mode='Markdown'
                )
                return
            
            current_keywords = set(category.keywords)
            removed = []
            not_found = []
            
            for keyword in keywords_to_remove:
                if keyword in current_keywords:
                    current_keywords.remove(keyword)
                    removed.append(keyword)
                else:
                    not_found.append(keyword)
            
            if not removed:
                await update.message.reply_text(
                    f"ℹ️ Ninguna palabra clave fue eliminada.\n"
                    f"No encontradas: {', '.join(not_found)}"
                )
                return
            
            if len(current_keywords) == 0:
                await update.message.reply_text(
                    f"⚠️ No puedes eliminar todas las palabras clave.\n"
                    f"La categoría debe tener al menos una palabra clave."
                )
                return
            
            category.keywords = list(current_keywords)
            if hasattr(category, 'updated_at'):
                category.updated_at = datetime.utcnow()
            
            await session.commit()
            
            self.logger.info(
                f"Keywords eliminadas de '{category_name}': {len(removed)}"
            )
            
            response = [
                f"✅ *Palabras clave eliminadas de:* `{category_name}`\n",
                f"🗑️ *Eliminadas ({len(removed)}):*",
                f"   {', '.join(removed)}\n"
            ]
            
            if not_found:
                response.append(f"⚠️ *No encontradas ({len(not_found)}):*")
                response.append(f"   {', '.join(not_found)}\n")
            
            response.append(f"📊 *Total restante:* {len(current_keywords)}")
            
            await update.message.reply_text(
                "\n".join(response),
                parse_mode='Markdown'
            )