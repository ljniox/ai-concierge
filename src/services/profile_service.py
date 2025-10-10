"""
Profile and Action Management Service for Gust-IA
Handles user profiles, permissions, and action execution
"""

import json
import time
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from src.utils.database import get_supabase_client
from src.utils.text_normalization import normalize_command
from src.services.response_formatter import ResponseFormatter
from src.services.claude_service import ServiceType
import structlog

logger = structlog.get_logger()

class ExecutionStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"

class ProfileService:
    """Service for managing profiles and executing actions"""

    def __init__(self):
        self.supabase = get_supabase_client()
        self.formatter = ResponseFormatter()
        self.action_cache = {}
        self.profile_cache = {}

    async def get_profile_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get profile by phone number"""
        try:
            # Nettoyer le numéro de téléphone
            clean_phone = self._clean_phone_number(phone_number)

            result = self.supabase.table('profile_phones').select(
                '*, profiles(*)'
            ).eq('phone_number', clean_phone).eq('is_active', True).execute()

            if result.data:
                profile_data = result.data[0]
                profile = profile_data.get('profiles', {})
                profile['phone_number'] = clean_phone
                return profile

            return None

        except Exception as e:
            logger.error("profile_retrieval_error", phone=phone_number, error=str(e))
            return None

    async def check_permission(self, profile_id: str, required_permissions: List[str]) -> bool:
        """Check if profile has required permissions"""
        try:
            if not profile_id:
                return False

            result = self.supabase.table('profiles').select('permissions').eq('profile_id', profile_id).eq('is_active', True).execute()

            if result.data:
                profile_permissions = result.data[0].get('permissions', [])

                # Vérifier si le profil a la permission super_admin
                if 'super_admin' in profile_permissions:
                    return True

                # Vérifier chaque permission requise
                for permission in required_permissions:
                    if permission not in profile_permissions:
                        return False

                return True

            return False

        except Exception as e:
            logger.error("permission_check_error", profile=profile_id, permissions=required_permissions, error=str(e))
            return False

    async def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get action configuration"""
        try:
            # Vérifier le cache
            if action_id in self.action_cache:
                return self.action_cache[action_id]

            result = self.supabase.table('actions').select('*').eq('action_id', action_id).eq('is_active', True).execute()

            if result.data:
                action_data = result.data[0]
                # Mettre en cache
                self.action_cache[action_id] = action_data
                return action_data

            return None

        except Exception as e:
            logger.error("action_retrieval_error", action=action_id, error=str(e))
            return None

    async def execute_action(self, profile: Dict[str, Any], action_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action with given parameters"""
        start_time = time.time()
        execution_id = None

        try:
            # Loguer le début de l'exécution
            log_result = self.supabase.table('action_logs').insert({
                'profile_id': profile.get('profile_id'),
                'phone_number': profile.get('phone_number'),
                'action_id': action_id,
                'parameters': parameters,
                'execution_status': ExecutionStatus.PENDING.value
            }).execute()

            if log_result.data:
                execution_id = log_result.data[0]['id']

            # Récupérer la configuration de l'action
            action = await self.get_action(action_id)
            if not action:
                raise ValueError(f"Action '{action_id}' non trouvée")

            # Vérifier les permissions
            required_permissions = action.get('required_permissions', [])
            if not await self.check_permission(profile.get('profile_id'), required_permissions):
                raise PermissionError(f"Permissions insuffisantes pour l'action '{action_id}'")

            # Valider les paramètres
            validated_params = await self._validate_parameters(action, parameters)

            # Exécuter les opérations de base de données
            result = await self._execute_database_operations(action, validated_params)

            # Formatter la réponse
            response = await self._format_response(action, result, validated_params)

            # Mettre à jour le log
            execution_time = int((time.time() - start_time) * 1000)
            if execution_id:
                self.supabase.table('action_logs').update({
                    'execution_status': ExecutionStatus.SUCCESS.value,
                    'response_data': response,
                    'execution_time': execution_time
                }).eq('id', execution_id).execute()

            return {
                'success': True,
                'response': response,
                'execution_time': execution_time
            }

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_message = str(e)

            # Mettre à jour le log avec l'erreur
            if execution_id:
                self.supabase.table('action_logs').update({
                    'execution_status': ExecutionStatus.ERROR.value,
                    'error_message': error_message,
                    'execution_time': execution_time
                }).eq('id', execution_id).execute()

            logger.error("action_execution_error", action=action_id, profile=profile.get('profile_id'), error=error_message)

            return {
                'success': False,
                'error': error_message,
                'execution_time': execution_time
            }

    async def _validate_parameters(self, action: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate action parameters"""
        action_params = action.get('parameters', [])
        validated = {}

        for param_config in action_params:
            param_name = param_config['name']
            param_type = param_config['type']
            is_required = param_config.get('required', False)
            default_value = param_config.get('default')

            # Récupérer la valeur ou utiliser la valeur par défaut
            value = parameters.get(param_name, default_value)

            # Vérifier si le paramètre est requis
            if is_required and value is None:
                raise ValueError(f"Paramètre requis manquant: {param_name}")

            # Valider le type
            if value is not None:
                if param_type == 'string':
                    validated[param_name] = str(value)
                elif param_type == 'integer':
                    try:
                        validated[param_name] = int(value)
                    except ValueError:
                        raise ValueError(f"Paramètre '{param_name}' doit être un entier: {value}")
                elif param_type == 'boolean':
                    validated[param_name] = bool(value)
                else:
                    validated[param_name] = value
            elif default_value is not None:
                validated[param_name] = default_value

        return validated

    async def _execute_database_operations(self, action: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database operations defined in action"""
        operations = action.get('database_operations', [])
        results = {}

        for i, operation in enumerate(operations):
            try:
                table = operation['table']
                operation_type = operation['operation']

                if operation_type == 'select':
                    result = await self._execute_select_operation(operation, parameters)
                    results[f'operation_{i}'] = result
                elif operation_type == 'insert':
                    result = await self._execute_insert_operation(operation, parameters)
                    results[f'operation_{i}'] = result
                elif operation_type == 'update':
                    result = await self._execute_update_operation(operation, parameters)
                    results[f'operation_{i}'] = result
                elif operation_type == 'delete':
                    result = await self._execute_delete_operation(operation, parameters)
                    results[f'operation_{i}'] = result

            except Exception as e:
                logger.error("database_operation_error", operation=operation, error=str(e))
                raise e

        return results

    async def _execute_select_operation(self, operation: Dict[str, Any], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute SELECT operation"""
        table = operation['table']
        fields = operation.get('fields', ['*'])
        conditions = operation.get('conditions', [])
        joins = operation.get('joins', [])
        order_by = operation.get('order_by')
        limit = operation.get('limit')

        # Construire la requête
        query = self.supabase.table(table).select(', '.join(fields))

        # Ajouter les conditions
        for condition in conditions:
            if condition.get('optional', False) and not parameters.get(condition['field'].split('.')[0]):
                continue

            field = condition['field']
            operator = condition['operator']
            value_template = condition['value']

            # Remplacer les paramètres dans le template
            value = value_template.format(**parameters)

            if operator == '=':
                query = query.eq(field, value)
            elif operator == 'ilike':
                query = query.like(field, value)
            elif operator == '!=':
                query = query.neq(field, value)
            elif operator == '>':
                query = query.gt(field, value)
            elif operator == '<':
                query = query.lt(field, value)

        # Ajouter le tri
        if order_by:
            if 'DESC' in order_by.upper():
                field = order_by.replace('DESC', '').strip()
                query = query.order(field, desc=True)
            else:
                query = query.order(order_by)

        # Ajouter la limite
        if limit:
            limit_value = int(limit.format(**parameters))
            query = query.limit(limit_value)

        # Exécuter la requête
        result = query.execute()
        return result.data if result.data else []

    async def _execute_insert_operation(self, operation: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute INSERT operation"""
        table = operation['table']
        fields = operation['fields']

        # Remplacer les paramètres dans les valeurs
        insert_data = {}
        for field, value_template in fields.items():
            insert_data[field] = value_template.format(**parameters)

        result = self.supabase.table(table).insert(insert_data).execute()
        return result.data[0] if result.data else {}

    async def _execute_update_operation(self, operation: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute UPDATE operation"""
        table = operation['table']
        fields = operation['fields']
        conditions = operation.get('conditions', [])

        # Remplacer les paramètres dans les valeurs
        update_data = {}
        for field, value_template in fields.items():
            update_data[field] = value_template.format(**parameters)

        # Construire la requête
        query = self.supabase.table(table).update(update_data)

        # Ajouter les conditions
        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            value = condition['value'].format(**parameters)

            if operator == '=':
                query = query.eq(field, value)
            elif operator == 'ilike':
                query = query.like(field, value)

        result = query.execute()
        return result.data[0] if result.data else {}

    async def _execute_delete_operation(self, operation: Dict[str, Any], parameters: Dict[str, Any]) -> bool:
        """Execute DELETE operation"""
        table = operation['table']
        conditions = operation.get('conditions', [])

        # Construire la requête
        query = self.supabase.table(table).delete()

        # Ajouter les conditions
        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            value = condition['value'].format(**parameters)

            if operator == '=':
                query = query.eq(field, value)
            elif operator == 'ilike':
                query = query.like(field, value)

        result = query.execute()
        return len(result.data) > 0 if result.data else False

    async def _format_response(self, action: Dict[str, Any], result: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Format response using action template"""
        response_format = action.get('response_format', {})

        # Récupérer les données principales
        main_result = result.get('operation_0', [])

        if not main_result:
            template = response_format.get('empty_template', response_format.get('error_template', 'Aucun résultat trouvé'))
            return template.format(**parameters)

        if len(main_result) == 1:
            # Résultat unique
            template = response_format.get('success_template', 'Résultat: {result}')
            data = main_result[0]

            # Formater pour un seul élément
            if action['action_id'] == 'search_catechumene':
                return template.format(**data, **parameters)
            elif action['action_id'] == 'view_parent_info':
                children_count = len(main_result) - 1 if len(main_result) > 1 else 0
                children_list = '\n'.join([f"• {child.get('nom', '')} {child.get('prenom', '')} ({child.get('classe_nom', 'N/A')})" for child in main_result[1:]])
                return template.format(**data, children_count=children_count, children_list=children_list, **parameters)
            else:
                return template.format(**data, **parameters)
        else:
            # Résultats multiples
            template = response_format.get('multiple_results_template', response_format.get('success_template'))

            if action['action_id'] == 'list_class_students':
                student_list = '\n'.join([f"• {student.get('nom', '')} {student.get('prenom', '')}" for student in main_result])
                classe_nom = main_result[0].get('classe_nom', parameters.get('class_name', 'classe'))
                return template.format(student_list=student_list, classe_nom=classe_nom, **parameters)
            elif action['action_id'] == 'list_renseignements':
                renseignements_list = '\n'.join([f"📝 {r.get('titre', '')} ({r.get('categorie', '')})" for r in main_result])
                categorie_filter = parameters.get('categorie', 'toutes catégories')
                return template.format(renseignements_list=renseignements_list, categorie_filter=categorie_filter, **parameters)
            elif action['action_id'] == 'check_class_schedule':
                schedule_list = '\n'.join([f"📅 {sched.get('nom', '')}: {sched.get('jour', '')} {sched.get('horaire', '')}" for sched in main_result])
                return template.format(schedule_list=schedule_list, **parameters)
            elif action['action_id'] == 'list_classes':
                classes_list = '\n'.join([f"📚 {classe.get('classe_nom', '')} ({classe.get('niveau', '')})" for classe in main_result])
                return template.format(classes_list=classes_list, **parameters)
            else:
                results_text = '\n'.join([str(item) for item in main_result])
                return template.format(results=results_text, count=len(main_result), **parameters)

    def _clean_phone_number(self, phone_number: str) -> str:
        """Clean phone number for consistent storage"""
        # Supprimer tous les caractères non numériques
        cleaned = ''.join(filter(str.isdigit, str(phone_number)))

        # Si le numéro commence par 0, le remplacer par l'indicatif international
        if cleaned.startswith('0'):
            cleaned = '221' + cleaned[1:]

        return cleaned

    async def parse_profile_command(self, message: str, phone_number: str) -> Dict[str, Any]:
        """Parse message for profile actions"""
        normalized_message = normalize_command(message)

        # Récupérer le profil
        profile = await self.get_profile_by_phone(phone_number)

        if not profile:
            return {
                'action': 'no_profile',
                'message': "Aucun profil trouvé pour ce numéro de téléphone.",
                'profile': None
            }

        # Analyser les commandes disponibles
        action_patterns = {
            'rechercher': 'search_catechumene',
            'chercher': 'search_catechumene',
            'trouver': 'search_catechumene',
            'liste': 'list_class_students',
            'lister': 'list_class_students',
            'voir': 'view_parent_info',
            'parent': 'view_parent_info',
            'horaire': 'check_class_schedule',
            'emploi': 'check_class_schedule',
            'planning': 'check_class_schedule',
            'ajouter': 'add_renseignement',
            'renseignement': 'add_renseignement',
            'info': 'list_renseignements',
            'informations': 'list_renseignements'
        }

        # Chercher des correspondances
        for keyword, action_id in action_patterns.items():
            if keyword in normalized_message:
                # Extraire les paramètres en préservant la casse originale
                params = self._extract_parameters_original_case(message, normalized_message, action_id, keyword)

                return {
                    'action': 'execute_action',
                    'action_id': action_id,
                    'parameters': params,
                    'profile': profile,
                    'raw_message': message
                }

        return {
            'action': 'unknown_command',
            'message': "Commande non reconnue. Essayez: rechercher [nom], liste [classe], parent [code], horaire [classe]",
            'profile': profile
        }

    def _extract_parameters_original_case(self, original_message: str, normalized_message: str, action_id: str, matched_keyword: str) -> Dict[str, Any]:
        """Extract parameters from message preserving original case"""
        params = {}

        if action_id == 'search_catechumene':
            # Extraire le terme de recherche en préservant la casse originale
            search_term = self._extract_search_term_original_case(original_message, matched_keyword)
            if search_term:
                params['search_term'] = search_term
                params['search_type'] = 'name'

        elif action_id == 'list_class_students':
            # Extraire le nom de la classe en préservant la casse
            class_name = self._extract_search_term_original_case(original_message, matched_keyword)
            if class_name:
                params['class_name'] = class_name

        elif action_id == 'view_parent_info':
            # Extraire le code parent en préservant la casse
            parent_code = self._extract_search_term_original_case(original_message, matched_keyword)
            if parent_code:
                params['parent_code'] = parent_code

        elif action_id == 'check_class_schedule':
            # Extraire le nom de la classe (optionnel) en préservant la casse
            class_name = self._extract_search_term_original_case(original_message, matched_keyword)
            if class_name:
                params['class_name'] = class_name

        elif action_id == 'add_renseignement':
            # Extraire titre et contenu en préservant la casse
            if '|' in original_message:
                parts = [p.strip() for p in original_message.split('|')]
                if len(parts) >= 2:
                    # Remove the keyword from the first part
                    keyword_lower = matched_keyword.lower()
                    title = parts[0].lower()
                    if keyword_lower in title:
                        title = title[len(keyword_lower):].strip()

                    params['titre'] = title
                    params['contenu'] = parts[1]
                    if len(parts) >= 3:
                        params['categorie'] = parts[2]
                    if len(parts) >= 4:
                        params['priorite'] = int(parts[3])

        elif action_id == 'list_renseignements':
            # Extraire la catégorie (optionnel) en préservant la casse
            category = self._extract_search_term_original_case(original_message, matched_keyword)
            if category:
                params['categorie'] = category

        return params

    def _extract_search_term_original_case(self, original_message: str, keyword: str) -> str:
        """Extract search term preserving original case from original message"""
        # Find the keyword position in the original message (case-insensitive)
        keyword_lower = keyword.lower()
        message_lower = original_message.lower()

        keyword_pos = message_lower.find(keyword_lower)

        if keyword_pos != -1:
            # Extract everything after the keyword, preserving case
            search_term = original_message[keyword_pos + len(keyword):].strip()
            return search_term

        return ""

    def _extract_parameters(self, message: str, action_id: str) -> Dict[str, Any]:
        """Extract parameters from message based on action type (legacy method)"""
        params = {}

        if action_id == 'search_catechumene':
            # Extraire le terme de recherche
            search_term = message.replace('rechercher', '').replace('chercher', '').replace('trouver', '').strip()
            if search_term:
                params['search_term'] = search_term
                params['search_type'] = 'name'

        elif action_id == 'list_class_students':
            # Extraire le nom de la classe
            class_name = message.replace('liste', '').replace('lister', '').replace('élèves', '').replace('eleves', '').strip()
            if class_name:
                params['class_name'] = class_name

        elif action_id == 'view_parent_info':
            # Extraire le code parent
            parent_code = message.replace('voir', '').replace('parent', '').strip()
            if parent_code:
                params['parent_code'] = parent_code

        elif action_id == 'check_class_schedule':
            # Extraire le nom de la classe (optionnel)
            class_name = message.replace('horaire', '').replace('emploi', '').replace('planning', '').strip()
            if class_name:
                params['class_name'] = class_name

        elif action_id == 'add_renseignement':
            # Extraire titre et contenu (format: ajouter renseignement | titre | contenu)
            if '|' in message:
                parts = [p.strip() for p in message.split('|')]
                if len(parts) >= 2:
                    params['titre'] = parts[0].replace('ajouter', '').replace('renseignement', '').strip()
                    params['contenu'] = parts[1]
                    if len(parts) >= 3:
                        params['categorie'] = parts[2]
                    if len(parts) >= 4:
                        params['priorite'] = int(parts[3])

        elif action_id == 'list_renseignements':
            # Extraire la catégorie (optionnel)
            category = message.replace('info', '').replace('informations', '').replace('renseignements', '').strip()
            if category:
                params['categorie'] = category

        return params

    
    async def load_actions_from_config(self, config_file: str) -> bool:
        """Load actions from JSON configuration file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Charger les profils
            for profile_config in config.get('profiles', []):
                await self._create_profile_from_config(profile_config)

            # Charger les actions
            for action_config in config.get('actions', []):
                await self._create_action_from_config(action_config)

            logger.info("actions_loaded_from_config", config=config_file)
            return True

        except Exception as e:
            logger.error("config_loading_error", config=config_file, error=str(e))
            return False

    async def _create_profile_from_config(self, profile_config: Dict[str, Any]) -> bool:
        """Create profile from configuration"""
        try:
            profile_data = {
                'profile_id': profile_config['profile_id'],
                'profile_name': profile_config['profile_name'],
                'description': profile_config.get('description', ''),
                'permissions': profile_config.get('permissions', []),
                'default_locale': profile_config.get('default_locale', 'fr'),
                'is_active': profile_config.get('is_active', True)
            }

            # Insérer ou mettre à jour le profil
            result = self.supabase.table('profiles').upsert(profile_data).execute()

            # Ajouter les numéros de téléphone
            for phone_number in profile_config.get('phone_numbers', []):
                phone_data = {
                    'profile_id': profile_config['profile_id'],
                    'phone_number': phone_number,
                    'is_primary': phone_number == profile_config.get('phone_numbers', [])[0]
                }
                self.supabase.table('profile_phones').upsert(phone_data).execute()

            return True

        except Exception as e:
            logger.error("profile_creation_error", profile=profile_config.get('profile_id'), error=str(e))
            return False

    async def _create_action_from_config(self, action_config: Dict[str, Any]) -> bool:
        """Create action from configuration"""
        try:
            action_data = {
                'action_id': action_config['action_id'],
                'name': action_config['name'],
                'description': action_config.get('description', ''),
                'category': action_config.get('category', 'general'),
                'required_permissions': action_config.get('required_permissions', []),
                'parameters': action_config.get('parameters', []),
                'database_operations': action_config.get('database_operations', []),
                'response_format': action_config.get('response_format', {}),
                'is_active': action_config.get('is_active', True)
            }

            # Insérer ou mettre à jour l'action
            result = self.supabase.table('actions').upsert(action_data).execute()

            # Mettre à jour le cache
            self.action_cache[action_config['action_id']] = action_data

            return True

        except Exception as e:
            logger.error("action_creation_error", action=action_config.get('action_id'), error=str(e))
            return False