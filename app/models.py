"""
Modelos de base de datos usando SQLAlchemy ORM.

Este módulo define las tablas de la base de datos para almacenar
mensajes categorizados y definiciones de categorías.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Clase base para todos los modelos de SQLAlchemy."""
    pass


class Category(Base):
    """
    Modelo para almacenar categorías y sus palabras clave asociadas.
    
    Una categoría contiene un nombre único y un array de palabras clave
    que se usan para clasificar mensajes entrantes.
    
    Attributes:
        id: Identificador único autoincremental
        name: Nombre único de la categoría
        keywords: Lista de palabras clave para matching
        created_at: Timestamp de creación del registro
        updated_at: Timestamp de última actualización
        messages: Relación con mensajes que pertenecen a esta categoría
    """
    
    __tablename__ = "categories"
    
    # Campos principales
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Relación con mensajes
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="category_ref",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """Representación legible del objeto Category."""
        return f"<Category(id={self.id}, name='{self.name}', keywords_count={len(self.keywords)})>"
    
    def to_dict(self) -> dict:
        """
        Convierte el objeto Category a diccionario.
        
        Returns:
            dict: Representación en diccionario del objeto
        """
        return {
            "id": self.id,
            "name": self.name,
            "keywords": self.keywords,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }


class Message(Base):
    """
    Modelo para almacenar mensajes recibidos de Telegram con su categorización.
    
    Cada mensaje incluye información del usuario, chat, texto original,
    categoría asignada y score de confianza de la categorización.
    
    Attributes:
        id: Identificador único autoincremental
        telegram_chat_id: ID del chat de Telegram
        telegram_user_id: ID del usuario de Telegram
        username: Nombre de usuario de Telegram (opcional)
        chat_type: Tipo de chat ('private', 'group', 'channel')
        message_text: Texto completo del mensaje
        category: Nombre de la categoría asignada
        confidence_score: Score de confianza de la categorización (0.0 a 1.0)
        created_at: Timestamp de recepción del mensaje
        category_ref: Relación con el objeto Category
    """
    
    __tablename__ = "messages"
    
    # Campos principales
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    chat_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Contenido del mensaje
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Categorización
    category: Mapped[str] = mapped_column(
        String(100), 
        ForeignKey("categories.name", ondelete="SET NULL"),
        nullable=False,
        index=True
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        index=True
    )
    
    # Relación con categoría
    category_ref: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="messages"
    )
    
    # Índices compuestos para consultas comunes
    __table_args__ = (
        Index("idx_messages_category_created", "category", "created_at"),
        Index("idx_messages_user_category", "telegram_user_id", "category"),
    )
    
    def __repr__(self) -> str:
        """Representación legible del objeto Message."""
        text_preview = self.message_text[:50] + "..." if len(self.message_text) > 50 else self.message_text
        return f"<Message(id={self.id}, category='{self.category}', text='{text_preview}')>"
    
    def to_dict(self) -> dict:
        """
        Convierte el objeto Message a diccionario.
        
        Returns:
            dict: Representación en diccionario del objeto
        """
        return {
            "id": self.id,
            "telegram_chat_id": self.telegram_chat_id,
            "telegram_user_id": self.telegram_user_id,
            "username": self.username,
            "chat_type": self.chat_type,
            "message_text": self.message_text,
            "category": self.category,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class MessageStatistics:
    """
    Clase de utilidad para calcular estadísticas de mensajes.
    
    No es un modelo de base de datos, sino una clase helper para
    realizar cálculos y agregaciones sobre los mensajes.
    """
    
    @staticmethod
    def get_category_distribution(messages: List[Message]) -> dict:
        """
        Calcula la distribución de mensajes por categoría.
        
        Args:
            messages: Lista de objetos Message
            
        Returns:
            dict: Diccionario con conteo por categoría
        """
        distribution = {}
        for message in messages:
            category_name = message.category
            distribution[category_name] = distribution.get(category_name, 0) + 1
        return distribution
    
    @staticmethod
    def get_average_confidence_by_category(messages: List[Message]) -> dict:
        """
        Calcula el promedio de confidence score por categoría.
        
        Args:
            messages: Lista de objetos Message
            
        Returns:
            dict: Diccionario con promedio de confidence por categoría
        """
        category_scores = {}
        category_counts = {}
        
        for message in messages:
            if message.confidence_score is not None:
                category_name = message.category
                current_sum = category_scores.get(category_name, 0)
                current_count = category_counts.get(category_name, 0)
                
                category_scores[category_name] = current_sum + message.confidence_score
                category_counts[category_name] = current_count + 1
        
        averages = {}
        for category_name, total_score in category_scores.items():
            count = category_counts[category_name]
            averages[category_name] = total_score / count if count > 0 else 0.0
        
        return averages