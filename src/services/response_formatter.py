"""
Response formatting service for Gust-IA with custom prefix and service indicators
"""

from typing import Optional, Dict, Any
from src.services.claude_service import ServiceType
import structlog

logger = structlog.get_logger()

class ResponseFormatter:
    """Service for formatting responses with Gust-IA branding"""

    def __init__(self):
        self.ai_name = "Gust-IA"
        self.separator = "----------------------------¬"

    def format_response(
        self,
        response_content: str,
        service_type: ServiceType,
        is_admin: bool = False
    ) -> str:
        """
        Format response with Gust-IA prefix and service indicator

        Args:
            response_content: The raw response content
            service_type: The service type that generated the response
            is_admin: Whether this is an admin response

        Returns:
            Formatted response string
        """
        try:
            # Get service display name
            service_display = self._get_service_display_name(service_type, is_admin)

            # Create prefix based on service type
            if is_admin:
                prefix = f"[{self.ai_name}-Admin]"
            elif service_display:
                prefix = f"[{self.ai_name}] | {service_display}"
            else:
                prefix = f"[{self.ai_name}]"

            # Format the response
            formatted_response = f"{prefix}\n{self.separator}\n{response_content}"

            return formatted_response

        except Exception as e:
            logger.error("response_formatting_error", error=str(e))
            # Fallback to simple formatting
            return f"[{self.ai_name}]\n{self.separator}\n{response_content}"

    def _get_service_display_name(self, service_type: ServiceType, is_admin: bool) -> Optional[str]:
        """Get display name for service type"""
        if is_admin:
            return "Super Admin"

        service_names = {
            ServiceType.RENSEIGNEMENT: "Renseignements",
            ServiceType.CATECHESE: "Catéchèse",
            ServiceType.CONTACT_HUMAIN: "Contact Humain",
            ServiceType.SUPER_ADMIN: "Super Admin"
        }

        return service_names.get(service_type)

    def format_admin_help(self, help_content: str) -> str:
        """Format admin help response"""
        return self.format_response(help_content, ServiceType.SUPER_ADMIN, is_admin=True)

    def format_error_response(self, error_message: str, service_type: ServiceType = ServiceType.CONTACT_HUMAIN) -> str:
        """Format error response"""
        return self.format_response(
            f"❌ Erreur: {error_message}",
            service_type
        )

    def format_success_response(self, success_message: str, service_type: ServiceType) -> str:
        """Format success response"""
        emoji = self._get_success_emoji(service_type)
        return self.format_response(
            f"{emoji} {success_message}",
            service_type
        )

    def _get_success_emoji(self, service_type: ServiceType) -> str:
        """Get appropriate emoji for service type"""
        emojis = {
            ServiceType.RENSEIGNEMENT: "ℹ️",
            ServiceType.CATECHESE: "🙏",
            ServiceType.CONTACT_HUMAIN: "📞",
            ServiceType.SUPER_ADMIN: "🔧"
        }
        return emojis.get(service_type, "✅")

    def extract_text_from_claude_response(self, claude_response: Dict[str, Any]) -> str:
        """Extract text content from Claude API response"""
        try:
            content = claude_response.get('content', [])
            if content and isinstance(content, list) and len(content) > 0:
                text_content = content[0].get('text', '')
                return text_content.strip()
            return ""
        except Exception as e:
            logger.error("text_extraction_error", error=str(e))
            return ""

    def format_renseignement_list(self, renseignements: list) -> str:
        """Format list of renseignements for display"""
        if not renseignements:
            return "Aucun renseignement disponible."

        formatted_items = []
        for i, renseignement in enumerate(renseignements[:5], 1):  # Limit to 5 items
            titre = renseignement.get('titre', f'Renseignement {i}')
            contenu = renseignement.get('contenu', '')
            categorie = renseignement.get('categorie', 'général')

            # Truncate long content
            if len(contenu) > 100:
                contenu = contenu[:100] + "..."

            formatted_items.append(f"{i}. **{titre}** ({categorie})\n   {contenu}")

        result = "📋 **Renseignements disponibles:**\n\n" + "\n\n".join(formatted_items)

        if len(renseignements) > 5:
            result += f"\n\n... et {len(renseignements) - 5} autres renseignements."

        return result