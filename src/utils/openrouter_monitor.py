"""
OpenRouter API Key Monitoring and Credit Management
"""

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenRouterMonitor:
    """Monitor OpenRouter API key usage and credits"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def check_key_credits(self) -> Dict[str, Any]:
        """
        Check credit usage and limits for an OpenRouter API key

        Returns:
            Dict containing key information including usage and limits
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/key",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    key_info = data.get('data', {})

                    result = {
                        'success': True,
                        'label': key_info.get('label', 'Unknown'),
                        'usage': key_info.get('usage', 0),
                        'limit': key_info.get('limit'),
                        'is_free_tier': key_info.get('is_free_tier', False),
                        'remaining_credits': self._calculate_remaining_credits(key_info),
                        'timestamp': datetime.now().isoformat()
                    }

                    logger.info(f"OpenRouter key {result['label']}: "
                              f"{result['usage']}/{result['limit']} credits used "
                              f"({result['remaining_credits']} remaining)")

                    return result
                else:
                    logger.error(f"Failed to check OpenRouter key credits: "
                               f"HTTP {response.status_code}")
                    return {
                        'success': False,
                        'error': f"HTTP {response.status_code}",
                        'timestamp': datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"Error checking OpenRouter key credits: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _calculate_remaining_credits(self, key_info: Dict[str, Any]) -> Optional[float]:
        """Calculate remaining credits based on usage and limit"""
        usage = key_info.get('usage', 0)
        limit = key_info.get('limit')

        if limit is None:
            return None  # Unlimited credits

        return max(0, limit - usage)

    @staticmethod
    async def check_multiple_keys(api_keys: list) -> Dict[str, Dict[str, Any]]:
        """
        Check credits for multiple OpenRouter API keys

        Args:
            api_keys: List of OpenRouter API keys

        Returns:
            Dict mapping each key to its credit information
        """
        results = {}

        for i, api_key in enumerate(api_keys, 1):
            monitor = OpenRouterMonitor(api_key)
            key_info = await monitor.check_key_credits()
            results[f"key_{i}"] = key_info

            # Add small delay between requests to avoid rate limiting
            if i < len(api_keys):
                import asyncio
                await asyncio.sleep(0.5)

        return results

    @staticmethod
    def format_credit_report(key_results: Dict[str, Dict[str, Any]]) -> str:
        """Format credit information into a readable report"""
        report = ["📊 OpenRouter API Key Credit Report", "=" * 40]

        for key_name, key_info in key_results.items():
            if key_info.get('success'):
                label = key_info.get('label', 'Unknown')
                usage = key_info.get('usage', 0)
                limit = key_info.get('limit')
                remaining = key_info.get('remaining_credits')
                is_free = key_info.get('is_free_tier', False)

                if limit is not None:
                    percentage = (usage / limit) * 100
                    status = "🟢" if percentage < 70 else "🟡" if percentage < 90 else "🔴"
                    credit_info = f"{usage:.2f}/{limit:.2f} credits ({percentage:.1f}%)"
                else:
                    status = "♾️"
                    credit_info = f"{usage:.2f} credits (unlimited)"

                report.append(f"{status} {key_name} ({label}): {credit_info}")
                if remaining is not None:
                    report.append(f"    Remaining: {remaining:.2f} credits")
                if is_free:
                    report.append(f"    Tier: Free")
            else:
                error = key_info.get('error', 'Unknown error')
                report.append(f"❌ {key_name}: Error - {error}")

            report.append("")  # Empty line for readability

        return "\n".join(report)


# Utility function for manual checking
async def check_openrouter_credits(api_keys: list) -> str:
    """
    Check OpenRouter API key credits and return formatted report

    Args:
        api_keys: List of OpenRouter API keys

    Returns:
        Formatted credit report string
    """
    if not api_keys:
        return "❌ No OpenRouter API keys provided"

    results = await OpenRouterMonitor.check_multiple_keys(api_keys)
    return OpenRouterMonitor.format_credit_report(results)