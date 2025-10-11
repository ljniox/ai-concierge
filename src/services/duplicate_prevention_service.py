"""
Duplicate Account Prevention Service

This service handles detection and prevention of duplicate account creation
through various validation methods and cross-platform deduplication.
Enhanced for Phase 3 with comprehensive duplicate detection strategies.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple, Set
from uuid import UUID
from enum import Enum
import hashlib

from src.services.database_service import get_database_service
from src.services.phone_validation_service import get_phone_validation_service
from src.utils.logging import get_logger
from src.utils.exceptions import (
    DatabaseConnectionError,
    DuplicateAccountError,
    ValidationError
)


class DuplicateDetectionMethod(Enum):
    """Methods for detecting duplicate accounts."""
    PHONE_NUMBER = "phone_number"
    PLATFORM_USER_ID = "platform_user_id"
    PARENT_ID = "parent_id"
    EMAIL_ADDRESS = "email_address"
    NAME_AND_PHONE = "name_and_phone"
    FUZZY_MATCHING = "fuzzy_matching"


class DuplicateCheckResult:
    """Result of duplicate account check."""

    def __init__(
        self,
        is_duplicate: bool = False,
        existing_account_id: Optional[UUID] = None,
        detection_method: Optional[DuplicateDetectionMethod] = None,
        confidence_score: float = 0.0,
        platform_links: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.is_duplicate = is_duplicate
        self.existing_account_id = existing_account_id
        self.detection_method = detection_method
        self.confidence_score = confidence_score
        self.platform_links = platform_links or []
        self.metadata = metadata or {}
        self.checked_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_duplicate': self.is_duplicate,
            'existing_account_id': str(self.existing_account_id) if self.existing_account_id else None,
            'detection_method': self.detection_method.value if self.detection_method else None,
            'confidence_score': self.confidence_score,
            'platform_links': self.platform_links,
            'metadata': self.metadata,
            'checked_at': self.checked_at.isoformat()
        }


class AccountMergeResult:
    """Result of account merge operation."""

    def __init__(
        self,
        success: bool = False,
        primary_account_id: Optional[UUID] = None,
        merged_account_ids: Optional[List[UUID]] = None,
        merged_platform_links: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.success = success
        self.primary_account_id = primary_account_id
        self.merged_account_ids = merged_account_ids or []
        self.merged_platform_links = merged_platform_links or {}
        self.error_code = error_code
        self.error_message = error_message
        self.merged_at = datetime.now(timezone.utc)


class DuplicatePreventionService:
    """
    Service for preventing duplicate account creation.

    This service provides multiple methods to detect and prevent duplicate
    accounts across different platforms and contact methods.
    """

    def __init__(
        self,
        database_service=None,
        phone_validation_service=None
    ):
        """
        Initialize duplicate prevention service.

        Args:
            database_service: Database service instance
            phone_validation_service: Phone validation service instance
        """
        self.database_service = database_service or get_database_service()
        self.phone_validation_service = phone_validation_service or get_phone_validation_service()
        self.logger = get_logger(__name__)

    async def check_for_duplicates(
        self,
        phone_number: str,
        platform: str = None,
        platform_user_id: str = None,
        email: str = None,
        first_name: str = None,
        last_name: str = None,
        parent_id: str = None
    ) -> List[DuplicateCheckResult]:
        """
        Check for duplicate accounts using multiple detection methods.

        Args:
            phone_number: Phone number to check
            platform: Platform name
            platform_user_id: Platform-specific user ID
            email: Email address
            first_name: First name
            last_name: Last name
            parent_id: Parent ID from catechism database

        Returns:
            List of duplicate check results
        """
        try:
            results = []

            # Check by phone number (primary method)
            phone_result = await self._check_by_phone_number(phone_number)
            if phone_result.is_duplicate:
                results.append(phone_result)

            # Check by platform user ID
            if platform and platform_user_id:
                platform_result = await self._check_by_platform_user_id(platform, platform_user_id)
                if platform_result.is_duplicate:
                    results.append(platform_result)

            # Check by parent ID
            if parent_id:
                parent_result = await self._check_by_parent_id(parent_id)
                if parent_result.is_duplicate:
                    results.append(parent_id)

            # Check by email address
            if email:
                email_result = await self._check_by_email(email)
                if email_result.is_duplicate:
                    results.append(email_result)

            # Check by name and phone combination
            if first_name and last_name:
                name_result = await self._check_by_name_and_phone(first_name, last_name, phone_number)
                if name_result.is_duplicate:
                    results.append(name_result)

            # Check for fuzzy matches (more expensive, run last)
            if phone_number and (first_name or last_name):
                fuzzy_result = await self._check_fuzzy_matching(phone_number, first_name, last_name)
                if fuzzy_result.is_duplicate and fuzzy_result.confidence_score > 0.7:
                    results.append(fuzzy_result)

            # Log duplicate check
            await self._log_duplicate_check(
                phone_number, platform, platform_user_id, results
            )

            return results

        except Exception as e:
            self.logger.error(f"Error checking for duplicates: {str(e)}")
            return []

    async def prevent_duplicate_creation(
        self,
        account_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[UUID], Optional[DuplicateCheckResult]]:
        """
        Prevent duplicate account creation.

        Args:
            account_data: Account creation data

        Returns:
            Tuple of (can_create, existing_account_id, duplicate_result)
        """
        try:
            # Extract relevant data
            phone_number = account_data.get('phone_number')
            platform = account_data.get('platform')
            platform_user_id = account_data.get('platform_user_id')
            email = account_data.get('email')
            first_name = account_data.get('first_name')
            last_name = account_data.get('last_name')
            parent_id = account_data.get('parent_id')

            # Check for duplicates
            duplicates = await self.check_for_duplicates(
                phone_number=phone_number,
                platform=platform,
                platform_user_id=platform_user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                parent_id=parent_id
            )

            if duplicates:
                # Get the highest confidence duplicate
                best_duplicate = max(duplicates, key=lambda x: x.confidence_score)

                # Log prevention
                await self._log_duplicate_prevention(
                    phone_number, platform, platform_user_id, best_duplicate
                )

                return False, best_duplicate.existing_account_id, best_duplicate

            # No duplicates found, can create account
            return True, None, None

        except Exception as e:
            self.logger.error(f"Error in duplicate prevention: {str(e)}")
            return True, None, None  # Fail-safe: allow creation if check fails

    async def link_platform_to_existing_account(
        self,
        platform: str,
        platform_user_id: str,
        existing_account_id: UUID
    ) -> AccountMergeResult:
        """
        Link platform account to existing account instead of creating duplicate.

        Args:
            platform: Platform name
            platform_user_id: Platform-specific user ID
            existing_account_id: ID of existing account

        Returns:
            Account merge result
        """
        try:
            # Update existing account with platform link
            update_data = {
                f"{platform}_user_id": platform_user_id,
                "updated_at": datetime.now(timezone.utc),
                f"{platform}_linked_at": datetime.now(timezone.utc)
            }

            await self.database_service.update(
                "user_accounts",
                update_data,
                {"id": str(existing_account_id)},
                database_name="supabase"
            )

            # Get current platform links
            account = await self._get_account_by_id(existing_account_id)
            platform_links = {}
            if account:
                for platform_name in ['whatsapp', 'telegram']:
                    user_id_field = f"{platform_name}_user_id"
                    if account.get(user_id_field):
                        platform_links[platform_name] = account[user_id_field]

            self.logger.info(
                f"Linked {platform} account {platform_user_id[:10]}*** to existing account {existing_account_id}"
            )

            # Log successful merge
            await self._log_account_merge(
                platform, platform_user_id, existing_account_id, "platform_link"
            )

            return AccountMergeResult(
                success=True,
                primary_account_id=existing_account_id,
                merged_platform_links=platform_links
            )

        except Exception as e:
            self.logger.error(f"Failed to link platform account: {str(e)}")
            return AccountMergeResult(
                success=False,
                error_code="PLATFORM_LINK_FAILED",
                error_message=str(e)
            )

    async def merge_duplicate_accounts(
        self,
        primary_account_id: UUID,
        duplicate_account_ids: List[UUID]
    ) -> AccountMergeResult:
        """
        Merge duplicate accounts into a single primary account.

        Args:
            primary_account_id: ID of account to keep
            duplicate_account_ids: IDs of accounts to merge

        Returns:
            Account merge result
        """
        try:
            merged_links = {}
            merged_sessions = []

            for duplicate_id in duplicate_account_ids:
                # Get duplicate account data
                duplicate_account = await self._get_account_by_id(duplicate_id)
                if not duplicate_account:
                    continue

                # Transfer platform links
                for platform in ['whatsapp', 'telegram']:
                    platform_field = f"{platform}_user_id"
                    duplicate_platform_id = duplicate_account.get(platform_field)
                    if duplicate_platform_id:
                        merged_links[platform] = duplicate_platform_id

                # Mark duplicate account as merged
                await self.database_service.update(
                    "user_accounts",
                    {
                        "status": "MERGED",
                        "merged_into": str(primary_account_id),
                        "merged_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    },
                    {"id": str(duplicate_id)},
                    database_name="supabase"
                )

                # Transfer sessions to primary account
                await self._transfer_sessions(duplicate_id, primary_account_id)
                merged_sessions.append(str(duplicate_id))

            # Update primary account with merged platform links
            if merged_links:
                update_data = {
                    "updated_at": datetime.now(timezone.utc),
                    **{f"{platform}_user_id": user_id for platform, user_id in merged_links.items()}
                }

                await self.database_service.update(
                    "user_accounts",
                    update_data,
                    {"id": str(primary_account_id)},
                    database_name="supabase"
                )

            self.logger.info(f"Merged {len(duplicate_account_ids)} accounts into {primary_account_id}")

            # Log successful merge
            await self._log_account_merge(
                "system", str(primary_account_id), primary_account_id, "account_merge",
                {"merged_accounts": duplicate_account_ids, "merged_links": merged_links}
            )

            return AccountMergeResult(
                success=True,
                primary_account_id=primary_account_id,
                merged_account_ids=duplicate_account_ids,
                merged_platform_links=merged_links
            )

        except Exception as e:
            self.logger.error(f"Failed to merge duplicate accounts: {str(e)}")
            return AccountMergeResult(
                success=False,
                error_code="ACCOUNT_MERGE_FAILED",
                error_message=str(e)
            )

    async def cleanup_potential_duplicates(self, days_threshold: int = 7) -> Dict[str, Any]:
        """
        Clean up potential duplicates created recently.

        Args:
            days_threshold: Number of days to look back

        Returns:
            Cleanup summary
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)

            # Find recently created accounts that might be duplicates
            query = """
            SELECT ua1.id as account1_id, ua1.phone_number as phone1,
                   ua1.platform as platform1, ua1.platform_user_id as user_id1,
                   ua2.id as account2_id, ua2.platform as platform2, ua2.platform_user_id as user_id2
            FROM user_accounts ua1
            INNER JOIN user_accounts ua2 ON ua1.phone_number = ua2.phone_number
            WHERE ua1.id != ua2.id
              AND ua1.created_at >= ? AND ua2.created_at >= ?
              AND ua1.status = 'ACTIVE' AND ua2.status = 'ACTIVE'
            """

            potential_duplicates = await self.database_service.fetch_all(
                query,
                (cutoff_date, cutoff_date),
                database_name="supabase"
            )

            duplicates_found = len(potential_duplicates)
            duplicates_merged = 0

            processed_pairs = set()
            for duplicate in potential_duplicates:
                # Create a unique pair identifier to avoid processing the same pair twice
                pair_id = tuple(sorted([duplicate['account1_id'], duplicate['account2_id']]))
                if pair_id in processed_pairs:
                    continue
                processed_pairs.add(pair_id)

                try:
                    # Merge accounts (keep the older one as primary)
                    account1_id = UUID(duplicate['account1_id'])
                    account2_id = UUID(duplicate['account2_id'])

                    # Get account creation times to determine primary
                    account1 = await self._get_account_by_id(account1_id)
                    account2 = await self._get_account_by_id(account2_id)

                    if account1 and account2:
                        if account1['created_at'] <= account2['created_at']:
                            primary_id, duplicate_id = account1_id, account2_id
                        else:
                            primary_id, duplicate_id = account2_id, account1_id

                        result = await self.merge_duplicate_accounts(primary_id, [duplicate_id])
                        if result.success:
                            duplicates_merged += 1

                except Exception as e:
                    self.logger.error(f"Failed to merge duplicate pair {pair_id}: {str(e)}")

            summary = {
                'potential_duplicates_found': duplicates_found,
                'duplicates_merged': duplicates_merged,
                'period_days': days_threshold
            }

            self.logger.info(f"Duplicate cleanup completed: {duplicates_merged}/{duplicates_found} merged")
            return summary

        except Exception as e:
            self.logger.error(f"Failed to cleanup duplicates: {str(e)}")
            return {
                'error': str(e),
                'potential_duplicates_found': 0,
                'duplicates_merged': 0
            }

    # Private methods for specific duplicate checks

    async def _check_by_phone_number(self, phone_number: str) -> DuplicateCheckResult:
        """Check for duplicates by phone number."""
        try:
            # Normalize phone number
            validation = await self.phone_validation_service.validate_phone_number(phone_number)
            if not validation.is_valid:
                return DuplicateCheckResult(is_duplicate=False)

            normalized_phone = validation.normalized_number

            query = "SELECT id, platform, platform_user_id FROM user_accounts WHERE phone_number = ? AND is_deleted = FALSE"
            result = await self.database_service.fetch_one(
                query,
                (normalized_phone,),
                database_name="supabase"
            )

            if result:
                platform_links = []
                for platform in ['whatsapp', 'telegram']:
                    user_id = result.get(f"{platform}_user_id")
                    if user_id:
                        platform_links.append(f"{platform}:{user_id}")

                return DuplicateCheckResult(
                    is_duplicate=True,
                    existing_account_id=UUID(result['id']),
                    detection_method=DuplicateDetectionMethod.PHONE_NUMBER,
                    confidence_score=1.0,
                    platform_links=platform_links,
                    metadata={'normalized_phone': normalized_phone}
                )

            return DuplicateCheckResult(is_duplicate=False)

        except Exception as e:
            self.logger.error(f"Error checking by phone number: {str(e)}")
            return DuplicateCheckResult(is_duplicate=False)

    async def _check_by_platform_user_id(self, platform: str, platform_user_id: str) -> DuplicateCheckResult:
        """Check for duplicates by platform user ID."""
        try:
            query = f"SELECT id, phone_number FROM user_accounts WHERE {platform}_user_id = ? AND is_deleted = FALSE"
            result = await self.database_service.fetch_one(
                query,
                (platform_user_id,),
                database_name="supabase"
            )

            if result:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    existing_account_id=UUID(result['id']),
                    detection_method=DuplicateDetectionMethod.PLATFORM_USER_ID,
                    confidence_score=1.0,
                    metadata={'platform': platform, 'platform_user_id': platform_user_id}
                )

            return DuplicateCheckResult(is_duplicate=False)

        except Exception as e:
            self.logger.error(f"Error checking by platform user ID: {str(e)}")
            return DuplicateCheckResult(is_duplicate=False)

    async def _check_by_parent_id(self, parent_id: str) -> DuplicateCheckResult:
        """Check for duplicates by parent ID."""
        try:
            query = "SELECT id, phone_number FROM user_accounts WHERE parent_id = ? AND is_deleted = FALSE"
            result = await self.database_service.fetch_one(
                query,
                (parent_id,),
                database_name="supabase"
            )

            if result:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    existing_account_id=UUID(result['id']),
                    detection_method=DuplicateDetectionMethod.PARENT_ID,
                    confidence_score=0.9,
                    metadata={'parent_id': parent_id}
                )

            return DuplicateCheckResult(is_duplicate=False)

        except Exception as e:
            self.logger.error(f"Error checking by parent ID: {str(e)}")
            return DuplicateCheckResult(is_duplicate=False)

    async def _check_by_email(self, email: str) -> DuplicateCheckResult:
        """Check for duplicates by email address."""
        try:
            if not email or '@' not in email:
                return DuplicateCheckResult(is_duplicate=False)

            query = "SELECT id, phone_number FROM user_accounts WHERE email = ? AND is_deleted = FALSE"
            result = await self.database_service.fetch_one(
                query,
                (email.lower().strip(),),
                database_name="supabase"
            )

            if result:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    existing_account_id=UUID(result['id']),
                    detection_method=DuplicateDetectionMethod.EMAIL_ADDRESS,
                    confidence_score=0.8,
                    metadata={'email': email}
                )

            return DuplicateCheckResult(is_duplicate=False)

        except Exception as e:
            self.logger.error(f"Error checking by email: {str(e)}")
            return DuplicateCheckResult(is_duplicate=False)

    async def _check_by_name_and_phone(self, first_name: str, last_name: str, phone_number: str) -> DuplicateCheckResult:
        """Check for duplicates by name and phone combination."""
        try:
            # Normalize names
            first_norm = first_name.lower().strip()
            last_norm = last_name.lower().strip()

            query = """
            SELECT id, phone_number, first_name, last_name
            FROM user_accounts
            WHERE LOWER(first_name) = ? AND LOWER(last_name) = ? AND is_deleted = FALSE
            """

            results = await self.database_service.fetch_all(
                query,
                (first_norm, last_norm),
                database_name="supabase"
            )

            for result in results:
                # Check if phone numbers are similar (might have different formatting)
                if self._phones_similar(phone_number, result['phone_number']):
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        existing_account_id=UUID(result['id']),
                        detection_method=DuplicateDetectionMethod.NAME_AND_PHONE,
                        confidence_score=0.7,
                        metadata={
                            'first_name': first_name,
                            'last_name': last_name,
                            'existing_phone': result['phone_number']
                        }
                    )

            return DuplicateCheckResult(is_duplicate=False)

        except Exception as e:
            self.logger.error(f"Error checking by name and phone: {str(e)}")
            return DuplicateCheckResult(is_duplicate=False)

    async def _check_fuzzy_matching(self, phone_number: str, first_name: str, last_name: str) -> DuplicateCheckResult:
        """Check for duplicates using fuzzy matching."""
        try:
            # This is a simplified implementation
            # In production, you might use more sophisticated fuzzy matching

            # Clean phone number to digits only
            clean_phone = ''.join(filter(str.isdigit, phone_number))

            # Look for accounts with similar phone numbers (last 7 digits)
            if len(clean_phone) >= 7:
                phone_suffix = clean_phone[-7:]

                query = """
                SELECT id, phone_number, first_name, last_name
                FROM user_accounts
                WHERE REPLACE(REPLACE(REPLACE(phone_number, '+', ''), '-', ''), ' ', '') LIKE ?
                  AND is_deleted = FALSE
                """

                results = await self.database_service.fetch_all(
                    query,
                    (f"%{phone_suffix}%",),
                    database_name="supabase"
                )

                for result in results:
                    # Calculate similarity score
                    name_similarity = self._calculate_name_similarity(
                        first_name, last_name,
                        result.get('first_name', ''), result.get('last_name', '')
                    )

                    if name_similarity > 0.6:
                        confidence_score = min(0.8, name_similarity + 0.2)
                        return DuplicateCheckResult(
                            is_duplicate=True,
                            existing_account_id=UUID(result['id']),
                            detection_method=DuplicateDetectionMethod.FUZZY_MATCHING,
                            confidence_score=confidence_score,
                            metadata={
                                'similarity_score': name_similarity,
                                'matched_phone': result['phone_number']
                            }
                        )

            return DuplicateCheckResult(is_duplicate=False)

        except Exception as e:
            self.logger.error(f"Error in fuzzy matching: {str(e)}")
            return DuplicateCheckResult(is_duplicate=False)

    # Helper methods

    def _phones_similar(self, phone1: str, phone2: str) -> bool:
        """Check if two phone numbers are similar."""
        # Extract digits only
        digits1 = ''.join(filter(str.isdigit, phone1))
        digits2 = ''.join(filter(str.isdigit, phone2))

        # If both have at least 7 digits, compare last 7
        if len(digits1) >= 7 and len(digits2) >= 7:
            return digits1[-7:] == digits2[-7:]

        # Otherwise, compare all digits
        return digits1 == digits2

    def _calculate_name_similarity(self, first1: str, last1: str, first2: str, last2: str) -> float:
        """Calculate similarity score between two names."""
        # Simple implementation - in production, use more sophisticated algorithms
        first1_norm = first1.lower().strip()
        last1_norm = last1.lower().strip()
        first2_norm = first2.lower().strip()
        last2_norm = last2.lower().strip()

        # Exact match
        if first1_norm == first2_norm and last1_norm == last2_norm:
            return 1.0

        # Partial match
        score = 0.0
        if first1_norm == first2_norm:
            score += 0.5
        elif first1_norm in first2_norm or first2_norm in first1_norm:
            score += 0.3

        if last1_norm == last2_norm:
            score += 0.5
        elif last1_norm in last2_norm or last2_norm in last1_norm:
            score += 0.2

        return score

    async def _get_account_by_id(self, account_id: UUID) -> Optional[Dict[str, Any]]:
        """Get account by ID."""
        try:
            query = "SELECT * FROM user_accounts WHERE id = ? AND is_deleted = FALSE"
            result = await self.database_service.fetch_one(
                query,
                (str(account_id),),
                database_name="supabase"
            )
            return dict(result) if result else None

        except Exception as e:
            self.logger.error(f"Error getting account by ID: {str(e)}")
            return None

    async def _transfer_sessions(self, from_account_id: UUID, to_account_id: UUID) -> None:
        """Transfer sessions from one account to another."""
        try:
            update_data = {
                "user_id": str(to_account_id),
                "updated_at": datetime.now(timezone.utc),
                "transferred_from": str(from_account_id)
            }

            await self.database_service.update(
                "user_sessions",
                update_data,
                {"user_id": str(from_account_id)},
                database_name="supabase"
            )

        except Exception as e:
            self.logger.error(f"Error transferring sessions: {str(e)}")

    async def _log_duplicate_check(
        self,
        phone_number: str,
        platform: str,
        platform_user_id: str,
        results: List[DuplicateCheckResult]
    ) -> None:
        """Log duplicate check for audit purposes."""
        try:
            log_data = {
                'phone_number': phone_number,
                'platform': platform,
                'platform_user_id': platform_user_id,
                'duplicates_found': len([r for r in results if r.is_duplicate]),
                'detection_results': [r.to_dict() for r in results],
                'checked_at': datetime.now(timezone.utc)
            }

            await self.database_service.insert(
                'duplicate_check_logs',
                log_data,
                database_name='supabase'
            )

        except Exception as e:
            self.logger.error(f"Failed to log duplicate check: {str(e)}")

    async def _log_duplicate_prevention(
        self,
        phone_number: str,
        platform: str,
        platform_user_id: str,
        duplicate_result: DuplicateCheckResult
    ) -> None:
        """Log duplicate prevention for audit purposes."""
        try:
            log_data = {
                'phone_number': phone_number,
                'platform': platform,
                'platform_user_id': platform_user_id,
                'existing_account_id': str(duplicate_result.existing_account_id),
                'detection_method': duplicate_result.detection_method.value,
                'confidence_score': duplicate_result.confidence_score,
                'prevented_at': datetime.now(timezone.utc)
            }

            await self.database_service.insert(
                'duplicate_prevention_logs',
                log_data,
                database_name='supabase'
            )

        except Exception as e:
            self.logger.error(f"Failed to log duplicate prevention: {str(e)}")

    async def _log_account_merge(
        self,
        platform: str,
        platform_user_id: str,
        primary_account_id: UUID,
        merge_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log account merge for audit purposes."""
        try:
            log_data = {
                'platform': platform,
                'platform_user_id': platform_user_id,
                'primary_account_id': str(primary_account_id),
                'merge_type': merge_type,
                'metadata': metadata or {},
                'merged_at': datetime.now(timezone.utc)
            }

            await self.database_service.insert(
                'account_merge_logs',
                log_data,
                database_name='supabase'
            )

        except Exception as e:
            self.logger.error(f"Failed to log account merge: {str(e)}")


# Factory function for getting duplicate prevention service
def get_duplicate_prevention_service() -> DuplicatePreventionService:
    """Get duplicate prevention service instance."""
    return DuplicatePreventionService()