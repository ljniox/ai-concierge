"""
SQLite Connection Manager with WAL Mode and Connection Pooling

Provides centralized management for 3 SQLite databases:
- sdb_cate.sqlite: Core catechism data (EXISTING + new tables)
- temp_pages_system.db: Temporary secure pages
- core_system.db: System configuration

Features:
- WAL (Write-Ahead Logging) mode for concurrent read/write
- Connection pooling (20 connections per database)
- Automatic database initialization
- Health check capabilities

Research Decision: research.md#2 - SQLite Concurrency Strategy
"""

import aiosqlite
import asyncio
import os
from pathlib import Path
from typing import Dict, Optional
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class SQLiteManager:
    """
    Multi-database SQLite manager with connection pooling and WAL mode.

    Usage:
        manager = SQLiteManager()
        await manager.initialize()

        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute("SELECT * FROM inscriptions")
            results = await cursor.fetchall()
    """

    # Database configuration
    DATABASES = {
        'catechese': {
            'path_env': 'SQLITE_DB_PATH',
            'default_path': '/home/ubuntu/ai-concierge/sdb_cate.sqlite',
            'pool_size': 20,
            'description': 'Core catechism data (EXISTING + new enrollment tables)'
        },
        'temp_pages': {
            'path_env': 'SQLITE_TEMP_PAGES_DB',
            'default_path': './data/temp_pages_system.db',
            'pool_size': 20,
            'description': 'Temporary secure pages for document collection'
        },
        'core': {
            'path_env': 'SQLITE_CORE_DB',
            'default_path': './data/core_system.db',
            'pool_size': 20,
            'description': 'System configuration and application metadata'
        }
    }

    def __init__(self):
        self._pools: Dict[str, list] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize all database connections with WAL mode and pooling."""
        if self._initialized:
            logger.warning("SQLiteManager already initialized")
            return

        logger.info("Initializing SQLite Manager...")

        for db_name, config in self.DATABASES.items():
            db_path = os.getenv(config['path_env'], config['default_path'])

            # Ensure parent directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

            # Check if database exists
            db_exists = Path(db_path).exists()

            logger.info(f"Database '{db_name}': {db_path} (exists={db_exists})")

            # Initialize connection pool
            self._pools[db_name] = []
            self._locks[db_name] = asyncio.Lock()

            # Create initial connection to enable WAL mode
            if db_exists or db_name == 'catechese':  # catechese must already exist
                conn = await aiosqlite.connect(db_path)
                await self._configure_wal_mode(conn, db_name)
                await conn.close()

                # Pre-populate connection pool
                for _ in range(config['pool_size']):
                    pool_conn = await aiosqlite.connect(db_path)
                    await self._configure_connection(pool_conn)
                    self._pools[db_name].append(pool_conn)

                logger.info(f"  ✓ Pool created: {config['pool_size']} connections")
            else:
                logger.warning(f"  ⚠ Database '{db_name}' does not exist yet - will be created on first use")

        self._initialized = True
        logger.info("SQLite Manager initialized successfully")

    async def _configure_wal_mode(self, conn: aiosqlite.Connection, db_name: str):
        """
        Configure WAL mode and performance settings for concurrent access.

        WAL Mode Benefits:
        - Multiple readers can access database while writer is active
        - Improved concurrency for read-heavy workloads
        - Better performance for multi-threaded applications

        Research Decision: research.md#2
        """
        try:
            # Enable WAL mode
            await conn.execute("PRAGMA journal_mode=WAL")

            # Set synchronous mode to NORMAL (faster than FULL, still safe with WAL)
            await conn.execute("PRAGMA synchronous=NORMAL")

            # Set busy timeout to 5 seconds
            await conn.execute("PRAGMA busy_timeout=5000")

            # Enable foreign keys
            await conn.execute("PRAGMA foreign_keys=ON")

            await conn.commit()

            # Verify WAL mode is enabled
            cursor = await conn.execute("PRAGMA journal_mode")
            mode = await cursor.fetchone()

            if mode and mode[0].upper() == 'WAL':
                logger.info(f"  ✓ WAL mode enabled for '{db_name}'")
            else:
                logger.warning(f"  ⚠ WAL mode verification failed for '{db_name}': {mode}")

        except Exception as e:
            logger.error(f"  ✗ Failed to configure WAL mode for '{db_name}': {e}")
            raise

    async def _configure_connection(self, conn: aiosqlite.Connection):
        """Configure connection settings for optimal performance."""
        # Enable row factory for dict-like row access
        conn.row_factory = aiosqlite.Row

        # Set busy timeout
        await conn.execute("PRAGMA busy_timeout=5000")

        # Enable foreign keys
        await conn.execute("PRAGMA foreign_keys=ON")

    @asynccontextmanager
    async def get_connection(self, db_name: str):
        """
        Get a connection from the pool for the specified database.

        Args:
            db_name: Database identifier ('catechese', 'temp_pages', 'core')

        Yields:
            aiosqlite.Connection: Database connection

        Example:
            async with manager.get_connection('catechese') as conn:
                cursor = await conn.execute("SELECT * FROM inscriptions WHERE id = ?", (inscription_id,))
                result = await cursor.fetchone()
        """
        if not self._initialized:
            await self.initialize()

        if db_name not in self._pools:
            raise ValueError(f"Unknown database: {db_name}. Available: {list(self._pools.keys())}")

        # Get connection from pool
        async with self._locks[db_name]:
            if self._pools[db_name]:
                conn = self._pools[db_name].pop()
            else:
                # Pool exhausted, create new connection
                config = self.DATABASES[db_name]
                db_path = os.getenv(config['path_env'], config['default_path'])
                conn = await aiosqlite.connect(db_path)
                await self._configure_connection(conn)
                logger.warning(f"Pool exhausted for '{db_name}', created new connection")

        try:
            yield conn
        finally:
            # Return connection to pool
            async with self._locks[db_name]:
                self._pools[db_name].append(conn)

    async def execute_query(self, db_name: str, query: str, params: tuple = ()):
        """
        Execute a query and return results.

        Args:
            db_name: Database identifier
            query: SQL query
            params: Query parameters

        Returns:
            List of Row objects
        """
        async with self.get_connection(db_name) as conn:
            cursor = await conn.execute(query, params)
            return await cursor.fetchall()

    async def execute_write(self, db_name: str, query: str, params: tuple = ()):
        """
        Execute a write query (INSERT, UPDATE, DELETE).

        Args:
            db_name: Database identifier
            query: SQL query
            params: Query parameters

        Returns:
            int: Number of affected rows
        """
        async with self.get_connection(db_name) as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            return cursor.rowcount

    async def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all databases.

        Returns:
            Dict mapping database name to health status (True = healthy)
        """
        health = {}

        for db_name in self._pools.keys():
            try:
                async with self.get_connection(db_name) as conn:
                    cursor = await conn.execute("SELECT 1")
                    result = await cursor.fetchone()
                    health[f"sqlite_{db_name}"] = result[0] == 1
            except Exception as e:
                logger.error(f"Health check failed for '{db_name}': {e}")
                health[f"sqlite_{db_name}"] = False

        return health

    async def get_database_info(self, db_name: str) -> Dict:
        """
        Get information about a database.

        Args:
            db_name: Database identifier

        Returns:
            Dict containing database metadata
        """
        config = self.DATABASES[db_name]
        db_path = os.getenv(config['path_env'], config['default_path'])

        info = {
            'name': db_name,
            'path': db_path,
            'exists': Path(db_path).exists(),
            'pool_size': config['pool_size'],
            'description': config['description']
        }

        if info['exists']:
            # Get file size
            info['size_bytes'] = Path(db_path).stat().st_size
            info['size_mb'] = round(info['size_bytes'] / 1024 / 1024, 2)

            # Get table count
            try:
                async with self.get_connection(db_name) as conn:
                    cursor = await conn.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                    )
                    result = await cursor.fetchone()
                    info['table_count'] = result[0]

                    # Check WAL mode
                    cursor = await conn.execute("PRAGMA journal_mode")
                    mode = await cursor.fetchone()
                    info['journal_mode'] = mode[0] if mode else 'unknown'

            except Exception as e:
                logger.error(f"Failed to get info for '{db_name}': {e}")
                info['error'] = str(e)

        return info

    async def close_all(self):
        """Close all pooled connections."""
        logger.info("Closing all SQLite connections...")

        for db_name, pool in self._pools.items():
            for conn in pool:
                await conn.close()
            pool.clear()
            logger.info(f"  ✓ Closed connections for '{db_name}'")

        self._initialized = False
        logger.info("All SQLite connections closed")


# Global singleton instance
_manager_instance: Optional[SQLiteManager] = None


def get_sqlite_manager() -> SQLiteManager:
    """
    Get the global SQLite manager instance.

    Returns:
        SQLiteManager: Singleton instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SQLiteManager()
    return _manager_instance


# CLI for database management
if __name__ == "__main__":
    import sys
    import asyncio

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python sqlite_manager.py [init|info|health]")
            return

        command = sys.argv[1]
        manager = get_sqlite_manager()

        if command == "init":
            print("Initializing SQLite databases...")
            await manager.initialize()
            print("\n✓ Initialization complete")

            for db_name in manager.DATABASES.keys():
                info = await manager.get_database_info(db_name)
                print(f"\n{db_name}:")
                print(f"  Path: {info['path']}")
                print(f"  Exists: {info['exists']}")
                if info['exists']:
                    print(f"  Size: {info.get('size_mb', 0)} MB")
                    print(f"  Tables: {info.get('table_count', 0)}")
                    print(f"  Journal Mode: {info.get('journal_mode', 'unknown')}")

        elif command == "info":
            await manager.initialize()
            for db_name in manager.DATABASES.keys():
                info = await manager.get_database_info(db_name)
                print(f"\n{db_name}:")
                for key, value in info.items():
                    print(f"  {key}: {value}")

        elif command == "health":
            await manager.initialize()
            health = await manager.health_check()
            print("\nHealth Check Results:")
            for db, status in health.items():
                status_str = "✓ HEALTHY" if status else "✗ UNHEALTHY"
                print(f"  {db}: {status_str}")

        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, info, health")

        await manager.close_all()

    asyncio.run(main())
