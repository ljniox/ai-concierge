"""
Database connection service for the automatic account creation system.

This module provides database connection management, session handling,
and database operations for Supabase PostgreSQL integration.
"""

import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional, List
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import ThreadedConnectionPool
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.utils.logging import get_logger
from src.utils.exceptions import DatabaseError, DatabaseConnectionError

logger = get_logger(__name__)


class DatabaseConfig:
    """Database configuration management."""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_password = os.getenv("SUPABASE_PASSWORD")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        # Connection pool settings
        self.min_connections = int(os.getenv("DB_MIN_CONNECTIONS", "2"))
        self.max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
        self.connection_timeout = int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))

        # Validate required environment variables
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate required database configuration."""
        required_vars = ["SUPABASE_URL", "SUPABASE_PASSWORD"]
        missing_vars = [var for var in required_vars if not getattr(self, var.lower())]

        if missing_vars:
            raise DatabaseConnectionError(
                f"Missing required database configuration: {', '.join(missing_vars)}"
            )

    @property
    def database_url(self) -> str:
        """Get the complete database URL for SQLAlchemy."""
        if not self.supabase_url or not self.supabase_password:
            raise DatabaseConnectionError("Supabase URL and password are required")

        # Extract database connection details from Supabase URL
        parsed_url = urlparse(self.supabase_url)

        # Supabase URL format: https://project-id.supabase.co
        # PostgreSQL connection: postgresql://postgres:password@db.project-id.supabase.co:5432/postgres
        project_id = parsed_url.netloc.split('.')[0]

        return (
            f"postgresql://postgres:{self.supabase_password}"
            f"@db.{project_id}.supabase.co:5432/postgres"
        )

    @property
    def psycopg2_dsn(self) -> Dict[str, Any]:
        """Get psycopg2 connection parameters."""
        if not self.supabase_url or not self.supabase_password:
            raise DatabaseConnectionError("Supabase URL and password are required")

        parsed_url = urlparse(self.supabase_url)
        project_id = parsed_url.netloc.split('.')[0]

        return {
            "host": f"db.{project_id}.supabase.co",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": self.supabase_password,
            "connect_timeout": self.connection_timeout,
            "cursor_factory": RealDictCursor
        }


class DatabaseService:
    """
    Database service for managing connections and operations.

    Provides connection pooling, session management, and database
    operations for the automatic account creation system.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._connection_pool: Optional[ThreadedConnectionPool] = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize database connections and session factory."""
        if self._initialized:
            return

        try:
            logger.info("Initializing database connections",
                       supabase_url=self.config.supabase_url)

            # Initialize SQLAlchemy engine
            self._initialize_sqlalchemy_engine()

            # Initialize psycopg2 connection pool
            self._initialize_connection_pool()

            self._initialized = True
            logger.info("Database connections initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize database connections",
                        error=str(e), error_type=type(e).__name__)
            raise DatabaseConnectionError(f"Database initialization failed: {e}")

    def _initialize_sqlalchemy_engine(self) -> None:
        """Initialize SQLAlchemy engine with connection pooling."""
        database_url = self.config.database_url

        # Create engine with optimized settings for Supabase
        self._engine = create_engine(
            database_url,
            pool_size=self.config.min_connections,
            max_overflow=self.config.max_connections - self.config.min_connections,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )

        # Create session factory
        self._session_factory = sessionmaker(bind=self._engine)

        # Set up connection event listeners
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for connection management."""
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set connection pragmas and settings."""
            with dbapi_connection.cursor() as cursor:
                # Set timezone to UTC
                cursor.execute("SET timezone = 'UTC'")

                # Set statement timeout
                cursor.execute("SET statement_timeout = '30s'")

                # Set application name for monitoring
                cursor.execute("SET application_name = 'ai_concierge_account_creation'")

        @event.listens_for(self._engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout."""
            logger.debug("Database connection checked out")

        @event.listens_for(self._engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin."""
            logger.debug("Database connection checked in")

    def _initialize_connection_pool(self) -> None:
        """Initialize psycopg2 connection pool for direct SQL operations."""
        try:
            self._connection_pool = ThreadedConnectionPool(
                minconn=self.config.min_connections,
                maxconn=self.config.max_connections,
                **self.config.psycopg2_dsn
            )
            logger.info("Psycopg2 connection pool created",
                       min_connections=self.config.min_connections,
                       max_connections=self.config.max_connections)
        except Exception as e:
            logger.error("Failed to create psycopg2 connection pool",
                        error=str(e))
            raise DatabaseConnectionError(f"Connection pool creation failed: {e}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a SQLAlchemy session with automatic cleanup.

        Yields:
            SQLAlchemy session instance
        """
        if not self._initialized:
            self.initialize()

        if not self._session_factory:
            raise DatabaseConnectionError("Session factory not initialized")

        session = self._session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error("Database session error",
                        error=str(e), error_type=type(e).__name__)
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            session.close()

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """
        Get a direct psycopg2 connection with automatic cleanup.

        Yields:
            Psycopg2 connection instance
        """
        if not self._initialized:
            self.initialize()

        if not self._connection_pool:
            raise DatabaseConnectionError("Connection pool not initialized")

        connection = None
        try:
            connection = self._connection_pool.getconn()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error("Database connection error",
                        error=str(e), error_type=type(e).__name__)
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if connection:
                self._connection_pool.putconn(connection)

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of result rows as dictionaries

        Raises:
            DatabaseError: If query execution fails
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    results = cursor.fetchall()

                    # Convert RealDictCursor results to regular dictionaries
                    return [dict(row) for row in results]

            except Exception as e:
                logger.error("Query execution failed",
                            query=query, params=params, error=str(e))
                raise DatabaseError(f"Query execution failed: {e}")

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an UPDATE/INSERT/DELETE query and return affected rows.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Number of affected rows

        Raises:
            DatabaseError: If query execution fails
        """
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount

            except Exception as e:
                conn.rollback()
                logger.error("Update query failed",
                            query=query, params=params, error=str(e))
                raise DatabaseError(f"Update query failed: {e}")

    def execute_batch_insert(
        self,
        table: str,
        columns: List[str],
        values: List[tuple]
    ) -> int:
        """
        Execute batch INSERT operation for better performance.

        Args:
            table: Target table name
            columns: List of column names
            values: List of value tuples

        Returns:
            Number of rows inserted

        Raises:
            DatabaseError: If batch insert fails
        """
        if not values:
            return 0

        with self.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    # Build the query
                    placeholders = ', '.join(['%s'] * len(columns))
                    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

                    # Execute batch insert
                    execute_values(cursor, query, values)
                    conn.commit()
                    return len(values)

            except Exception as e:
                conn.rollback()
                logger.error("Batch insert failed",
                            table=table, columns=columns,
                            row_count=len(values), error=str(e))
                raise DatabaseError(f"Batch insert failed: {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check.

        Returns:
            Dictionary with health check results
        """
        try:
            if not self._initialized:
                return {
                    "status": "unhealthy",
                    "error": "Database not initialized",
                    "timestamp": None
                }

            # Test SQLAlchemy connection
            with self.get_session() as session:
                session.execute("SELECT 1")
                sqlalchemy_status = "healthy"

            # Test psycopg2 connection pool
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version_info = cursor.fetchone()
                    psycopg2_status = "healthy"

            # Get connection pool statistics
            pool_stats = {}
            if self._connection_pool:
                pool_stats = {
                    "min_connections": self._connection_pool.minconn,
                    "max_connections": self._connection_pool.maxconn,
                    "closed_connections": self._connection_pool.closed
                }

            return {
                "status": "healthy",
                "sqlalchemy_status": sqlalchemy_status,
                "psycopg2_status": psycopg2_status,
                "pool_statistics": pool_stats,
                "database_version": version_info.get("version", "Unknown") if version_info else None,
                "timestamp": self._get_current_timestamp()
            }

        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self._get_current_timestamp()
            }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        if not self._connection_pool:
            return {"error": "Connection pool not initialized"}

        try:
            return {
                "min_connections": self._connection_pool.minconn,
                "max_connections": self._connection_pool.maxconn,
                "closed_connections": self._connection_pool.closed,
                "connections_in_use": self._connection_pool._used,
                "available_connections": len(self._connection_pool._pool)
            }
        except Exception as e:
            logger.error("Failed to get pool statistics", error=str(e))
            return {"error": str(e)}

    def close(self) -> None:
        """Close all database connections."""
        try:
            if self._connection_pool:
                self._connection_pool.closeall()
                logger.info("Psycopg2 connection pool closed")

            if self._engine:
                self._engine.dispose()
                logger.info("SQLAlchemy engine disposed")

            self._initialized = False
            logger.info("Database connections closed")

        except Exception as e:
            logger.error("Error closing database connections", error=str(e))

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global database service instance
_database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """
    Get the global database service instance.

    Returns:
        DatabaseService instance
    """
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service


def initialize_database() -> DatabaseService:
    """
    Initialize the global database service.

    Returns:
        Initialized DatabaseService instance
    """
    service = get_database_service()
    service.initialize()
    return service


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session from the global service.

    Yields:
        SQLAlchemy session instance
    """
    service = get_database_service()
    with service.get_session() as session:
        yield session


@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Get a database connection from the global service.

    Yields:
        Psycopg2 connection instance
    """
    service = get_database_service()
    with service.get_connection() as connection:
        yield connection


def execute_sql_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Execute a SQL query using the global database service.

    Args:
        query: SQL query to execute
        params: Query parameters

    Returns:
        List of result rows as dictionaries
    """
    service = get_database_service()
    return service.execute_query(query, params)


def execute_sql_update(query: str, params: Optional[tuple] = None) -> int:
    """
    Execute an SQL update using the global database service.

    Args:
        query: SQL query to execute
        params: Query parameters

    Returns:
        Number of affected rows
    """
    service = get_database_service()
    return service.execute_update(query, params)


def check_database_health() -> Dict[str, Any]:
    """
    Check database health using the global service.

    Returns:
        Dictionary with health check results
    """
    service = get_database_service()
    return service.health_check()