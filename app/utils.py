"""
Utilidades y funciones auxiliares de la aplicación.
"""

import logging
import re
import unicodedata
from typing import Optional

from app.config import config


class LoggerConfig:
    """Configuración centralizada del sistema de logging."""
    
    _loggers = {}
    
    @classmethod
    def setup_logger(cls, name: str) -> logging.Logger:
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(config.log_level)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(config.log_level)
            
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        cls._loggers[name] = logger
        return logger


class TextNormalizer:
    """Utilidades para normalización y limpieza de texto."""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        text_lower = text.lower()
        text_normalized = unicodedata.normalize('NFKD', text_lower)
        text_ascii = text_normalized.encode('ascii', 'ignore').decode('ascii')
        return text_ascii
    
    @staticmethod
    def remove_extra_whitespace(text: str) -> str:
        text_cleaned = re.sub(r'\s+', ' ', text)
        return text_cleaned.strip()
    
    @staticmethod
    def remove_special_characters(text: str, keep_spaces: bool = True) -> str:
        if keep_spaces:
            pattern = r'[^a-zA-Z0-9\s]'
        else:
            pattern = r'[^a-zA-Z0-9]'
        
        return re.sub(pattern, '', text)
    
    @staticmethod
    def clean_and_normalize(text: str) -> str:
        text_no_special = TextNormalizer.remove_special_characters(text, keep_spaces=True)
        text_no_whitespace = TextNormalizer.remove_extra_whitespace(text_no_special)
        text_normalized = TextNormalizer.normalize_text(text_no_whitespace)
        return text_normalized


class StringHelper:
    """Funciones auxiliares para manipulación de strings."""
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_words(text: str) -> list[str]:
        text_cleaned = TextNormalizer.clean_and_normalize(text)
        words = text_cleaned.split()
        return [word for word in words if len(word) > 0]
    
    @staticmethod
    def keywords_to_string(keywords: list[str], separator: str = ", ") -> str:
        return separator.join(keywords)
    
    @staticmethod
    def string_to_keywords(text: str, separator: str = ",") -> list[str]:
        keywords_raw = text.split(separator)
        keywords_cleaned = [kw.strip() for kw in keywords_raw if kw.strip()]
        return keywords_cleaned


class ValidationHelper:
    """Utilidades para validación de datos."""
    
    @staticmethod
    def is_valid_telegram_id(telegram_id: int) -> bool:
        return telegram_id > 0
    
    @staticmethod
    def is_valid_confidence_score(score: Optional[float]) -> bool:
        if score is None:
            return True
        return 0.0 <= score <= 1.0
    
    @staticmethod
    def is_valid_category_name(name: str) -> bool:
        if not name or len(name) == 0:
            return False
        if len(name) > 100:
            return False
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, name))


class FormatterHelper:
    """Utilidades para formateo de datos para presentación."""
    
    @staticmethod
    def format_confidence_score(score: Optional[float]) -> str:
        if score is None:
            return "N/A"
        return f"{score * 100:.1f}%"
    
    @staticmethod
    def format_category_info(category_name: str, keywords: list[str]) -> str:
        keywords_text = StringHelper.keywords_to_string(keywords)
        return f"📁 {category_name}\n🔑 Keywords: {keywords_text}"
    
    @staticmethod
    def format_message_stats(total: int, by_category: dict) -> str:
        lines = [f"📊 Total de mensajes: {total}\n"]
        
        for category_name, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            lines.append(f"  • {category_name}: {count} ({percentage:.1f}%)")
        
        return "\n".join(lines)