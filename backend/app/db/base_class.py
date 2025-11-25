"""
Database Base Class (Settings-Free)
Declarative base for SQLAlchemy ORM models without config dependencies.
Used by Alembic migrations to avoid circular imports and config parsing.
"""
from sqlalchemy.ext.declarative import declarative_base

# Declarative base for all ORM models
Base = declarative_base()
