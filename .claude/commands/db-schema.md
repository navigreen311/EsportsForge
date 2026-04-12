# Database Schema Update Command

## Database Architecture
- ORM: SQLAlchemy with async support (aiosqlite for dev, asyncpg for prod)
- Models: backend/app/models/
- DB setup: backend/app/db/base.py
- Tables auto-created via Base.metadata.create_all in app lifespan

## Migration Checklist
1. Add or update model in backend/app/models/[name].py
2. Import model in backend/app/models/__init__.py so Base.metadata knows about it
3. For production: use Alembic migrations (alembic/ directory)
4. For dev: delete esportsforge.db and restart to recreate all tables
5. Add indexes for frequently queried columns

## Security Rules
- ALWAYS filter by authenticated user_id in queries
- Use SQLAlchemy parameterized queries (never raw SQL with user input)
- Add created_at and updated_at to every new model

## Schema Change Required
$ARGUMENTS
