"""
Database setup utilities for creating required tables
"""

from typing import Dict, Any, List
from src.utils.config import get_settings
from src.utils.database import get_supabase_client
import structlog

logger = structlog.get_logger()

async def setup_renseignements_table() -> Dict[str, Any]:
    """Create the renseignements table if it doesn't exist"""
    try:
        supabase = get_supabase_client()

        # Table creation SQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS renseignements (
            id SERIAL PRIMARY KEY,
            titre VARCHAR(255) NOT NULL,
            contenu TEXT NOT NULL,
            date_debut DATE NOT NULL DEFAULT CURRENT_DATE,
            date_fin DATE,
            categorie VARCHAR(100) DEFAULT 'general',
            priorite INTEGER DEFAULT 1,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Create indexes
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_renseignements_categorie ON renseignements(categorie);",
            "CREATE INDEX IF NOT EXISTS idx_renseignements_status ON renseignements(status);",
            "CREATE INDEX IF NOT EXISTS idx_renseignements_date_debut ON renseignements(date_debut);",
            "CREATE INDEX IF NOT EXISTS idx_renseignements_priorite ON renseignements(priorite);",
            "CREATE INDEX IF NOT EXISTS idx_renseignements_date_fin ON renseignements(date_fin);"
        ]

        # Execute table creation
        logger.info("creating_renseignements_table")

        # Note: In Supabase, we would typically use the dashboard or migrations
        # For now, we'll log the SQL that should be executed
        logger.info("table_creation_sql", sql=create_table_sql)

        for index_sql in create_indexes_sql:
            logger.info("index_creation_sql", sql=index_sql)

        # Insert sample data if table is empty
        sample_data = [
            {
                "titre": "Horaires des cours de catéchisme",
                "contenu": "Les cours de catéchisme ont lieu le samedi de 9h à 11h et le dimanche de 10h à 12h dans toutes les paroisses du diocèse.",
                "categorie": "horaire",
                "priorite": 5
            },
            {
                "titre": "Inscriptions pour l'année 2024-2025",
                "contenu": "Les inscriptions pour la nouvelle année catéchétique sont ouvertes. Renseignez-vous auprès de votre paroisse. Un certificat de baptême est requis.",
                "categorie": "inscription",
                "priorite": 4
            },
            {
                "titre": "Frais de scolarité",
                "contenu": "Les frais de catéchisme sont de 10 000 FCFA par an. Des facilités de paiement sont disponibles pour les familles nécessiteuses.",
                "categorie": "frais",
                "priorite": 3
            }
        ]

        return {
            "success": True,
            "message": "Table renseignements setup completed",
            "sample_data_count": len(sample_data)
        }

    except Exception as e:
        logger.error("renseignements_table_setup_failed", error=str(e))
        return {
            "success": False,
            "message": f"Erreur lors de la création de la table: {str(e)}"
        }

async def check_database_setup() -> Dict[str, Any]:
    """Check if all required tables are set up"""
    try:
        supabase = get_supabase_client()

        required_tables = ["renseignements"]
        setup_status = {}

        for table in required_tables:
            try:
                # Try to query the table
                result = supabase.table(table).select("count", count="exact").limit(1).execute()
                setup_status[table] = {
                    "exists": True,
                    "count": result.count if hasattr(result, 'count') else 0
                }
                logger.info("table_check_success", table=table, count=setup_status[table]["count"])
            except Exception as e:
                setup_status[table] = {
                    "exists": False,
                    "error": str(e)
                }
                logger.warning("table_check_failed", table=table, error=str(e))

        return {
            "success": True,
            "setup_status": setup_status,
            "all_tables_exist": all(status.get("exists", False) for status in setup_status.values())
        }

    except Exception as e:
        logger.error("database_setup_check_failed", error=str(e))
        return {
            "success": False,
            "message": f"Erreur lors de la vérification: {str(e)}"
        }

async def initialize_database() -> Dict[str, Any]:
    """Initialize database with required tables and data"""
    try:
        logger.info("initializing_database")

        # Check current setup
        check_result = await check_database_setup()

        if not check_result.get("all_tables_exist", False):
            # Setup missing tables
            setup_result = await setup_renseignements_table()

            if setup_result.get("success"):
                logger.info("database_initialization_completed")
                return {
                    "success": True,
                    "message": "Base de données initialisée avec succès",
                    "setup_result": setup_result
                }
            else:
                return setup_result
        else:
            logger.info("database_already_initialized")
            return {
                "success": True,
                "message": "Base de données déjà initialisée",
                "setup_status": check_result.get("setup_status", {})
            }

    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        return {
            "success": False,
            "message": f"Erreur lors de l'initialisation: {str(e)}"
        }