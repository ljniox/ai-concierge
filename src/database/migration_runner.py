"""
SQL Migration Runner for SQLite Databases

Executes SQL migration scripts with transaction rollback on error.
Supports verification queries to confirm migration success.

Usage:
    python migration_runner.py --db=/path/to/db.sqlite --migration=migrations/script.sql
"""

import aiosqlite
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Executes SQL migrations with transaction safety."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_exists = Path(db_path).exists()

    async def run_migration(self, migration_path: str) -> Dict:
        """
        Execute a SQL migration script.

        Args:
            migration_path: Path to SQL migration file

        Returns:
            Dict containing migration results:
                - success: bool
                - tables_created: list
                - indexes_created: list
                - triggers_created: list
                - error: str (if failed)
        """
        result = {
            'success': False,
            'tables_created': [],
            'indexes_created': [],
            'triggers_created': [],
            'error': None
        }

        if not self.db_exists:
            result['error'] = f"Database not found: {self.db_path}"
            logger.error(result['error'])
            return result

        migration_file = Path(migration_path)
        if not migration_file.exists():
            result['error'] = f"Migration file not found: {migration_path}"
            logger.error(result['error'])
            return result

        logger.info(f"Running migration: {migration_file.name}")
        logger.info(f"Target database: {self.db_path}")

        # Read migration SQL
        try:
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
        except Exception as e:
            result['error'] = f"Failed to read migration file: {e}"
            logger.error(result['error'])
            return result

        # Execute migration
        try:
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = aiosqlite.Row

            # Enable foreign keys
            await conn.execute("PRAGMA foreign_keys=ON")

            try:
                # Execute migration in transaction
                logger.info("Executing migration SQL...")
                await conn.executescript(migration_sql)
                await conn.commit()
                logger.info("✓ Migration SQL executed successfully")

                # Verify tables created
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
                    "('inscriptions', 'documents', 'paiements', 'profil_utilisateurs', 'action_logs')"
                )
                tables = await cursor.fetchall()
                result['tables_created'] = [row[0] for row in tables]

                # Verify indexes created
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
                )
                indexes = await cursor.fetchall()
                result['indexes_created'] = [row[0] for row in indexes]

                # Verify triggers created
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger' AND name IN "
                    "('inscriptions_updated_at', 'generate_numero_unique', 'update_classe_effectif_on_activation', 'update_classe_effectif_on_deactivation')"
                )
                triggers = await cursor.fetchall()
                result['triggers_created'] = [row[0] for row in triggers]

                result['success'] = True

                # Log verification results
                logger.info(f"✓ Tables created: {len(result['tables_created'])}")
                for table in result['tables_created']:
                    logger.info(f"  - {table}")

                logger.info(f"✓ Indexes created: {len(result['indexes_created'])}")
                for index in result['indexes_created'][:5]:  # Show first 5
                    logger.info(f"  - {index}")
                if len(result['indexes_created']) > 5:
                    logger.info(f"  ... and {len(result['indexes_created']) - 5} more")

                logger.info(f"✓ Triggers created: {len(result['triggers_created'])}")
                for trigger in result['triggers_created']:
                    logger.info(f"  - {trigger}")

            except Exception as e:
                # Rollback on error
                await conn.rollback()
                result['error'] = f"Migration failed: {e}"
                logger.error(f"✗ {result['error']}")
                logger.error("Transaction rolled back")
                raise

            finally:
                await conn.close()

        except Exception as e:
            if not result['error']:
                result['error'] = str(e)
            logger.error(f"Migration execution error: {e}")
            return result

        logger.info("✓ Migration completed successfully")
        return result

    async def verify_database(self) -> Dict:
        """
        Verify database structure after migration.

        Returns:
            Dict containing verification results
        """
        if not self.db_exists:
            return {'error': 'Database not found'}

        verification = {
            'tables': {},
            'journal_mode': None,
            'foreign_keys_enabled': None
        }

        try:
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = aiosqlite.Row

            # Check journal mode (should be WAL)
            cursor = await conn.execute("PRAGMA journal_mode")
            mode = await cursor.fetchone()
            verification['journal_mode'] = mode[0] if mode else 'unknown'

            # Check foreign keys
            cursor = await conn.execute("PRAGMA foreign_keys")
            fk = await cursor.fetchone()
            verification['foreign_keys_enabled'] = bool(fk[0]) if fk else False

            # Get table row counts
            for table in ['inscriptions', 'documents', 'paiements', 'profil_utilisateurs', 'action_logs']:
                try:
                    cursor = await conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = await cursor.fetchone()
                    verification['tables'][table] = {
                        'exists': True,
                        'row_count': count[0] if count else 0
                    }
                except:
                    verification['tables'][table] = {
                        'exists': False,
                        'row_count': 0
                    }

            await conn.close()

        except Exception as e:
            verification['error'] = str(e)
            logger.error(f"Verification failed: {e}")

        return verification


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Run SQL migrations on SQLite databases')
    parser.add_argument('--db', required=True, help='Path to SQLite database')
    parser.add_argument('--migration', required=True, help='Path to migration SQL file')
    parser.add_argument('--verify', action='store_true', help='Verify database after migration')

    args = parser.parse_args()

    runner = MigrationRunner(args.db)

    # Run migration
    result = await runner.run_migration(args.migration)

    if result['success']:
        print("\n" + "="*60)
        print("MIGRATION SUCCESSFUL")
        print("="*60)
        print(f"Database: {args.db}")
        print(f"Migration: {args.migration}")
        print(f"\nTables created: {len(result['tables_created'])}")
        for table in result['tables_created']:
            print(f"  ✓ {table}")
        print(f"\nIndexes created: {len(result['indexes_created'])}")
        print(f"Triggers created: {len(result['triggers_created'])}")

        # Verify if requested
        if args.verify:
            print("\n" + "="*60)
            print("VERIFICATION")
            print("="*60)
            verification = await runner.verify_database()

            print(f"Journal Mode: {verification.get('journal_mode', 'unknown')}")
            print(f"Foreign Keys: {'Enabled' if verification.get('foreign_keys_enabled') else 'Disabled'}")

            print("\nTable Status:")
            for table, info in verification.get('tables', {}).items():
                status = "✓" if info['exists'] else "✗"
                print(f"  {status} {table}: {info['row_count']} rows")

        print("\n" + "="*60)
        sys.exit(0)

    else:
        print("\n" + "="*60)
        print("MIGRATION FAILED")
        print("="*60)
        print(f"Error: {result['error']}")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
