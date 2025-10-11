"""
Data Retention Service

Enforces GDPR-compliant data retention policies across all databases.
Handles automatic cleanup and anonymization of expired data.

Retention Policies (FR-054-055):
- Audit logs: 2 years, then anonymize/delete
- Documents: 7 years after enrollment completion
- Payment records: 10 years (financial requirement)
- User profiles: Keep active, anonymize inactive after 5 years

Constitution Principle V: Security and GDPR compliance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..database.sqlite_manager import get_sqlite_manager
from ..services.audit_service import get_audit_service

logger = logging.getLogger(__name__)


class RetentionService:
    """
    Data retention service for GDPR compliance.

    Handles automated cleanup of expired data while preserving
    necessary records for legal and operational requirements.
    """

    def __init__(self):
        self.manager = get_sqlite_manager()
        self.audit_service = get_audit_service()

        # Retention periods in days
        self.RETENTION_PERIODS = {
            'audit_logs': 365 * 2,  # 2 years (FR-054)
            'documents': 365 * 7,   # 7 years
            'payments': 365 * 10,   # 10 years (financial requirement)
            'temp_pages': 7,        # 7 days (FR-043)
            'inactive_profiles': 365 * 5  # 5 years
        }

    async def enforce_all_retention_policies(self) -> Dict[str, Any]:
        """
        Enforce all retention policies.

        Returns:
            Dict: Summary of cleanup operations performed
        """
        logger.info("Starting retention policy enforcement")

        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'policies_enforced': [],
            'total_records_cleaned': 0,
            'errors': []
        }

        try:
            # Enforce audit log retention
            audit_result = await self.enforce_audit_log_retention()
            results['policies_enforced'].append(audit_result)

            # Enforce document retention
            doc_result = await self.enforce_document_retention()
            results['policies_enforced'].append(doc_result)

            # Enforce payment retention
            payment_result = await self.enforce_payment_retention()
            results['policies_enforced'].append(payment_result)

            # Clean expired temporary pages
            temp_result = await self.clean_expired_temp_pages()
            results['policies_enforced'].append(temp_result)

            # Anonymize inactive user profiles
            profile_result = await self.anonymize_inactive_profiles()
            results['policies_enforced'].append(profile_result)

            # Calculate total
            results['total_records_cleaned'] = sum(
                policy.get('records_cleaned', 0) for policy in results['policies_enforced']
            )

            logger.info(f"Retention policy enforcement completed: {results['total_records_cleaned']} records processed")

            # Log the cleanup operation
            await self.audit_service.log_action(
                user_id="system-retention",
                action_type="system_maintenance",
                entity_type="retention_policy",
                entity_id="enforcement-" + datetime.utcnow().strftime("%Y%m%d"),
                details=results,
                statut_action="succes"
            )

            return results

        except Exception as e:
            logger.error(f"Retention policy enforcement failed: {e}")
            results['errors'].append(str(e))

            # Log the failure
            await self.audit_service.log_action(
                user_id="system-retention",
                action_type="system_maintenance",
                entity_type="retention_policy",
                entity_id="enforcement-" + datetime.utcnow().strftime("%Y%m%d"),
                details={"error": str(e)},
                statut_action="echec",
                error_message=str(e)
            )

            return results

    async def enforce_audit_log_retention(self) -> Dict[str, Any]:
        """
        Enforce 2-year retention for audit logs (FR-054-055).

        Strategy: Anonymize IP addresses and details, keep basic action history
        """
        logger.info("Enforcing audit log retention policy (2 years)")

        cutoff_date = datetime.utcnow() - timedelta(days=self.RETENTION_PERIODS['audit_logs'])

        try:
            async with self.manager.get_connection('catechese') as conn:
                # Anonymize approach: Remove sensitive data but keep action history
                update_query = """
                UPDATE action_logs
                SET ip_address = NULL,
                    user_agent = 'Anonymized',
                    details = '{"anonymized": true, "retention_applied": true}'
                WHERE timestamp < ?
                """

                cursor = await conn.execute(update_query, (cutoff_date.isoformat(),))
                anonymized_count = cursor.rowcount
                await conn.commit()

                result = {
                    'policy': 'audit_logs',
                    'strategy': 'anonymize',
                    'cutoff_date': cutoff_date.isoformat(),
                    'records_anonymized': anonymized_count,
                    'records_cleaned': anonymized_count
                }

                logger.info(f"Anonymized {anonymized_count} audit log entries")
                return result

        except Exception as e:
            logger.error(f"Failed to enforce audit log retention: {e}")
            return {
                'policy': 'audit_logs',
                'strategy': 'anonymize',
                'error': str(e),
                'records_cleaned': 0
            }

    async def enforce_document_retention(self) -> Dict[str, Any]:
        """
        Enforce 7-year retention for documents (post-enrollment completion).

        Strategy: Delete document files and metadata for completed enrollments older than 7 years
        """
        logger.info("Enforcing document retention policy (7 years)")

        cutoff_date = datetime.utcnow() - timedelta(days=self.RETENTION_PERIODS['documents'])

        try:
            async with self.manager.get_connection('catechese') as conn:
                # Find completed enrollments older than 7 years
                query = """
                SELECT i.id, i.statut, i.updated_at
                FROM inscriptions i
                WHERE i.statut = 'active'
                AND i.updated_at < ?
                """

                cursor = await conn.execute(query, (cutoff_date.isoformat(),))
                old_enrollments = await cursor.fetchall()

                if not old_enrollments:
                    return {
                        'policy': 'documents',
                        'strategy': 'delete',
                        'cutoff_date': cutoff_date.isoformat(),
                        'enrollments_processed': 0,
                        'records_cleaned': 0
                    }

                # Delete documents for old enrollments
                enrollment_ids = [row['id'] for row in old_enrollments]

                delete_query = "DELETE FROM documents WHERE inscription_id IN ({})".format(
                    ','.join(['?' for _ in enrollment_ids])
                )

                cursor = await conn.execute(delete_query, enrollment_ids)
                deleted_count = cursor.rowcount
                await conn.commit()

                # TODO: Also delete files from MinIO storage
                # This would require MinIO client integration

                result = {
                    'policy': 'documents',
                    'strategy': 'delete',
                    'cutoff_date': cutoff_date.isoformat(),
                    'enrollments_processed': len(old_enrollments),
                    'records_cleaned': deleted_count
                }

                logger.info(f"Deleted {deleted_count} documents for {len(old_enrollments)} old enrollments")
                return result

        except Exception as e:
            logger.error(f"Failed to enforce document retention: {e}")
            return {
                'policy': 'documents',
                'strategy': 'delete',
                'error': str(e),
                'records_cleaned': 0
            }

    async def enforce_payment_retention(self) -> Dict[str, Any]:
        """
        Enforce 10-year retention for payment records (financial requirement).

        Strategy: Keep summary data, delete detailed transaction data older than 10 years
        """
        logger.info("Enforcing payment retention policy (10 years)")

        cutoff_date = datetime.utcnow() - timedelta(days=self.RETENTION_PERIODS['payments'])

        try:
            async with self.manager.get_connection('catechese') as conn:
                # For financial records, we might want to keep summary data
                # For now, implement a conservative approach

                # Get old payments count first
                count_query = "SELECT COUNT(*) as count FROM paiements WHERE soumis_at < ?"
                cursor = await conn.execute(count_query, (cutoff_date.isoformat(),))
                old_payments_count = (await cursor.fetchone())['count']

                if old_payments_count == 0:
                    return {
                        'policy': 'payments',
                        'strategy': 'keep',
                        'cutoff_date': cutoff_date.isoformat(),
                        'records_processed': 0,
                        'records_cleaned': 0
                    }

                # For financial compliance, we'll keep all payment records
                # but anonymize sensitive metadata
                update_query = """
                UPDATE paiements
                SET metadata = '{"retained": true, "retention_applied": true}'
                WHERE soumis_at < ?
                AND metadata IS NOT NULL
                """

                cursor = await conn.execute(update_query, (cutoff_date.isoformat(),))
                anonymized_count = cursor.rowcount
                await conn.commit()

                result = {
                    'policy': 'payments',
                    'strategy': 'keep_anonymize',
                    'cutoff_date': cutoff_date.isoformat(),
                    'records_processed': old_payments_count,
                    'records_anonymized': anonymized_count,
                    'records_cleaned': anonymized_count
                }

                logger.info(f"Processed {old_payments_count} payment records, anonymized {anonymized_count}")
                return result

        except Exception as e:
            logger.error(f"Failed to enforce payment retention: {e}")
            return {
                'policy': 'payments',
                'strategy': 'keep_anonymize',
                'error': str(e),
                'records_cleaned': 0
            }

    async def clean_expired_temp_pages(self) -> Dict[str, Any]:
        """
        Clean expired temporary pages (7 days per FR-043).

        Strategy: Delete expired temporary pages and associated data
        """
        logger.info("Cleaning expired temporary pages (7 days)")

        try:
            async with self.manager.get_connection('temp_pages') as conn:
                # Delete expired pages
                delete_query = "DELETE FROM pages_temporaires WHERE expires_at < datetime('now')"
                cursor = await conn.execute(delete_query)
                deleted_count = cursor.rowcount
                await conn.commit()

                result = {
                    'policy': 'temp_pages',
                    'strategy': 'delete',
                    'records_cleaned': deleted_count
                }

                logger.info(f"Deleted {deleted_count} expired temporary pages")
                return result

        except Exception as e:
            logger.error(f"Failed to clean expired temp pages: {e}")
            return {
                'policy': 'temp_pages',
                'strategy': 'delete',
                'error': str(e),
                'records_cleaned': 0
            }

    async def anonymize_inactive_profiles(self) -> Dict[str, Any]:
        """
        Anonymize inactive user profiles (5 years).

        Strategy: Anonymize personal data for users inactive for 5+ years
        """
        logger.info("Anonymizing inactive user profiles (5 years)")

        cutoff_date = datetime.utcnow() - timedelta(days=self.RETENTION_PERIODS['inactive_profiles'])

        try:
            async with self.manager.get_connection('catechese') as conn:
                # Find inactive profiles (no recent login, no active enrollments)
                query = """
                SELECT pu.user_id, pu.nom, pu.prenom, pu.telephone, pu.email
                FROM profil_utilisateurs pu
                LEFT JOIN inscriptions i ON pu.user_id = i.parent_id AND i.statut = 'active'
                WHERE pu.derniere_connexion < ?
                OR pu.derniere_connexion IS NULL
                AND i.id IS NULL
                AND pu.role != 'super_admin'  -- Don't anonymize admins
                """

                cursor = await conn.execute(query, (cutoff_date.isoformat(),))
                inactive_profiles = await cursor.fetchall()

                if not inactive_profiles:
                    return {
                        'policy': 'inactive_profiles',
                        'strategy': 'anonymize',
                        'cutoff_date': cutoff_date.isoformat(),
                        'profiles_processed': 0,
                        'records_cleaned': 0
                    }

                # Anonymize profiles
                user_ids = [profile['user_id'] for profile in inactive_profiles]

                update_query = """
                UPDATE profil_utilisateurs
                SET nom = 'Anonymized',
                    prenom = 'User',
                    email = NULL,
                    code_parent_hash = NULL,
                    metadata = '{"anonymized": true, "retention_applied": true}'
                WHERE user_id IN ({})
                """.format(','.join(['?' for _ in user_ids]))

                cursor = await conn.execute(update_query, user_ids)
                anonymized_count = cursor.rowcount
                await conn.commit()

                result = {
                    'policy': 'inactive_profiles',
                    'strategy': 'anonymize',
                    'cutoff_date': cutoff_date.isoformat(),
                    'profiles_processed': len(inactive_profiles),
                    'records_cleaned': anonymized_count
                }

                logger.info(f"Anonymized {anonymized_count} inactive user profiles")
                return result

        except Exception as e:
            logger.error(f"Failed to anonymize inactive profiles: {e}")
            return {
                'policy': 'inactive_profiles',
                'strategy': 'anonymize',
                'error': str(e),
                'records_cleaned': 0
            }

    async def get_retention_status(self) -> Dict[str, Any]:
        """
        Get status of data retention across all policies.

        Returns:
            Dict: Retention status and statistics
        """
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'policies': {},
            'total_records_at_risk': 0
        }

        try:
            # Check audit logs approaching retention limit
            for policy_name, retention_days in self.RETENTION_PERIODS.items():
                warning_date = datetime.utcnow() - timedelta(days=retention_days - 30)  # 30-day warning

                if policy_name == 'audit_logs':
                    async with self.manager.get_connection('catechese') as conn:
                        query = "SELECT COUNT(*) as count FROM action_logs WHERE timestamp < ?"
                        cursor = await conn.execute(query, (warning_date.isoformat(),))
                        count = (await cursor.fetchone())['count']
                        status['policies'][policy_name] = {
                            'retention_days': retention_days,
                            'records_near_limit': count,
                            'status': 'warning' if count > 0 else 'ok'
                        }
                        status['total_records_at_risk'] += count

                elif policy_name == 'temp_pages':
                    async with self.manager.get_connection('temp_pages') as conn:
                        query = "SELECT COUNT(*) as count FROM pages_temporaires WHERE expires_at < datetime('now')"
                        cursor = await conn.execute(query)
                        count = cursor.fetchone()[0] if cursor else 0
                        status['policies'][policy_name] = {
                            'retention_days': retention_days,
                            'records_expired': count,
                            'status': 'action_required' if count > 0 else 'ok'
                        }

            return status

        except Exception as e:
            logger.error(f"Failed to get retention status: {e}")
            status['error'] = str(e)
            return status


# Global retention service instance
_retention_service_instance: Optional[RetentionService] = None


def get_retention_service() -> RetentionService:
    """Get global retention service instance."""
    global _retention_service_instance
    if _retention_service_instance is None:
        _retention_service_instance = RetentionService()
    return _retention_service_instance


# Scheduled task for daily retention enforcement
async def scheduled_retention_enforcement():
    """
    Daily task to enforce retention policies.

    Should be called by scheduler (e.g., cron job, Celery task)
    """
    logger.info("Starting scheduled retention enforcement")
    retention_service = get_retention_service()
    results = await retention_service.enforce_all_retention_policies()
    logger.info(f"Scheduled retention enforcement completed: {results}")
    return results