"""
Text normalization utilities for case-insensitive and accent-insensitive processing
"""

import re
import unicodedata
from typing import Optional

def normalize_french_text(text: str) -> str:
    """
    Normalize French text by removing accents and converting to lowercase

    Args:
        text: Input text to normalize

    Returns:
        Normalized text (lowercase, no accents)
    """
    if not text:
        return ""

    # Convert to lowercase first
    text = text.lower()

    # Remove accents using Unicode normalization
    # NFD (Normalization Form Decomposition) separates characters and accents
    normalized = unicodedata.normalize('NFD', text)

    # Remove accent characters (combining diacritical marks)
    no_accents = ''.join(
        char for char in normalized
        if not unicodedata.combining(char)
    )

    # Convert back to NFC form and return
    return unicodedata.normalize('NFC', no_accents)

def normalize_command(text: str) -> str:
    """
    Normalize command text for comparison

    Args:
        text: Command text to normalize

    Returns:
        Normalized command ready for comparison
    """
    if not text:
        return ""

    # Normalize French characters
    normalized = normalize_french_text(text)

    # Normalize whitespace and common punctuation
    normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single space
    normalized = normalized.strip()  # Remove leading/trailing spaces

    return normalized

def get_command_variations(command: str) -> list:
    """
    Generate common variations of a command for testing

    Args:
        command: Base command in normalized form

    Returns:
        List of possible variations
    """
    variations = [command]

    # Add common French accented variations
    accent_map = {
        'e': ['é', 'è', 'ê', 'ë'],
        'a': ['à', 'â', 'ä'],
        'i': ['î', 'ï'],
        'o': ['ô', 'ö'],
        'u': ['ù', 'û', 'ü'],
        'c': ['ç'],
    }

    # Generate accented versions
    for base_char, accents in accent_map.items():
        if base_char in command:
            for accent in accents:
                variation = command.replace(base_char, accent)
                variations.append(variation)

    return variations

def commands_match(command1: str, command2: str) -> bool:
    """
    Check if two commands match after normalization

    Args:
        command1: First command
        command2: Second command

    Returns:
        True if commands match after normalization
    """
    norm1 = normalize_command(command1)
    norm2 = normalize_command(command2)

    return norm1 == norm2

def extract_command_and_params(message: str, command_keywords: list) -> Optional[tuple]:
    """
    Extract command and parameters from message

    Args:
        message: User message
        command_keywords: List of possible command keywords (normalized)

    Returns:
        Tuple of (matched_keyword, params) or None
    """
    normalized_message = normalize_command(message)

    for keyword in command_keywords:
        if normalized_message.startswith(keyword):
            # Extract parameters (everything after the keyword)
            params = message[len(keyword):].strip()
            return keyword, params

    return None

# Common command mappings
COMMAND_MAPPINGS = {
    # French commands with variations
    'ajouter': ['ajouter', 'add', 'ajout'],
    'modifier': ['modifier', 'update', 'modif', 'maj'],
    'desactiver': ['desactiver', 'deactivate', 'desact', 'disable'],
    'supprimer': ['supprimer', 'remove', 'suppr', 'delete', 'del'],
    'lister': ['lister', 'list', 'afficher', 'show', 'voir'],
    'categories': ['categories', 'categorie', 'catégories', 'catégorie', 'cats'],
    'aide': ['aide', 'help', 'assistance', 'commandes'],
    'admin': ['admin', 'administrateur', 'admins'],
    'renseignement': ['renseignement', 'renseignements', 'info', 'infos', 'information'],
}

def get_normalized_command_mapping() -> dict:
    """
    Get normalized command mapping for flexible command recognition

    Returns:
        Dictionary mapping normalized commands to their canonical form
    """
    mapping = {}

    for canonical, variations in COMMAND_MAPPINGS.items():
        for variation in variations:
            normalized = normalize_command(variation)
            mapping[normalized] = canonical

    return mapping