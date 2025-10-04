
# Telegram Categorizer Bot

Bot de Telegram que categoriza automáticamente mensajes usando palabras clave y similitud fuzzy (difflib).

## 🚀 Características

- ✅ Recibe mensajes de chats personales, grupos y canales
- ✅ Categorización automática con palabras clave
- ✅ Fallback con similitud fuzzy usando difflib
- ✅ Gestión de categorías vía comandos de Telegram
- ✅ Estadísticas de mensajes categorizados
- ✅ Exportación de categorías a CSV
- ✅ 100% Dockerizado
- ✅ Base de datos PostgreSQL

## 📋 Requisitos

- Docker & Docker Compose
- Token de bot de Telegram (obtener de @BotFather)

## 🛠️ Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repo>
cd telegram-categorizer
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` y configura:
- `TELEGRAM_BOT_TOKEN`: Tu token de BotFather
- `POSTGRES_PASSWORD`: Contraseña segura para PostgreSQL
- `DATABASE_URL`: Actualiza con tu contraseña

### 3. Construir y ejecutar

```bash
docker-compose up --build
```

### 4. Verificar que funciona

```bash
# Ver logs
docker-compose logs -f app

# Health check
curl http://localhost:8000/health
```

## 📱 Comandos del Bot

### Gestión de Categorías

- `/add_category <nombre> <palabra1, palabra2, ...>` o `/ac`
  - Ejemplo: `/ac trabajo reunion, meeting, oficina`

- `/list_categories` o `/lc`
  - Lista todas las categorías configuradas

- `/delete_category <nombre>` o `/dc`
  - Ejemplo: `/dc trabajo`

### Estadísticas

- `/stats` o `/s`
  - Muestra estadísticas de mensajes por categoría

### Exportación

- `/export_categories`
  - Descarga CSV con todas las categorías

### Mensajes Normales

Cualquier mensaje de texto será categorizado automáticamente y guardado en la base de datos.

## 🗂️ Estructura del Proyecto

```
telegram-categorizer/
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada
│   ├── config.py            # Configuración
│   ├── database.py          # Gestión de DB
│   ├── models.py            # Modelos SQLAlchemy
│   ├── utils.py             # Utilidades
│   └── bot/
│       ├── __init__.py
│       ├── categorizer.py   # Lógica de categorización
│       └── handlers.py      # Handlers de Telegram
├── categories.csv           # Categorías iniciales (opcional)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
```

## 🔧 Desarrollo

### Ver logs en tiempo real

```bash
docker-compose logs -f app
```

### Conectar a PostgreSQL

```bash
docker-compose exec postgres psql -U telegram_user -d telegram_db
```

### Reiniciar solo la app

```bash
docker-compose restart app
```

### Reconstruir después de cambios

```bash
docker-compose up --build
```

### Detener todo

```bash
docker-compose down
```