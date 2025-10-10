"""
Super Admin service for managing renseignements and system operations
"""

import json
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date
from enum import Enum
from src.utils.config import get_settings
from src.utils.database import get_supabase_client
from src.utils.text_normalization import normalize_command, get_normalized_command_mapping, extract_command_and_params
import structlog

logger = structlog.get_logger()

class RenseignementStatus(Enum):
    """Status for renseignements"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SCHEDULED = "scheduled"
    EXPIRED = "expired"

class SuperAdminService:
    """Service for Super Admin operations"""

    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self.super_admin_phones = ["221765005555"]  # List of admin phone numbers

    def is_super_admin(self, phone_number: str) -> bool:
        """Check if phone number belongs to Super Admin"""
        # Remove any formatting and compare
        clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        return clean_phone in self.super_admin_phones

    async def add_admin_phone(self, phone_number: str) -> Dict[str, Any]:
        """Add a new admin phone number"""
        try:
            clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")

            if clean_phone in self.super_admin_phones:
                return {
                    "success": False,
                    "message": f"Le numéro {phone_number} est déjà un administrateur."
                }

            self.super_admin_phones.append(clean_phone)

            logger.info("admin_phone_added", phone_number=clean_phone, total_admins=len(self.super_admin_phones))

            return {
                "success": True,
                "message": f"Le numéro {phone_number} a été ajouté comme administrateur.",
                "total_admins": len(self.super_admin_phones)
            }
        except Exception as e:
            logger.error("admin_phone_add_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

    async def remove_admin_phone(self, phone_number: str) -> Dict[str, Any]:
        """Remove an admin phone number"""
        try:
            clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")

            if clean_phone not in self.super_admin_phones:
                return {
                    "success": False,
                    "message": f"Le numéro {phone_number} n'est pas un administrateur."
                }

            if len(self.super_admin_phones) <= 1:
                return {
                    "success": False,
                    "message": "Impossible de supprimer le dernier administrateur."
                }

            self.super_admin_phones.remove(clean_phone)

            logger.info("admin_phone_removed", phone_number=clean_phone, total_admins=len(self.super_admin_phones))

            return {
                "success": True,
                "message": f"Le numéro {phone_number} a été supprimé comme administrateur.",
                "total_admins": len(self.super_admin_phones)
            }
        except Exception as e:
            logger.error("admin_phone_remove_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

    async def list_admin_phones(self) -> Dict[str, Any]:
        """List all admin phone numbers"""
        try:
            return {
                "success": True,
                "message": f"Administrateurs ({len(self.super_admin_phones)}):",
                "admins": self.super_admin_phones
            }
        except Exception as e:
            logger.error("admin_list_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

    async def add_renseignement(
        self,
        titre: str,
        contenu: str,
        date_debut: Optional[date] = None,
        date_fin: Optional[date] = None,
        categorie: str = "general",
        priorite: int = 1
    ) -> Dict[str, Any]:
        """Add a new renseignement"""
        try:
            # Set default dates if not provided
            if date_debut is None:
                date_debut = date.today()

            # Insert into Supabase
            data = {
                "titre": titre,
                "contenu": contenu,
                "date_debut": date_debut.isoformat(),
                "categorie": categorie,
                "priorite": priorite,
                "status": RenseignementStatus.ACTIVE.value,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            if date_fin:
                data["date_fin"] = date_fin.isoformat()

            result = self.supabase.table("renseignements").insert(data).execute()

            if result.data:
                logger.info("renseignement_added", titre=titre, categorie=categorie)
                return {
                    "success": True,
                    "message": f"Renseignement '{titre}' ajouté avec succès",
                    "data": result.data[0]
                }
            else:
                logger.error("renseignement_add_failed", titre=titre)
                return {
                    "success": False,
                    "message": "Erreur lors de l'ajout du renseignement"
                }

        except Exception as e:
            logger.error("renseignement_add_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

    async def update_renseignement(
        self,
        renseignement_id: int,
        titre: Optional[str] = None,
        contenu: Optional[str] = None,
        date_debut: Optional[date] = None,
        date_fin: Optional[date] = None,
        categorie: Optional[str] = None,
        priorite: Optional[int] = None,
        status: Optional[RenseignementStatus] = None
    ) -> Dict[str, Any]:
        """Update an existing renseignement"""
        try:
            # Build update data
            update_data = {
                "updated_at": datetime.now().isoformat()
            }

            if titre:
                update_data["titre"] = titre
            if contenu:
                update_data["contenu"] = contenu
            if date_debut:
                update_data["date_debut"] = date_debut.isoformat()
            if date_fin is not None:  # Allow setting to None
                update_data["date_fin"] = date_fin.isoformat() if date_fin else None
            if categorie:
                update_data["categorie"] = categorie
            if priorite is not None:
                update_data["priorite"] = priorite
            if status:
                update_data["status"] = status.value

            result = self.supabase.table("renseignements").update(update_data).eq("id", renseignement_id).execute()

            if result.data:
                logger.info("renseignement_updated", id=renseignement_id)
                return {
                    "success": True,
                    "message": f"Renseignement ID {renseignement_id} mis à jour avec succès",
                    "data": result.data[0]
                }
            else:
                logger.error("renseignement_update_failed", id=renseignement_id)
                return {
                    "success": False,
                    "message": f"Renseignement ID {renseignement_id} non trouvé"
                }

        except Exception as e:
            logger.error("renseignement_update_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

    async def deactivate_renseignement(self, renseignement_id: int) -> Dict[str, Any]:
        """Deactivate a renseignement"""
        return await self.update_renseignement(
            renseignement_id=renseignement_id,
            status=RenseignementStatus.INACTIVE
        )

    async def get_categories(self) -> Dict[str, Any]:
        """Get all unique categories from renseignements"""
        try:
            result = self.supabase.table("renseignements").select("categorie").execute()

            if result.data:
                # Extract unique categories
                categories = list(set(item.get("categorie", "général") for item in result.data))
                categories.sort()  # Sort alphabetically

                logger.info("categories_retrieved", count=len(categories))
                return {
                    "success": True,
                    "message": f"Catégories disponibles ({len(categories)}):",
                    "categories": categories
                }
            else:
                return {
                    "success": True,
                    "message": "Aucune catégorie trouvée",
                    "categories": []
                }
        except Exception as e:
            logger.error("categories_retrieval_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

    async def list_renseignements(
        self,
        categorie: Optional[str] = None,
        status: Optional[RenseignementStatus] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """List renseignements with optional filters"""
        try:
            query = self.supabase.table("renseignements").select("*")

            if categorie:
                query = query.eq("categorie", categorie)
            if status:
                query = query.eq("status", status.value)
            elif active_only:
                query = query.eq("status", RenseignementStatus.ACTIVE.value)

            # Order by priority and creation date
            query = query.order("priorite", desc=True).order("created_at", desc=True)

            result = query.execute()

            if result.data:
                # Filter by date validity
                today = date.today()
                valid_renseignements = []

                for renseignement in result.data:
                    date_debut = datetime.strptime(renseignement["date_debut"], "%Y-%m-%d").date()
                    date_fin = datetime.strptime(renseignement["date_fin"], "%Y-%m-%d").date() if renseignement.get("date_fin") else None

                    # Check if renseignement is currently valid
                    is_valid = date_debut <= today
                    if date_fin:
                        is_valid = is_valid and today <= date_fin

                    if not active_only or is_valid:
                        valid_renseignements.append(renseignement)

                logger.info("renseignements_listed", count=len(valid_renseignements))
                return {
                    "success": True,
                    "message": f"{len(valid_renseignements)} renseignements trouvés",
                    "data": valid_renseignements
                }
            else:
                return {
                    "success": True,
                    "message": "Aucun renseignement trouvé",
                    "data": []
                }

        except Exception as e:
            logger.error("renseignements_list_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

    async def get_renseignement(self, renseignement_id: int) -> Dict[str, Any]:
        """Get a specific renseignement by ID"""
        try:
            result = self.supabase.table("renseignements").select("*").eq("id", renseignement_id).execute()

            if result.data:
                return {
                    "success": True,
                    "message": "Renseignement trouvé",
                    "data": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": f"Renseignement ID {renseignement_id} non trouvé"
                }

        except Exception as e:
            logger.error("renseignement_get_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur: {str(e)}"
            }

    async def parse_admin_command(self, message: str) -> Dict[str, Any]:
        """Parse Super Admin command and execute appropriate action"""
        try:
            normalized_message = normalize_command(message)
            command_mapping = get_normalized_command_mapping()

            # Extract command parts
            message_parts = normalized_message.split()
            if not message_parts:
                return {
                    "success": False,
                    "message": "Commande vide. Tapez 'aide' pour voir les commandes disponibles."
                }

            # Get the root command (first word)
            root_command = message_parts[0]
            canonical_command = command_mapping.get(root_command, root_command)

            # Multi-word commands
            if len(message_parts) >= 2:
                second_word = message_parts[1]
                canonical_second = command_mapping.get(second_word, second_word)

                full_command = f"{canonical_command} {canonical_second}"

                # Add renseignement command
                if full_command in ["ajouter renseignement", "add renseignement"]:
                    return await self._parse_add_renseignement(message)

                # Update renseignement command
                elif full_command in ["modifier renseignement", "update renseignement"]:
                    return await self._parse_update_renseignement(message)

                # Deactivate renseignement command
                elif full_command in ["desactiver renseignement", "deactivate renseignement"]:
                    return await self._parse_deactivate_renseignement(message)

                # List renseignements command (both singular and plural)
                elif full_command in ["lister renseignement", "list renseignement", "lister renseignements", "list renseignements"]:
                    return await self._parse_list_renseignements(message)

                # Categories command
                elif canonical_second in ["categories", "categorie", "catégories", "catégorie"]:
                    categories_result = await self.get_categories()
                    if categories_result.get("success"):
                        suggestions = self._generate_suggestions("categories", None)
                        categories_result["suggestions"] = suggestions
                    return categories_result

                # Profile-based commands (admin can also use profile commands)
                elif full_command in ["rechercher catechumene", "chercher catechumene", "trouver catechumene"]:
                    return await self._parse_search_catechumene(message)
                elif full_command in ["voir parent", "parent info"]:
                    return await self._parse_view_parent_info(message)
                elif full_command in ["lister classe", "lister classes"]:
                    return await self._parse_list_classes(message)

                # Admin management commands
                elif full_command in ["ajouter admin", "add admin"]:
                    return await self._parse_add_admin(message)
                elif full_command in ["supprimer admin", "remove admin"]:
                    return await self._parse_remove_admin(message)
                elif full_command in ["lister admin", "list admin", "lister admins", "list admins"]:
                    return await self.list_admin_phones()

            # Single word commands
            # Help command
            if canonical_command in ["aide", "help", "commandes"]:
                return await self._get_admin_help()

            # Categories command (single word)
            elif canonical_command in ["categories", "categorie", "catégories", "catégorie"]:
                categories_result = await self.get_categories()
                if categories_result.get("success"):
                    suggestions = self._generate_suggestions("categories", None)
                    categories_result["suggestions"] = suggestions
                return categories_result

            # Try to match as list renseignements without second word
            elif canonical_command == "lister" and len(message_parts) >= 2:
                # Check if second word could be "renseignement" in any form (singular or plural)
                second_word_norm = command_mapping.get(message_parts[1], message_parts[1])
                if second_word_norm in ["renseignement", "renseignements"]:
                    return await self._parse_list_renseignements(message)

            # Profile-based single word commands
            elif canonical_command == "rechercher" and len(message_parts) >= 2:
                return await self._parse_search_catechumene(message)
            elif canonical_command == "chercher" and len(message_parts) >= 2:
                return await self._parse_search_catechumene(message)
            elif canonical_command == "trouver" and len(message_parts) >= 2:
                return await self._parse_search_catechumene(message)
            elif canonical_command == "voir" and len(message_parts) >= 2:
                second_word = message_parts[1]
                if second_word in ["parent", "parents"]:
                    return await self._parse_view_parent_info(message)

            return {
                "success": False,
                "message": f"Commande '{message}' non reconnue. Tapez 'aide' pour voir les commandes disponibles."
            }

        except Exception as e:
            logger.error("admin_command_parse_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur de traitement: {str(e)}"
            }

    async def _parse_add_renseignement(self, message: str) -> Dict[str, Any]:
        """Parse add renseignement command"""
        try:
            # Simple parsing - in production, use more sophisticated NLP
            parts = message.split("|")

            titre = parts[0].split("renseignement")[1].strip() if len(parts) > 0 else ""
            contenu = parts[1].strip() if len(parts) > 1 else ""
            categorie = parts[2].strip() if len(parts) > 2 else "general"

            if not titre or not contenu:
                return {
                    "success": False,
                    "message": "Format: ajouter renseignement | titre | contenu | [categorie]"
                }

            return await self.add_renseignement(
                titre=titre,
                contenu=contenu,
                categorie=categorie
            )

        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur d'analyse: {str(e)}"
            }

    async def _parse_update_renseignement(self, message: str) -> Dict[str, Any]:
        """Parse update renseignement command"""
        try:
            # Simple parsing - extract ID and new content
            parts = message.split("|")

            if len(parts) < 3:
                return {
                    "success": False,
                    "message": "Format: modifier renseignement | ID | [nouveau_titre |] [nouveau_contenu |] [nouvelle_categorie]"
                }

            try:
                renseignement_id = int(parts[1].strip())
            except ValueError:
                return {
                    "success": False,
                    "message": "ID invalide. Utilisez un nombre entier."
                }

            # Parse optional fields
            titre = None
            contenu = None
            categorie = None

            for i, part in enumerate(parts[2:], 2):
                part = part.strip().lower()
                if part.startswith("titre:"):
                    titre = part[6:].strip()
                elif part.startswith("contenu:"):
                    contenu = part[8:].strip()
                elif part.startswith("categorie:"):
                    categorie = part[10:].strip()

            return await self.update_renseignement(
                renseignement_id=renseignement_id,
                titre=titre,
                contenu=contenu,
                categorie=categorie
            )

        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur d'analyse: {str(e)}"
            }

    async def _parse_deactivate_renseignement(self, message: str) -> Dict[str, Any]:
        """Parse deactivate renseignement command"""
        try:
            # Extract ID from message
            parts = message.split()
            if len(parts) < 3:
                return {
                    "success": False,
                    "message": "Format: desactiver renseignement [ID]"
                }

            try:
                renseignement_id = int(parts[2])
                return await self.deactivate_renseignement(renseignement_id)
            except ValueError:
                return {
                    "success": False,
                    "message": "ID invalide. Utilisez un nombre entier."
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur d'analyse: {str(e)}"
            }

    async def _parse_list_renseignements(self, message: str) -> Dict[str, Any]:
        """Parse list renseignements command"""
        try:
            parts = message.split()

            # Check if specific category requested
            if len(parts) > 2:
                categorie = parts[2]
                result = await self.list_renseignements(categorie=categorie)

                # Add suggestions to the result
                if result.get("success"):
                    suggestions = self._generate_suggestions("list_with_category", categorie)
                    result["suggestions"] = suggestions

                return result
            else:
                # List all renseignements
                result = await self.list_renseignements(categorie=None)

                if result.get("success"):
                    # Get categories for suggestions
                    categories_result = await self.get_categories()

                    suggestions = self._generate_suggestions("list_all", None)
                    if categories_result.get("success"):
                        categories = categories_result.get("categories", [])
                        if categories:
                            suggestions.append(f"\n📂 **Catégories disponibles:** {', '.join(categories[:5])}")
                            if len(categories) > 5:
                                suggestions.append(f"   ... et {len(categories) - 5} autres catégories")

                    result["suggestions"] = suggestions
                    result["categories"] = categories_result.get("categories", [])

                return result

        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur d'analyse: {str(e)}"
            }

    def _generate_suggestions(self, context: str, param: str = None) -> List[str]:
        """Generate contextual command suggestions"""
        suggestions = []

        if context == "list_all":
            suggestions.extend([
                "\n💡 **Commandes suggérées:**",
                "• `lister renseignements horaire` - voir les horaires",
                "• `categories` - voir toutes les catégories",
                "• `ajouter renseignement | titre | contenu | categorie` - ajouter un nouveau renseignement"
            ])
        elif context == "list_with_category":
            category = param or ""
            suggestions.extend([
                "\n💡 **Commandes suggérées:**",
                f"• `lister renseignements` - voir tous les renseignements",
                f"• `categories` - voir toutes les catégories",
                f"• `ajouter renseignement | nouveau titre | contenu | {category}` - ajouter dans cette catégorie"
            ])
        elif context == "categories":
            suggestions.extend([
                "\n💡 **Commandes suggérées:**",
                "• `lister renseignements` - voir tous les renseignements",
                "• `lister renseignements [categorie]` - filtrer par catégorie",
                "• `ajouter renseignement | titre | contenu | categorie` - ajouter un renseignement"
            ])

        return suggestions

    async def _parse_add_admin(self, message: str) -> Dict[str, Any]:
        """Parse add admin command"""
        try:
            parts = message.split()
            if len(parts) < 3:
                return {
                    "success": False,
                    "message": "Format: ajouter admin [numéro_de_téléphone]"
                }

            phone_number = parts[2]
            return await self.add_admin_phone(phone_number)
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur d'analyse: {str(e)}"
            }

    async def _parse_remove_admin(self, message: str) -> Dict[str, Any]:
        """Parse remove admin command"""
        try:
            parts = message.split()
            if len(parts) < 3:
                return {
                    "success": False,
                    "message": "Format: supprimer admin [numéro_de_téléphone]"
                }

            phone_number = parts[2]
            return await self.remove_admin_phone(phone_number)
        except Exception as e:
            return {
                "success": False,
                "message": f"Erreur d'analyse: {str(e)}"
            }

    async def _get_admin_help(self) -> Dict[str, Any]:
        """Get admin help information"""
        help_text = """
🔧 **Commandes Super Admin Disponibles:**

📝 **Gestion des renseignements:**
• `ajouter renseignement | titre | contenu | [categorie]`
• `modifier renseignement | ID | titre: nouveau_titre | contenu: nouveau_contenu | categorie: nouvelle_categorie`
• `desactiver renseignement [ID]`
• `lister renseignements [categorie]`
• `categories` - voir toutes les catégories

👥 **Gestion des administrateurs:**
• `ajouter admin [numéro]` - ajouter un nouvel administrateur
• `supprimer admin [numéro]` - supprimer un administrateur
• `lister admins` - voir tous les administrateurs

❓ **Aide:**
• `aide` ou `help` - afficher cette aide

📝 **Note:** Les commandes ne sont pas sensibles à la casse ni aux accents!

**Exemples (tous fonctionnent):**
• `AJOUTER RENSEIGNEMENT | Nouvel horaire | Les cours sont maintenant le samedi | horaire`
• `Ajouter renseignement | Nouvel horaire | Les cours sont maintenant le samedi | horaire`
• `AJOUTER RENSEIGNEMENT | Titre | Contenu | Catégorie`
• `modifier renseignement 1 | titre: Horaire mis à jour`
• `MODIFIER RENSEIGNEMENT 1 | TITRE: Horaire mis à jour`
• `desactiver renseignement 5`
• `DESACTIVER RENSEIGNEMENT 5`
• `lister renseignements horaire`
• `LISTER RENSEIGNEMENTS HORAIRE`
• `categories` ou `catégories` ou `CATEGORIES`
• `ajouter admin 221765001234`
• `listER admins`
• `AIDE` ou `help`
        """

        return {
            "success": True,
            "message": help_text.strip(),
            "is_help": True
        }

    async def _parse_search_catechumene(self, message: str) -> Dict[str, Any]:
        """Parse search catechumene command using profile service"""
        try:
            from src.services.profile_service import ProfileService
            profile_service = ProfileService()

            # Extract search term preserving case
            search_term = self._extract_search_term_original_case(message, ['rechercher', 'chercher', 'trouver'])

            if not search_term:
                return {
                    "success": False,
                    "message": "Veuillez spécifier un nom à rechercher. Ex: rechercher Badji"
                }

            # Use profile service to execute the search
            result = await profile_service.execute_action(
                action_id='search_catechumene',
                profile={'profile_id': 'admin_principal', 'profile_name': 'Administrateur Principal'},
                parameters={'search_term': search_term, 'search_type': 'name'}
            )

            return result

        except Exception as e:
            logger.error("search_catechumene_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur lors de la recherche: {str(e)}"
            }

    async def _parse_view_parent_info(self, message: str) -> Dict[str, Any]:
        """Parse view parent info command using profile service"""
        try:
            from src.services.profile_service import ProfileService
            profile_service = ProfileService()

            # Extract parent code preserving case
            parent_code = self._extract_search_term_original_case(message, ['voir', 'parent'])

            if not parent_code:
                return {
                    "success": False,
                    "message": "Veuillez spécifier un code parent. Ex: voir parent 57704"
                }

            # Use profile service to execute the action
            result = await profile_service.execute_action(
                action_id='view_parent_info',
                profile={'profile_id': 'admin_principal', 'profile_name': 'Administrateur Principal'},
                parameters={'parent_code': parent_code}
            )

            return result

        except Exception as e:
            logger.error("view_parent_info_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur lors de la consultation: {str(e)}"
            }

    async def _parse_list_classes(self, message: str) -> Dict[str, Any]:
        """Parse list classes command using profile service"""
        try:
            from src.services.profile_service import ProfileService
            profile_service = ProfileService()

            # Use profile service to execute the action
            result = await profile_service.execute_action(
                action_id='list_classes',
                profile={'profile_id': 'admin_principal', 'profile_name': 'Administrateur Principal'},
                parameters={}
            )

            return result

        except Exception as e:
            logger.error("list_classes_error", error=str(e))
            return {
                "success": False,
                "message": f"Erreur lors de la liste des classes: {str(e)}"
            }

    def _extract_search_term_original_case(self, message: str, keywords: list) -> str:
        """Extract search term preserving original case from message"""
        for keyword in keywords:
            # Find the keyword position in the original message (case-insensitive)
            keyword_lower = keyword.lower()
            message_lower = message.lower()

            keyword_pos = message_lower.find(keyword_lower)

            if keyword_pos != -1:
                # Extract everything after the keyword, preserving case
                search_term = message[keyword_pos + len(keyword):].strip()
                return search_term

        return ""