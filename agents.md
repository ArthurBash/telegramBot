# Agent Instructions - Telegram Categorizer Backend

## Contexto del Proyecto

Estás desarrollando un backend MVP en Python que recibe mensajes de Telegram (personal, grupos, canales) y los categoriza automáticamente en una base de datos PostgreSQL usando palabras clave y similitud fuzzy con difflib.

## Stack Tecnológico

- **Python 3.11+**
- **FastAPI** - Framework web minimalista
- **python-telegram-bot** - Cliente Telegram con polling
- **SQLAlchemy** - ORM para PostgreSQL
- **PostgreSQL** - Base de datos
- **Docker & Docker Compose** - Containerización
- **asyncpg** - Driver asíncrono PostgreSQL
- **difflib** - Comparación fuzzy de strings (built-in)

## Arquitectura del Sistema

### Componentes Principales

1. **Bot de Telegram**: Recibe mensajes vía polling de cualquier tipo de chat
2. **Categorizador**: Clasifica mensajes usando palabras clave + difflib
3. **Base de Datos**: Almacena mensajes categorizados y definiciones de categorías
4. **Comandos Admin**: Gestión de categorías vía Telegram

### Estructura del Proyecto

```
telegram-categorizer/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Bot + FastAPI mínima
│   ├── config.py              # Variables de entorno
│   ├── database.py            # DB connection
│   ├── models.py              # Modelos SQLAlchemy
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers.py        # Message + command handlers
│   │   └── categorizer.py     # Lógica difflib + keywords
│   └── utils.py               # Helpers y logger
├── categories.csv             # Categorías iniciales (opcional)
├── docker-compose.yml         # app + postgres
├── Dockerfile
├── requirements.txt
├── .env
├── test_categorizer.py        # Script de prueba por consola
└── README.md
```

## Reglas de Código

### Convenciones de Nomenclatura

1. **Variables y funciones**: `snake_case`
   ```python
   user_message = "texto"
   def calculate_similarity_score():
   ```

2. **Clases**: `CamelCase`
   ```python
   class MessageCategorizer:
   class TelegramBotHandler:
   ```

3. **Constantes**: `UPPER_SNAKE_CASE`
   ```python
   DEFAULT_CATEGORY = "sin_categoria"
   SIMILARITY_THRESHOLD = 0.7
   ```

4. **Variables descriptivas**: Nombres claros y explícitos
   ```python
   # ✅ Correcto
   telegram_user_id = message.from_user.id
   category_confidence_score = 0.85
   
   # ❌ Evitar
   uid = message.from_user.id
   score = 0.85
   ```

### Paradigma Orientado a Objetos

**CRÍTICO**: Todo el código debe seguir OOP (Object-Oriented Programming)

1. **Usa clases para encapsular lógica**:
   ```python
   class MessageCategorizer:
       def __init__(self, similarity_threshold: float):
           self.similarity_threshold = similarity_threshold
       
       def categorize_message(self, message_text: str) -> dict:
           # Lógica de categorización
   ```

2. **Evita funciones sueltas**: Agrupa funciones relacionadas en clases
   ```python
   # ❌ Evitar
   def categorize(text):
       pass
   
   # ✅ Correcto
   class MessageCategorizer:
       def categorize(self, text):
           pass
   ```

3. **Inyección de dependencias**: Pasa dependencias en el constructor
   ```python
   class TelegramBotHandler:
       def __init__(self, categorizer: MessageCategorizer, database_session):
           self.categorizer = categorizer
           self.db_session = database_session
   ```

### Comentarios en Funciones

**OBLIGATORIO**: Todas las funciones nuevas deben estar comentadas

```python
class MessageCategorizer:
    def find_best_category_match(self, message_text: str, categories: list) -> tuple:
        """
        Encuentra la mejor categoría para un mensaje usando palabras clave y similitud fuzzy.
        
        Args:
            message_text (str): Texto del mensaje a categorizar
            categories (list): Lista de categorías disponibles con sus keywords
            
        Returns:
            tuple: (nombre_categoria, confidence_score)
                - nombre_categoria: Nombre de la categoría seleccionada
                - confidence_score: Puntaje de confianza entre 0 y 1
                
        Proceso:
            1. Normaliza el texto del mensaje
            2. Busca coincidencias exactas con palabras clave
            3. Si no encuentra, usa difflib.SequenceMatcher para similitud
            4. Retorna la categoría con mayor score
        """
        pass
```

### Enfoque MVP

1. **Simplicidad primero**: Implementa la solución más simple que funcione
2. **No optimización prematura**: Primero que funcione, luego optimiza
3. **Funcionalidad básica completa**: Todas las features core deben funcionar
4. **Sin features extras**: Solo lo estrictamente necesario

## Esquema de Base de Datos

### Tabla: messages
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    telegram_chat_id BIGINT NOT NULL,
    telegram_user_id BIGINT NOT NULL,
    username VARCHAR(255),
    chat_type VARCHAR(50),
    message_text TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Tabla: categories
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    keywords TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Flujo de Datos

1. **Mensaje recibido** → Bot Handler captura mensaje
2. **Extracción de datos** → Parse de información del mensaje
3. **Categorización** → MessageCategorizer determina categoría
4. **Persistencia** → DatabaseService guarda en PostgreSQL
5. **Confirmación** → Respuesta al usuario (opcional)

## Lógica del Categorizador

### Algoritmo de Categorización

```python
class MessageCategorizer:
    def categorize(self, message_text: str) -> dict:
        """
        1. Normalizar texto (minúsculas, sin acentos)
        2. Para cada categoría:
           a. Buscar coincidencias exactas en palabras clave
           b. Si no hay coincidencia exacta, calcular similitud con difflib
        3. Seleccionar categoría con mayor confidence_score
        4. Si ninguna supera el threshold, asignar "sin_categoria"
        """
```

### Uso de difflib

```python
from difflib import SequenceMatcher

def calculate_text_similarity(text_a: str, text_b: str) -> float:
    """
    Calcula similitud entre dos textos usando SequenceMatcher.
    
    Returns:
        float: Score entre 0.0 y 1.0
    """
    return SequenceMatcher(None, text_a, text_b).ratio()
```

## Comandos de Telegram

### Comandos Admin Requeridos

- `/add_category <nombre> <palabra1, palabra2, ...>` - Añadir nueva categoría
- `/ac <nombre> <palabra1, palabra2, ...>` - Añadir nueva categoría

- `/list_categories` - Listar todas las categorías
- `/lc` - Listar todas las categorías

- `/delete_category <nombre>` - Eliminar categoría
- `/dc <nombre>` - Eliminar categoría

- `/stats` - Estadísticas de mensajes por categoría
- `/s` - Estadísticas de mensajes por categoría

- `/export_categories` - Exportar categorías a CSV


## Variables de Entorno

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/telegram_db
POSTGRES_USER=telegram_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=telegram_db

# App
LOG_LEVEL=INFO
SIMILARITY_THRESHOLD=0.7
```

## Docker Configuration

### Services
- **postgres**: PostgreSQL 15
- **app**: Aplicación Python con FastAPI + Bot

### Networking
- Red interna Docker para comunicación entre servicios
- Puerto 8000 expuesto para FastAPI (health check)

## Testing

### Script de Prueba por Consola

Archivo `test_categorizer.py` debe:
1. Importar solo el categorizador (sin dependencias de Telegram/DB)
2. Simular diferentes textos de entrada
3. Mostrar resultados de categorización
4. Ejecutarse con: `docker-compose exec app python test_categorizer.py`

## Logging

- Usar Python logging module
- Configurar en `utils.py`
- Niveles: DEBUG, INFO, ERROR
- Format: `[%(asctime)s] %(levelname)s - %(name)s - %(message)s`

## Manejo de Errores

```python
class MessageCategorizer:
    def categorize(self, message_text: str) -> dict:
        """Categoriza un mensaje de texto."""
        try:
            # Lógica de categorización
            pass
        except Exception as error:
            self.logger.error(f"Error categorizando mensaje: {error}")
            return {
                'category': 'sin_categoria',
                'confidence_score': 0.0,
                'error': str(error)
            }
```

## Prioridades de Implementación

1. **Fase 1**: Docker + PostgreSQL + Conexión DB
2. **Fase 2**: Modelos SQLAlchemy + Migraciones
3. **Fase 3**: Categorizador básico (palabras clave)
4. **Fase 4**: Integración difflib (similitud fuzzy)
5. **Fase 5**: Bot de Telegram (recepción mensajes)
6. **Fase 6**: Comandos admin
7. **Fase 7**: Script de testing por consola

## Criterios de Éxito MVP

- ✅ Bot recibe mensajes de cualquier chat
- ✅ Categorización funciona con palabras clave
- ✅ Fallback con difflib cuando no hay match exacto
- ✅ Mensajes se guardan en PostgreSQL
- ✅ Comandos admin funcionan vía Telegram
- ✅ Script de prueba funciona sin Telegram
- ✅ Todo dockerizado y ejecutable con `docker-compose up`

## Notas Importantes

- **No usar localStorage/sessionStorage**: No aplicable en backend
- **No webhooks**: Usar polling para simplicidad del MVP
- **No API REST**: Solo bot de Telegram por ahora
- **Categorías dinámicas**: Cargables vía comandos o CSV opcional
- **Asincronía**: Usar async/await donde sea apropiado (DB, Bot)

## Referencias Rápidas

- python-telegram-bot docs: https://docs.python-telegram-bot.org/
- SQLAlchemy async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- difflib: https://docs.python.org/3/library/difflib.html

---

**Versión**: 1.0  
**Última actualización**: Paso a paso definido  
**Próximo milestone**: Implementación Fase 1 (Docker + PostgreSQL)