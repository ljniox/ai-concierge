"""
Enrollment Workflow Service - Conversationnel Flow

Gère le processus d'enrôlement conversationnel étape par étape:

1. Choix: Nouvelle inscription vs Réinscription
2. Si Réinscription: Chargement catéchumènes existants + classe prédéfinie
3. Si Nouvelle/Transfert: Vérification âge via OCR (extrait naissance/baptême)
4. Détermination classes possibles selon âge
5. Collecte infos parent et enfant avec validation OCR
6. Confirmation année d'inscription
7. Preuve de paiement (texte ou image avec OCR)
8. Validation manuelle par trésorier avant confirmation

Constitution Principle: User-friendly conversational interface
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from ..database.sqlite_manager import get_sqlite_manager
from ..models.enrollment import Inscription, InscriptionStatut
from ..models.legacy import LegacyCatechumene, LegacyParent, LegacyDataQueries
from ..services.ocr_service import get_ocr_service
from ..services.document_storage_service import get_document_storage_service
from ..services.enrollment_service import get_enrollment_service
from ..services.audit_service import log_user_action
from ..utils.exceptions import ValidationError, BusinessLogicError

logger = logging.getLogger(__name__)


class WorkflowStep(Enum):
    """Étapes du workflow d'enrôlement."""
    INITIAL_CHOICE = "initial_choice"  # Nouvelle vs Réinscription
    REENROLLMENT_SELECT = "reenrollment_select"  # Sélection catéchumène existant
    REENROLLMENT_CONFIRM = "reenrollment_confirm"  # Confirmation classe prédéfinie
    AGE_VERIFICATION = "age_verification"  # Vérification âge via OCR
    CLASS_SELECTION = "class_selection"  # Sélection classe selon âge
    PARENT_INFO = "parent_info"  # Infos parent
    CHILD_INFO = "child_info"  # Infos enfant avec validation OCR
    CONFIRM_DATA = "confirm_data"  # Confirmation données OCR
    YEAR_SELECTION = "year_selection"  # Choix année inscription
    PAYMENT_PROOF = "payment_proof"  # Preuve paiement
    TREASURER_VALIDATION = "treasurer_validation"  # Validation manuelle trésorier
    COMPLETED = "completed"  # Terminé
    PENDING_HUMAN = "pending_human"  # En attente intervention humaine


class EnrollmentWorkflowService:
    """
    Service de workflow d'enrôlement conversationnel.

    Gère le processus complet d'enrôlement via WhatsApp/Telegram
    avec validation OCR et intervention humaine quand nécessaire.
    """

    def __init__(self):
        self.manager = get_sqlite_manager()
        self.ocr_service = get_ocr_service()
        self.document_service = get_document_storage_service()
        self.enrollment_service = get_enrollment_service()
        self.fixed_fee = Decimal('5000.00')
        self.workflows = {}  # user_id -> workflow_data

    async def start_workflow(self, user_id: str, telephone: str, channel: str) -> Dict[str, Any]:
        """
        Démarrer un nouveau workflow d'enrôlement.

        Args:
            user_id: ID utilisateur
            telephone: Numéro de téléphone
            channel: Canal (whatsapp/telegram)

        Returns:
            Dict: État initial du workflow
        """
        try:
            # Vérifier si parent existe dans legacy system
            legacy_parent = await self._find_legacy_parent(telephone)

            workflow_data = {
                "user_id": user_id,
                "telephone": telephone,
                "channel": channel,
                "current_step": WorkflowStep.INITIAL_CHOICE,
                "legacy_parent": legacy_parent,
                "enrollment_type": None,  # "new" or "reenrollment"
                "data": {},
                "documents": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            self.workflows[user_id] = workflow_data

            message = await self._generate_step_message(workflow_data)

            return {
                "workflow_id": user_id,
                "step": workflow_data["current_step"].value,
                "message": message,
                "options": await self._get_step_options(workflow_data)
            }

        except Exception as e:
            logger.error(f"Failed to start workflow for {user_id}: {e}")
            raise

    async def process_user_input(self, user_id: str, user_input: str,
                                file_data: Optional[bytes] = None,
                                filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Traiter l'entrée utilisateur et avancer dans le workflow.

        Args:
            user_id: ID utilisateur
            user_input: Texte de l'utilisateur
            file_data: Fichier uploadé (optionnel)
            filename: Nom du fichier (optionnel)

        Returns:
            Dict: Prochaine étape et message
        """
        try:
            if user_id not in self.workflows:
                raise ValidationError("Workflow not found for user")

            workflow = self.workflows[user_id]
            current_step = workflow["current_step"]

            logger.info(f"Processing input for {user_id} at step {current_step.value}")

            # Traiter selon l'étape actuelle
            if current_step == WorkflowStep.INITIAL_CHOICE:
                result = await self._handle_initial_choice(workflow, user_input)

            elif current_step == WorkflowStep.REENROLLMENT_SELECT:
                result = await self._handle_reenrollment_selection(workflow, user_input)

            elif current_step == WorkflowStep.REENROLLMENT_CONFIRM:
                result = await self._handle_reenrollment_confirmation(workflow, user_input)

            elif current_step == WorkflowStep.AGE_VERIFICATION:
                result = await self._handle_age_verification(workflow, file_data, filename)

            elif current_step == WorkflowStep.CLASS_SELECTION:
                result = await self._handle_class_selection(workflow, user_input)

            elif current_step == WorkflowStep.PARENT_INFO:
                result = await self._handle_parent_info(workflow, user_input)

            elif current_step == WorkflowStep.CHILD_INFO:
                result = await self._handle_child_info(workflow, user_input)

            elif current_step == WorkflowStep.CONFIRM_DATA:
                result = await self._handle_data_confirmation(workflow, user_input)

            elif current_step == WorkflowStep.YEAR_SELECTION:
                result = await self._handle_year_selection(workflow, user_input)

            elif current_step == WorkflowStep.PAYMENT_PROOF:
                result = await self._handle_payment_proof(workflow, file_data, filename, user_input)

            else:
                result = {
                    "step": current_step.value,
                    "message": "Étape non reconnue",
                    "next_step": None
                }

            workflow["updated_at"] = datetime.utcnow()

            return result

        except Exception as e:
            logger.error(f"Failed to process user input for {user_id}: {e}")
            raise

    async def _handle_initial_choice(self, workflow: Dict, user_input: str) -> Dict[str, Any]:
        """
        Gérer le choix initial: nouvelle inscription vs réinscription.
        """
        user_input = user_input.strip().lower()

        if "réinscription" in user_input or "reinscr" in user_input or "ancien" in user_input:
            workflow["enrollment_type"] = "reenrollment"

            if workflow["legacy_parent"]:
                # Charger les catéchumènes existants
                catechumenes = await self._get_legacy_catechumenes(workflow["legacy_parent"]["Code_Parent"])

                if catechumenes:
                    workflow["current_step"] = WorkflowStep.REENROLLMENT_SELECT
                    workflow["data"]["available_catechumenes"] = catechumenes

                    message = "Voici les catéchumènes trouvés pour ce parent:\n\n"
                    for i, catechumene in enumerate(catechumenes, 1):
                        message += f"{i}. {catechumene['Nom']} {catechumene['Prenoms']} (né en {catechumene['Ann_e_de_naissance']})\n"

                    message += f"\nChoisissez le numéro du catéchumène à réinscrire (1-{len(catechumenes)}):"

                    return {
                        "step": WorkflowStep.REENROLLMENT_SELECT.value,
                        "message": message,
                        "options": [str(i) for i in range(1, len(catechumenes) + 1)]
                    }
                else:
                    # Aucun catéchumène trouvé
                    workflow["current_step"] = WorkflowStep.NEW_ENROLLMENT
                    return {
                        "step": WorkflowStep.NEW_ENROLLMENT.value,
                        "message": "Aucun catéchumène trouvé. Procédons à une nouvelle inscription.\nVeuillez envoyer l'extrait de naissance ou de baptême pour vérifier l'âge:",
                        "options": None
                    }
            else:
                # Parent non trouvé dans legacy system
                workflow["current_step"] = WorkflowStep.NEW_ENROLLMENT
                return {
                    "step": WorkflowStep.NEW_ENROLLMENT.value,
                    "message": "Parent non trouvé dans nos archives. Procédons à une nouvelle inscription.\nVeuillez envoyer l'extrait de naissance ou de baptême pour vérifier l'âge:",
                    "options": None
                }

        elif "nouvelle" in user_input or "nouveau" in user_input or "inscript" in user_input:
            workflow["enrollment_type"] = "new"
            workflow["current_step"] = WorkflowStep.AGE_VERIFICATION

            return {
                "step": WorkflowStep.AGE_VERIFICATION.value,
                "message": "Pour une nouvelle inscription, veuillez envoyer l'extrait de naissance ou de baptême pour que nous puissions vérifier l'âge et déterminer la classe appropriée:",
                "options": None
            }

        else:
            return {
                "step": WorkflowStep.INITIAL_CHOICE.value,
                "message": "Veuillez choisir:\n1. Réinscription (pour un catéchumène déjà inscrit)\n2. Nouvelle inscription",
                "options": ["1", "2", "réinscription", "nouvelle"]
            }

    async def _handle_reenrollment_selection(self, workflow: Dict, user_input: str) -> Dict[str, Any]:
        """
        Gérer la sélection du catéchumène pour réinscription.
        """
        try:
            selection = int(user_input.strip())
            catechumenes = workflow["data"]["available_catechumenes"]

            if 1 <= selection <= len(catechumenes):
                selected_catechumene = catechumenes[selection - 1]
                workflow["data"]["selected_catechumene"] = selected_catechumene

                # Déterminer classe prédéfinie
                classe = await self._get_predefined_class(selected_catechumene)
                workflow["data"]["predefined_class"] = classe

                workflow["current_step"] = WorkflowStep.REENROLLMENT_CONFIRM

                message = f"Catéchumène sélectionné: {selected_catechumene['Nom']} {selected_catechumene['Prenoms']}\n"
                message += f"Classe suggérée: {classe.get('Nom', 'Non définie')}\n\n"
                message += "Confirmez-vous cette classe?\n1. Oui, continuer\n2. Non, changer de classe"

                return {
                    "step": WorkflowStep.REENROLLMENT_CONFIRM.value,
                    "message": message,
                    "options": ["1", "2", "oui", "non"]
                }
            else:
                return {
                    "step": WorkflowStep.REENROLLMENT_SELECT.value,
                    "message": f"Choix invalide. Veuillez choisir entre 1 et {len(catechumenes)}:",
                    "options": [str(i) for i in range(1, len(catechumenes) + 1)]
                }

        except ValueError:
            return {
                "step": WorkflowStep.REENROLLMENT_SELECT.value,
                "message": "Veuillez entrer un numéro valide:",
                "options": [str(i) for i in range(1, len(workflow["data"]["available_catechumenes"]) + 1)]
            }

    async def _handle_reenrollment_confirmation(self, workflow: Dict, user_input: str) -> Dict[str, Any]:
        """
        Gérer la confirmation de classe pour réinscription.
        """
        user_input = user_input.strip().lower()

        if user_input in ["1", "oui", "yes", "ok"]:
            # Confirmer la classe
            workflow["data"]["confirmed_class"] = workflow["data"]["predefined_class"]
            workflow["current_step"] = WorkflowStep.PAYMENT_PROOF

            return {
                "step": WorkflowStep.PAYMENT_PROOF.value,
                "message": f"Classe confirmée: {workflow['data']['predefined_class']['Nom']}\n\n"
                        f"Frais d'inscription: {self.fixed_fee} FCFA\n\n"
                        "Veuillez fournir la preuve de paiement:\n"
                        "1. Envoyer une image du reçu de paiement\n"
                        "2. Envoyer le numéro de référence de transaction",
                "options": None
            }

        elif user_input in ["2", "non", "no"]:
            # Changer de classe
            workflow["current_step"] = WorkflowStep.CLASS_SELECTION

            # Obtenir les classes disponibles selon l'âge
            birth_year = int(workflow["data"]["selected_catechumene"]["Ann_e_de_naissance"])
            age = date.today().year - birth_year
            available_classes = await self._get_classes_for_age(age)

            workflow["data"]["available_classes"] = available_classes

            message = "Classes disponibles selon l'âge:\n\n"
            for i, classe in enumerate(available_classes, 1):
                message += f"{i}. {classe['Nom']}\n"

            message += f"\nChoisissez la classe (1-{len(available_classes)}):"

            return {
                "step": WorkflowStep.CLASS_SELECTION.value,
                "message": message,
                "options": [str(i) for i in range(1, len(available_classes) + 1)]
            }

        else:
            return {
                "step": WorkflowStep.REENROLLMENT_CONFIRM.value,
                "message": "Veuillez répondre par 'oui' ou 'non':",
                "options": ["1", "2", "oui", "non"]
            }

    async def _handle_age_verification(self, workflow: Dict, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Gérer la vérification d'âge via OCR.
        """
        try:
            if not file_data:
                return {
                    "step": WorkflowStep.AGE_VERIFICATION.value,
                    "message": "Veuillez envoyer l'image de l'extrait de naissance ou de baptême:",
                    "options": None
                }

            # Upload document temporaire
            temp_doc = await self.document_service.upload_document(
                file_data=file_data,
                filename=filename,
                inscription_id="temp_" + workflow["user_id"],
                document_type="extrait_naissance",
                user_id=workflow["user_id"]
            )

            # Traiter OCR
            ocr_result = await self.ocr_service.process_document(temp_doc.id)

            if ocr_result["statut_ocr"] == "succes" and ocr_result["confiance_ocr"] >= 0.7:
                extraction_data = ocr_result["donnees_extraites"]

                # Calculer l'âge
                birth_date_str = extraction_data.get("date_naissance")
                if birth_date_str:
                    birth_date = self._parse_french_date(birth_date_str)
                    if birth_date:
                        age = self._calculate_age(birth_date)
                        workflow["data"]["birth_date"] = birth_date
                        workflow["data"]["age"] = age
                        workflow["data"]["ocr_data"] = extraction_data
                        workflow["data"]["temp_document_id"] = temp_doc.id

                        # Déterminer classes possibles
                        available_classes = await self._get_classes_for_age(age)
                        workflow["data"]["available_classes"] = available_classes

                        workflow["current_step"] = WorkflowStep.CLASS_SELECTION

                        message = f"Âge détecté: {age} ans\n\n"
                        message += "Classes disponibles:\n\n"
                        for i, classe in enumerate(available_classes, 1):
                            message += f"{i}. {classe['Nom']}\n"

                        message += f"\nChoisissez la classe (1-{len(available_classes)}):"

                        return {
                            "step": WorkflowStep.CLASS_SELECTION.value,
                            "message": message,
                            "options": [str(i) for i in range(1, len(available_classes) + 1)]
                        }

                # Si OCR ne peut pas déterminer l'âge
                workflow["current_step"] = WorkflowStep.PENDING_HUMAN

                return {
                    "step": WorkflowStep.PENDING_HUMAN.value,
                    "message": "Je n'ai pas pu déterminer l'âge à partir du document. Un agent humain va vous aider pour continuer l'inscription.",
                    "options": None
                }
            else:
                # OCR a échoué
                workflow["current_step"] = WorkflowStep.PENDING_HUMAN

                return {
                    "step": WorkflowStep.PENDING_HUMAN.value,
                    "message": "Le traitement OCR a échoué. Un agent humain va vous aider pour continuer l'inscription.",
                    "options": None
                }

        except Exception as e:
            logger.error(f"Age verification failed: {e}")
            workflow["current_step"] = WorkflowStep.PENDING_HUMAN

            return {
                "step": WorkflowStep.PENDING_HUMAN.value,
                "message": "Une erreur s'est produite lors de la vérification. Un agent humain va vous aider.",
                "options": None
            }

    def _parse_french_date(self, date_str: str) -> Optional[date]:
        """
        Parser une date française (DD/MM/YYYY ou autre format).
        """
        import re
        from datetime import datetime

        # Formats possibles
        patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]

        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if pattern == patterns[0] or pattern == patterns[1]:  # DD/MM/YYYY or DD-MM-YYYY
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day)).date()
                    else:  # YYYY-MM-DD
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day)).date()
                except ValueError:
                    continue

        return None

    def _calculate_age(self, birth_date: date) -> int:
        """Calculer l'âge à partir de la date de naissance."""
        today = date.today()
        age = today.year - birth_date.year

        # Ajuster si l'anniversaire n'est pas encore passé cette année
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1

        return age

    async def _get_classes_for_age(self, age: int) -> List[Dict]:
        """
        Obtenir les classes appropriées selon l'âge.
        """
        try:
            query = "SELECT * FROM classes WHERE Actif = 'True' ORDER BY Ordre"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query)
                all_classes = await cursor.fetchall()

            # Filtrer selon l'âge
            appropriate_classes = []
            for classe in all_classes:
                classe_data = dict(classe)
                # Logique simple pour déterminer les classes appropriées
                # En pratique, cela dépend des règles spécifiques de la paroisse
                if self._is_class_age_appropriate(classe_data, age):
                    appropriate_classes.append(classe_data)

            return appropriate_classes

        except Exception as e:
            logger.error(f"Failed to get classes for age {age}: {e}")
            return []

    def _is_class_age_appropriate(self, classe: Dict, age: int) -> bool:
        """
        Vérifier si la classe est appropriée pour l'âge donné.
        """
        # Logique simplifiée - à adapter selon les règles de la paroisse
        class_name = classe.get('Nom', '').lower()

        if 'éveil' in class_name and 4 <= age <= 6:
            return True
        elif 'ce1' in class_name and 6 <= age <= 8:
            return True
        elif 'ce2' in class_name and 7 <= age <= 9:
            return True
        elif 'cm1' in class_name and 8 <= age <= 10:
            return True
        elif 'cm2' in class_name and 9 <= age <= 11:
            return True
        elif 'confirmation' in class_name and 12 <= age <= 15:
            return True

        return False

    async def _handle_class_selection(self, workflow: Dict, user_input: str) -> Dict[str, Any]:
        """
        Gérer la sélection de classe.
        """
        try:
            selection = int(user_input.strip())
            classes = workflow["data"]["available_classes"]

            if 1 <= selection <= len(classes):
                selected_class = classes[selection - 1]
                workflow["data"]["selected_class"] = selected_class
                workflow["current_step"] = WorkflowStep.PARENT_INFO

                return {
                    "step": WorkflowStep.PARENT_INFO.value,
                    "message": f"Classe sélectionnée: {selected_class['Nom']}\n\n"
                            "Veuillez fournir les informations du parent:\n"
                            "1. Nom complet du parent\n"
                            "2. Prénom(s) du parent\n"
                            "3. Numéro de téléphone\n"
                            "4. Email (optionnel)",
                    "options": None
                }
            else:
                return {
                    "step": WorkflowStep.CLASS_SELECTION.value,
                    "message": f"Choix invalide. Veuillez choisir entre 1 et {len(classes)}:",
                    "options": [str(i) for i in range(1, len(classes) + 1)]
                }

        except ValueError:
            return {
                "step": WorkflowStep.CLASS_SELECTION.value,
                "message": "Veuillez entrer un numéro valide:",
                "options": [str(i) for i in range(1, len(workflow["data"]["available_classes"]) + 1)]
            }

    async def _handle_parent_info(self, workflow: Dict, user_input: str) -> Dict[str, Any]:
        """
        Gérer la collecte des informations parent.
        """
        # Parser les informations parent (format attendu: nom;prénom;téléphone;email)
        parts = [part.strip() for part in user_input.split(';')]

        if len(parts) >= 3:  # nom, prénom, téléphone obligatoires
            workflow["data"]["parent_info"] = {
                "nom": parts[0],
                "prenom": parts[1],
                "telephone": parts[2],
                "email": parts[3] if len(parts) > 3 else None
            }

            workflow["current_step"] = WorkflowStep.CHILD_INFO

            return {
                "step": WorkflowStep.CHILD_INFO.value,
                "message": "Informations parent enregistrées.\n\n"
                        "Veuillez maintenant fournir les informations de l'enfant:\n"
                        "1. Nom de l'enfant\n"
                        "2. Prénom(s) de l'enfant\n"
                        "3. Date de naissance (format: JJ/MM/AAAA)\n"
                        "4. Lieu de naissance\n"
                        "5. A-t-il été baptisé? (oui/non)",
                "options": None
            }
        else:
            return {
                "step": WorkflowStep.PARENT_INFO.value,
                "message": "Format incorrect. Veuillez fournir: nom;prenom;telephone;email (email optionnel)\n"
                        "Exemple: DIALLO;Amadou;+221770000001;amadou@email.com",
                "options": None
            }

    async def _handle_child_info(self, workflow: Dict, user_input: str) -> Dict[str, Any]:
        """
        Gérer la collecte des informations enfant avec validation OCR.
        """
        # Parser les informations enfant
        parts = [part.strip() for part in user_input.split(';')]

        if len(parts) >= 5:
            child_info = {
                "nom": parts[0],
                "prenom": parts[1],
                "date_naissance": parts[2],
                "lieu_naissance": parts[3],
                "baptise": parts[4].lower() in ["oui", "yes", "o", "y"]
            }

            workflow["data"]["child_info"] = child_info
            workflow["current_step"] = WorkflowStep.CONFIRM_DATA

            # Valider la date de naissance
            birth_date = self._parse_french_date(child_info["date_naissance"])
            if not birth_date:
                return {
                    "step": WorkflowStep.CHILD_INFO.value,
                    "message": "Format de date incorrect. Veuillez utiliser JJ/MM/AAAA.",
                    "options": None
                }

            # Afficher les informations à confirmer
            message = "Voici les informations de l'enfant à confirmer:\n\n"
            message += f"Nom: {child_info['nom']}\n"
            message += f"Prénom(s): {child_info['prenom']}\n"
            message += f"Date de naissance: {child_info['date_naissance']}\n"
            message += f"Lieu de naissance: {child_info['lieu_naissance']}\n"
            message += f"Baptisé: {'Oui' if child_info['baptise'] else 'Non'}\n\n"

            # Ajouter les données OCR si disponibles
            if "ocr_data" in workflow["data"]:
                message += "Données extraites par OCR:\n"
                ocr_data = workflow["data"]["ocr_data"]
                if ocr_data.get("nom"):
                    message += f"- Nom OCR: {ocr_data['nom']}\n"
                if ocr_data.get("prenom"):
                    message += f"- Prénom OCR: {ocr_data['prenom']}\n"
                if ocr_data.get("date_naissance"):
                    message += f"- Date OCR: {ocr_data['date_naissance']}\n"

            message += "\nConfirmez-vous ces informations?\n1. Oui, tout est correct\n2. Non, je veux corriger"

            return {
                "step": WorkflowStep.CONFIRM_DATA.value,
                "message": message,
                "options": ["1", "2", "oui", "non"]
            }
        else:
            return {
                "step": WorkflowStep.CHILD_INFO.value,
                "message": "Format incorrect. Veuillez fournir: nom;prenom;date_naissance;lieu_naissance;baptise\n"
                        "Exemple: DIALLO;Amadou;12/03/2015;Dakar;oui",
                "options": None
            }

    async def _handle_data_confirmation(self, workflow: Dict, user_input: str) -> Dict[str, Any]:
        """
        Gérer la confirmation des données.
        """
        user_input = user_input.strip().lower()

        if user_input in ["1", "oui", "yes", "ok"]:
            # Données confirmées
            workflow["current_step"] = WorkflowStep.YEAR_SELECTION

            current_year = datetime.now().year
            next_year = current_year + 1

            return {
                "step": WorkflowStep.YEAR_SELECTION.value,
                "message": f"Informations confirmées!\n\n"
                        f"Nous proposons l'année d'inscription: {current_year}-{next_year}\n"
                        f"Frais d'inscription: {self.fixed_fee} FCFA\n\n"
                        "Confirmez-vous cette année d'inscription?\n1. Oui, continuer\n2. Non, changer d'année",
                "options": ["1", "2", "oui", "non"]
            }

        elif user_input in ["2", "non", "no"]:
            # Rediriger vers intervention humaine
            workflow["current_step"] = WorkflowStep.PENDING_HUMAN

            return {
                "step": WorkflowStep.PENDING_HUMAN.value,
                "message": "Un agent humain va vous contacter pour corriger les informations.",
                "options": None
            }

        else:
            return {
                "step": WorkflowStep.CONFIRM_DATA.value,
                "message": "Veuillez répondre par 'oui' ou 'non':",
                "options": ["1", "2", "oui", "non"]
            }

    async def _handle_year_selection(self, workflow: Dict, user_input: str) -> Dict[str, Any]:
        """
        Gérer la sélection de l'année d'inscription.
        """
        user_input = user_input.strip().lower()

        if user_input in ["1", "oui", "yes", "ok"]:
            # Année confirmée
            current_year = datetime.now().year
            workflow["data"]["annee_inscription"] = f"{current_year}-{current_year + 1}"
            workflow["current_step"] = WorkflowStep.PAYMENT_PROOF

            return {
                "step": WorkflowStep.PAYMENT_PROOF.value,
                "message": f"Année d'inscription confirmée: {workflow['data']['annee_inscription']}\n\n"
                        f"Frais d'inscription: {self.fixed_fee} FCFA\n\n"
                        "Veuillez fournir la preuve de paiement:\n"
                        "1. Envoyer une image du reçu de paiement\n"
                        "2. Envoyer le numéro de référence de transaction",
                "options": None
            }

        elif user_input in ["2", "non", "no"]:
            # Mettre en pending
            workflow["current_step"] = WorkflowStep.PENDING_HUMAN

            return {
                "step": WorkflowStep.PENDING_HUMAN.value,
                "message": "Un agent humain va vous contacter pour discuter de l'année d'inscription.",
                "options": None
            }

        else:
            return {
                "step": WorkflowStep.YEAR_SELECTION.value,
                "message": "Veuillez répondre par 'oui' ou 'non':",
                "options": ["1", "2", "oui", "non"]
            }

    async def _handle_payment_proof(self, workflow: Dict, file_data: bytes, filename: str, user_input: str) -> Dict[str, Any]:
        """
        Gérer la preuve de paiement.
        """
        try:
            if file_data:
                # Preuve de paiement par image
                temp_doc = await self.document_service.upload_document(
                    file_data=file_data,
                    filename=filename,
                    inscription_id="temp_" + workflow["user_id"],
                    document_type="preuve_paiement",
                    user_id=workflow["user_id"]
                )

                workflow["data"]["payment_document_id"] = temp_doc.id
                workflow["current_step"] = WorkflowStep.TREASURER_VALIDATION

                # Créer l'inscription en attente de validation
                await self._create_pending_enrollment(workflow)

                return {
                    "step": WorkflowStep.TREASURER_VALIDATION.value,
                    "message": f"Preuve de paiement reçue ({filename}).\n\n"
                            f"Votre inscription est maintenant en attente de validation par le trésorier.\n"
                            f"Numéro d'inscription: {workflow['data']['pending_enrollment_id']}\n\n"
                            "Vous recevrez une confirmation dès que le paiement sera validé.",
                    "options": None
                }

            else:
                # Preuve de paiement par texte (numéro de référence)
                ref_number = user_input.strip()
                if ref_number:
                    workflow["data"]["payment_reference"] = ref_number
                    workflow["current_step"] = WorkflowStep.TREASURER_VALIDATION

                    # Créer l'inscription en attente de validation
                    await self._create_pending_enrollment(workflow)

                    return {
                        "step": WorkflowStep.TREASURER_VALIDATION.value,
                        "message": f"Référence de paiement enregistrée: {ref_number}\n\n"
                                f"Votre inscription est en attente de validation par le trésorier.\n"
                                f"Numéro d'inscription: {workflow['data']['pending_enrollment_id']}\n\n"
                                "Vous recevrez une confirmation dès que le paiement sera validé.",
                        "options": None
                    }
                else:
                    return {
                        "step": WorkflowStep.PAYMENT_PROOF.value,
                        "message": "Veuillez fournir une preuve de paiement (image ou numéro de référence):",
                        "options": None
                    }

        except Exception as e:
            logger.error(f"Payment proof handling failed: {e}")
            workflow["current_step"] = WorkflowStep.PENDING_HUMAN

            return {
                "step": WorkflowStep.PENDING_HUMAN.value,
                "message": "Une erreur s'est produite. Un agent humain va vous aider.",
                "options": None
            }

    async def _create_pending_enrollment(self, workflow: Dict):
        """
        Créer une inscription en attente de validation.
        """
        try:
            from ...models.enrollment import InscriptionCreate
            from ...models.base import DatabaseModel

            # Préparer les données d'inscription
            enrollment_data = InscriptionCreate(
                nom_enfant=workflow["data"]["child_info"]["nom"],
                prenom_enfant=workflow["data"]["child_info"]["prenom"],
                date_naissance=self._parse_french_date(workflow["data"]["child_info"]["date_naissance"]),
                lieu_naissance=workflow["data"]["child_info"]["lieu_naissance"],
                annee_catechetique=workflow["data"]["annee_inscription"],
                niveau=workflow["data"]["selected_class"]["Nom"],
                montant_total=self.fixed_fee
            )

            # Créer l'inscription
            enrollment = await self.enrollment_service.create_enrollment(
                enrollment_data=enrollment_data,
                user_id=workflow["user_id"]
            )

            # Mettre à jour le statut en attente de validation
            await self.enrollment_service.transition_status(
                inscription_id=enrollment.id,
                new_status=InscriptionStatut.EN_ATTENTE_PAIEMENT,
                user_id="system-workflow"
            )

            workflow["data"]["pending_enrollment_id"] = enrollment.id
            workflow["data"]["pending_numero_unique"] = enrollment.numero_unique

        except Exception as e:
            logger.error(f"Failed to create pending enrollment: {e}")
            raise

    async def _find_legacy_parent(self, telephone: str) -> Optional[Dict]:
        """
        Chercher un parent dans le système legacy.
        """
        try:
            # Nettoyer le numéro de téléphone
            clean_phone = telephone.replace(' ', '').replace('-', '').replace('+', '')

            # Chercher dans plusieurs formats
            query = "SELECT * FROM parents_2 WHERE T_l_phone = ? OR T_l_phone = ? OR T_l_phone_2 = ? OR T_l_phone_2 = ?"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (telephone, clean_phone, telephone, clean_phone))
                row = await cursor.fetchone()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Failed to find legacy parent: {e}")
            return None

    async def _get_legacy_catechumenes(self, code_parent: str) -> List[Dict]:
        """
        Obtenir les catéchumènes d'un parent legacy.
        """
        try:
            query = "SELECT * FROM catechumenes_2 WHERE Code_Parent = ? ORDER BY Nom, Prenoms"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (code_parent,))
                rows = await cursor.fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get legacy catechumenes: {e}")
            return []

    async def _get_predefined_class(self, catechumene: Dict) -> Optional[Dict]:
        """
        Obtenir la classe prédéfinie pour un catéchumène.
        """
        try:
            # Logique à implémenter selon les règles de la paroisse
            # Pour l'instant, retourne la classe par défaut selon l'âge
            birth_year = int(catechumene.get('Ann_e_de_naissance', '2000'))
            age = date.today().year - birth_year

            classes = await self._get_classes_for_age(age)
            return classes[0] if classes else None

        except Exception as e:
            logger.error(f"Failed to get predefined class: {e}")
            return None

    async def _generate_step_message(self, workflow: Dict) -> str:
        """
        Générer le message pour l'étape actuelle.
        """
        return "Bienvenue! Choisissez le type d'inscription:\n1. Réinscription (élève déjà inscrit)\n2. Nouvelle inscription"

    async def _get_step_options(self, workflow: Dict) -> List[str]:
        """
        Obtenir les options pour l'étape actuelle.
        """
        return ["1", "2", "réinscription", "nouvelle"]

    def get_workflow_status(self, user_id: str) -> Optional[Dict]:
        """
        Obtenir le statut actuel du workflow.
        """
        return self.workflows.get(user_id)


# Service instance
_enrollment_workflow_service_instance: Optional[EnrollmentWorkflowService] = None


def get_enrollment_workflow_service() -> EnrollmentWorkflowService:
    """Obtenir l'instance du service de workflow."""
    global _enrollment_workflow_service_instance
    if _enrollment_workflow_service_instance is None:
        _enrollment_workflow_service_instance = EnrollmentWorkflowService()
    return _enrollment_workflow_service_instance