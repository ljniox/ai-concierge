"""
Parent Database Lookup Service

This service handles lookups to the external catechism database
to find parent information based on phone numbers.
Enhanced for Phase 3 with comprehensive parent data management.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from src.services.database_service import get_database_service
from src.utils.logging import get_logger
from src.utils.exceptions import (
    DatabaseConnectionError,
    ParentNotFoundError,
    ValidationError
)


class ParentLookupService:
    """
    Service for looking up parents in the catechism database.

    This service provides methods to find and retrieve parent information
    from the external catechism database based on various search criteria.
    """

    def __init__(self, database_service=None):
        """
        Initialize parent lookup service.

        Args:
            database_service: Database service instance
        """
        self.database_service = database_service or get_database_service()
        self.logger = get_logger(__name__)

    async def find_parent_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Find parent in catechese database by phone number.

        Args:
            phone_number: Normalized phone number in E.164 format

        Returns:
            Parent data if found, None otherwise
        """
        try:
            # Clean phone number for matching (remove country code and special characters)
            clean_number = phone_number.replace('+221', '').replace('00221', '')
            clean_number = clean_number.replace(' ', '').replace('-', '').replace('.', '')

            query = """
            SELECT id, code_parent, nom, prenoms, telephone, email, adresse,
                   quartier, commune, profession, date_naissance, lieu_naissance
            FROM parents
            WHERE REPLACE(REPLACE(REPLACE(telephone, ' ', ''), '-', ''), '+221', '') = ?
               OR REPLACE(REPLACE(REPLACE(telephone, ' ', ''), '-', ''), '00221', '') = ?
            LIMIT 1
            """

            # Use the new database service
            result = await self.database_service.fetch_one(
                query,
                (clean_number, clean_number),
                database_name='catechese'
            )

            if result:
                parent_data = dict(result)

                # Get additional information like children count
                children_count = await self._get_children_count(parent_data['id'])

                # Convert to expected format
                formatted_data = {
                    "parent_id": str(parent_data["id"]),
                    "parent_code": parent_data["code_parent"],
                    "first_name": parent_data.get("prenoms", "").split()[0] if parent_data.get("prenoms") else "",
                    "last_name": parent_data.get("nom", ""),
                    "full_name": f"{parent_data.get('prenoms', '')} {parent_data.get('nom', '')}".strip(),
                    "phone_number": parent_data.get("telephone", ""),
                    "email": parent_data.get("email", ""),
                    "address": parent_data.get("adresse", ""),
                    "neighborhood": parent_data.get("quartier", ""),
                    "commune": parent_data.get("commune", ""),
                    "profession": parent_data.get("profession", ""),
                    "birth_date": parent_data.get("date_naissance"),
                    "birth_place": parent_data.get("lieu_naissance", ""),
                    "children_count": children_count,
                    "parish": "Unknown",  # Would need to be queried separately
                    "lookup_timestamp": datetime.now(timezone.utc).isoformat()
                }

                self.logger.info(f"Parent found for phone {phone_number[:10]}***: {parent_data['id']}")

                return formatted_data
            else:
                self.logger.warning(f"No parent found for phone {phone_number[:10]}***")
                return None

        except Exception as e:
            self.logger.error(f"Error finding parent by phone: {str(e)}")
            return None

    async def find_parent_by_code(self, parent_code: str) -> Optional[Dict[str, Any]]:
        """
        Find parent in catechese database by parent code.

        Args:
            parent_code: Unique parent code

        Returns:
            Parent data if found, None otherwise
        """
        try:
            query = """
            SELECT id, code_parent, nom, prenoms, telephone, email, adresse,
                   quartier, commune, profession, date_naissance, lieu_naissance
            FROM parents
            WHERE code_parent = ?
            LIMIT 1
            """

            result = await self.database_service.fetch_one(
                query,
                (parent_code,),
                database_name='catechese'
            )

            if result:
                parent_data = dict(result)

                # Get additional information like children count
                children_count = await self._get_children_count(parent_data['id'])

                formatted_data = {
                    "parent_id": str(parent_data["id"]),
                    "parent_code": parent_data["code_parent"],
                    "first_name": parent_data.get("prenoms", "").split()[0] if parent_data.get("prenoms") else "",
                    "last_name": parent_data.get("nom", ""),
                    "full_name": f"{parent_data.get('prenoms', '')} {parent_data.get('nom', '')}".strip(),
                    "phone_number": parent_data.get("telephone", ""),
                    "email": parent_data.get("email", ""),
                    "address": parent_data.get("adresse", ""),
                    "neighborhood": parent_data.get("quartier", ""),
                    "commune": parent_data.get("commune", ""),
                    "profession": parent_data.get("profession", ""),
                    "birth_date": parent_data.get("date_naissance"),
                    "birth_place": parent_data.get("lieu_naissance", ""),
                    "children_count": children_count,
                    "parish": "Unknown",
                    "lookup_timestamp": datetime.now(timezone.utc).isoformat()
                }

                self.logger.info(f"Parent found for code {parent_code}: {parent_data['id']}")
                return formatted_data
            else:
                self.logger.warning(f"No parent found for code {parent_code}")
                return None

        except Exception as e:
            self.logger.error(f"Error finding parent by code: {str(e)}")
            return None

    async def search_parents_by_name(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search parents by name (first or last name).

        Args:
            name: Name to search for
            limit: Maximum number of results

        Returns:
            List of parent data
        """
        try:
            query = """
            SELECT id, code_parent, nom, prenoms, telephone, email, adresse,
                   quartier, commune, profession, date_naissance, lieu_naissance
            FROM parents
            WHERE LOWER(nom) LIKE LOWER(?)
               OR LOWER(prenoms) LIKE LOWER(?)
            ORDER BY nom, prenoms
            LIMIT ?
            """

            search_pattern = f"%{name}%"

            results = await self.database_service.fetch_all(
                query,
                (search_pattern, search_pattern, limit),
                database_name='catechese'
            )

            parents = []
            for result in results:
                parent_data = dict(result)

                # Get children count for each parent
                children_count = await self._get_children_count(parent_data['id'])

                formatted_data = {
                    "parent_id": str(parent_data["id"]),
                    "parent_code": parent_data["code_parent"],
                    "first_name": parent_data.get("prenoms", "").split()[0] if parent_data.get("prenoms") else "",
                    "last_name": parent_data.get("nom", ""),
                    "full_name": f"{parent_data.get('prenoms', '')} {parent_data.get('nom', '')}".strip(),
                    "phone_number": parent_data.get("telephone", ""),
                    "email": parent_data.get("email", ""),
                    "address": parent_data.get("adresse", ""),
                    "children_count": children_count,
                    "lookup_timestamp": datetime.now(timezone.utc).isoformat()
                }
                parents.append(formatted_data)

            self.logger.info(f"Found {len(parents)} parents matching name '{name}'")
            return parents

        except Exception as e:
            self.logger.error(f"Error searching parents by name: {str(e)}")
            return []

    async def get_parent_children(self, parent_id: str) -> List[Dict[str, Any]]:
        """
        Get all children associated with a parent.

        Args:
            parent_id: Parent ID

        Returns:
            List of children data
        """
        try:
            query = """
            SELECT id, nom, prenoms, date_naissance, lieu_naissance, classe_id,
                   annee_scolaire, statut, date_inscription
            FROM catechumenes
            WHERE parent_id = ?
            ORDER BY date_naissance
            """

            results = await self.database_service.fetch_all(
                query,
                (parent_id,),
                database_name='catechese'
            )

            children = []
            for result in results:
                child_data = dict(result)

                formatted_child = {
                    "child_id": str(child_data["id"]),
                    "first_name": child_data.get("prenoms", "").split()[0] if child_data.get("prenoms") else "",
                    "last_name": child_data.get("nom", ""),
                    "full_name": f"{child_data.get('prenoms', '')} {child_data.get('nom', '')}".strip(),
                    "birth_date": child_data.get("date_naissance"),
                    "birth_place": child_data.get("lieu_naissance", ""),
                    "class_id": child_data.get("classe_id"),
                    "school_year": child_data.get("annee_scolaire", ""),
                    "status": child_data.get("statut", ""),
                    "enrollment_date": child_data.get("date_inscription"),
                    "lookup_timestamp": datetime.now(timezone.utc).isoformat()
                }
                children.append(formatted_child)

            self.logger.info(f"Found {len(children)} children for parent {parent_id}")
            return children

        except Exception as e:
            self.logger.error(f"Error getting parent children: {str(e)}")
            return []

    async def validate_parent_access(self, phone_number: str, parent_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate parent access and return comprehensive parent data.

        Args:
            phone_number: Parent's phone number
            parent_code: Optional parent code for additional verification

        Returns:
            Validation result with parent data
        """
        try:
            # First lookup by phone number
            parent_data = await self.find_parent_by_phone(phone_number)

            if not parent_data:
                return {
                    "valid": False,
                    "error_code": "PARENT_NOT_FOUND",
                    "error_message": "Parent not found for this phone number",
                    "phone_number": phone_number
                }

            # If parent code is provided, verify it matches
            if parent_code and parent_data.get("parent_code") != parent_code:
                return {
                    "valid": False,
                    "error_code": "PARENT_CODE_MISMATCH",
                    "error_message": "Parent code does not match",
                    "phone_number": phone_number
                }

            # Get children information
            children = await self.get_parent_children(parent_data["parent_id"])

            # Return comprehensive validation result
            return {
                "valid": True,
                "parent_data": parent_data,
                "children": children,
                "access_level": "full",  # Could be enhanced with role-based access
                "validated_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error validating parent access: {str(e)}")
            return {
                "valid": False,
                "error_code": "VALIDATION_ERROR",
                "error_message": f"Validation error: {str(e)}",
                "phone_number": phone_number
            }

    async def _get_children_count(self, parent_id: str) -> int:
        """
        Get the number of children for a parent.

        Args:
            parent_id: Parent ID

        Returns:
            Number of children
        """
        try:
            query = "SELECT COUNT(*) as count FROM catechumenes WHERE parent_id = ?"
            result = await self.database_service.fetch_one(
                query,
                (parent_id,),
                database_name='catechese'
            )
            return result['count'] if result else 0

        except Exception as e:
            self.logger.error(f"Error getting children count: {str(e)}")
            return 0

    async def batch_lookup_parents(self, phone_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch lookup parents by phone numbers.

        Args:
            phone_numbers: List of phone numbers

        Returns:
            Dictionary mapping phone numbers to parent data
        """
        try:
            results = {}

            for phone_number in phone_numbers:
                parent_data = await self.find_parent_by_phone(phone_number)
                results[phone_number] = parent_data

            self.logger.info(f"Batch lookup completed for {len(phone_numbers)} phone numbers")
            return results

        except Exception as e:
            self.logger.error(f"Error in batch parent lookup: {str(e)}")
            return {}

    def _normalize_phone_number(self, phone_number: str) -> str:
        """
        Normalize phone number to E.164 format.

        Args:
            phone_number: Phone number to normalize

        Returns:
            Normalized phone number
        """
        # Remove all non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))

        # Add Senegal country code if missing
        if not clean_number.startswith('221'):
            if len(clean_number) == 9:  # Senegalese number without country code
                clean_number = '221' + clean_number

        return '+' + clean_number


# Factory function for getting parent lookup service
def get_parent_lookup_service() -> ParentLookupService:
    """Get parent lookup service instance."""
    return ParentLookupService()