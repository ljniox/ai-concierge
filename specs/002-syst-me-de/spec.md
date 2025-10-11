# Feature Specification: Système de Gestion de Profils et Inscriptions avec SQLite

**Feature Branch**: `002-syst-me-de`
**Created**: 2025-10-11
**Status**: Clarified - Ready for Planning
**Input**: User description: "Système de gestion de profils avec base SQLite et inscriptions multi-documents avec OCR pour la catéchèse SDB"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inscription Parent avec Documents et OCR (Priority: P1) 🎯 MVP

Un parent souhaite inscrire ou réinscrire son enfant à la catéchèse. Le parent accède au système via WhatsApp ou Telegram, remplit le formulaire d'inscription, télécharge les documents requis (extrait de naissance, extrait de baptême, attestation de transfert si applicable). Le système extrait automatiquement les informations des documents via OCR, les présente au parent pour validation, puis enregistre l'inscription en attente de paiement.

**Why this priority**: Cette fonctionnalité est le cœur du système car elle répond au besoin immédiat exprimé par l'utilisateur. Sans inscription, aucune autre fonctionnalité de gestion ne peut fonctionner. Elle réduit le travail manuel des secrétaires et améliore l'expérience parent.

**Independent Test**: Peut être testée en créant une inscription complète depuis l'upload des documents jusqu'à la validation des informations extraites par OCR. Démontre de la valeur immédiate en automatisant la saisie des données d'inscription.

**Acceptance Scenarios**:

1. **Given** un parent connecté au système, **When** il démarre une nouvelle inscription, **Then** le système lui présente un formulaire guidé demandant les informations de base de l'enfant
2. **Given** le formulaire de base complété, **When** le parent upload l'extrait de naissance (PDF ou image), **Then** le système extrait automatiquement le nom, prénom, date de naissance, lieu de naissance via OCR
3. **Given** les informations extraites affichées, **When** le parent valide ou corrige les données, **Then** le système enregistre les informations validées
4. **Given** l'extrait de naissance validé, **When** le parent upload l'extrait de baptême, **Then** le système extrait la date de baptême, lieu de baptême, paroisse et présente pour validation
5. **Given** une réinscription (enfant déjà dans le système), **When** le parent sélectionne "réinscription", **Then** le système pré-remplit les données existantes et demande uniquement les mises à jour
6. **Given** un transfert d'une autre paroisse, **When** le parent upload l'attestation de transfert, **Then** le système extrait la paroisse d'origine et l'année de catéchèse précédente
7. **Given** tous les documents validés, **When** le parent finalise l'inscription, **Then** le système génère un numéro d'inscription unique et passe au statut "En attente de paiement"

---

### User Story 2 - Gestion des Paiements avec Validation (Priority: P1) 🎯 MVP

Un parent finalise son inscription en effectuant le paiement des frais de scolarité. Le parent peut payer en cash (à la permanence), par Mobile Money, ou présenter un reçu papier pré-établi. Pour Mobile Money, le parent télécharge une capture d'écran du paiement comme preuve. La trésorière reçoit une notification, vérifie le paiement dans son système Mobile Money ou sa caisse, puis valide l'entrée dans le système pour activer l'inscription.

**Why this priority**: Le paiement est indissociable de l'inscription - une inscription sans paiement validé reste inactive. Cette story complète le parcours MVP parent et apporte de la valeur immédiate à la trésorière en centralisant la gestion des paiements.

**Independent Test**: Peut être testée indépendamment en créant une inscription "En attente de paiement", en soumettant une preuve de paiement, et en validant le workflow de vérification de la trésorière jusqu'à l'activation de l'inscription.

**Acceptance Scenarios**:

1. **Given** une inscription en attente de paiement, **When** le parent sélectionne "Payer en cash", **Then** le système génère un QR code ou référence pour présentation à la permanence
2. **Given** le parent à la permanence avec le QR code, **When** le sacristain ou secrétaire encaisse le paiement, **Then** le système enregistre l'entrée de caisse avec le montant, mode de paiement, et émetteur
3. **Given** un paiement Mobile Money effectué, **When** le parent upload la capture d'écran de la transaction, **Then** le système enregistre la preuve avec statut "En attente de validation trésorière"
4. **Given** une preuve de paiement soumise, **When** la trésorière consulte les paiements en attente, **Then** elle voit la liste avec nom parent, montant, capture d'écran, et référence Mobile Money
5. **Given** la trésorière vérifie le paiement dans son compte Mobile Money, **When** elle valide le paiement dans le système, **Then** l'inscription passe au statut "Active" et le parent reçoit une confirmation
6. **Given** un reçu papier pré-établi, **When** le parent fournit le numéro de reçu, **Then** la secrétaire saisit le numéro de reçu et valide l'inscription
7. **Given** un paiement rejeté (montant incorrect, transaction introuvable), **When** la trésorière rejette le paiement, **Then** le parent reçoit une notification avec raison du rejet et instructions pour correction

---

### User Story 3 - Système de Profils et Permissions de Base (Priority: P2)

Le système gère différents profils utilisateurs avec des permissions spécifiques pour la gestion de la catéchèse. Un Super Admin peut créer et gérer tous les profils. Chaque profil (Sacristain, Curé, Secrétaires, Président, Trésoriers, Catéchistes, Parents) a des permissions définies pour accéder aux fonctionnalités appropriées.

**Why this priority**: Les profils sont nécessaires pour sécuriser les fonctionnalités P1 (inscriptions et paiements). Cette story peut être développée en parallèle de P1 puis intégrée, car les tests initiaux peuvent utiliser un profil "admin" générique.

**Independent Test**: Peut être testée en créant différents profils, en leur assignant des permissions, puis en vérifiant que chaque profil accède uniquement aux fonctionnalités autorisées. Démontre la sécurité et la séparation des responsabilités.

**Acceptance Scenarios**:

1. **Given** un Super Admin connecté, **When** il crée un nouveau profil "Trésorier", **Then** le système assigne automatiquement les permissions: voir paiements, valider paiements, voir rapports caisse
2. **Given** un profil Sacristain créé, **When** le sacristain se connecte, **Then** il peut uniquement: créer inscriptions, voir inscriptions, voir informations publiques
3. **Given** un profil Parent créé, **When** le parent se connecte, **Then** il peut uniquement: voir ses inscriptions, payer inscriptions, voir notes de ses enfants, envoyer messages
4. **Given** un profil Curé créé, **When** le curé se connecte, **Then** il a accès à toutes les informations en lecture et modification selon les modules disponibles
5. **Given** un profil Catéchiste créé, **When** le catéchiste se connecte, **Then** il peut voir la liste des élèves de sa classe assignée et rechercher un enfant
6. **Given** un utilisateur non autorisé, **When** il tente d'accéder à une fonctionnalité hors de ses permissions, **Then** le système refuse l'accès et enregistre la tentative dans les logs de sécurité
7. **Given** un changement de rôle, **When** le Super Admin modifie le profil d'un utilisateur, **Then** les nouvelles permissions prennent effet immédiatement

---

### User Story 4 - Infrastructure SQLite Multi-Applications (Priority: P2)

Le système migre du stockage Supabase unique vers une architecture SQLite multi-fichiers où chaque application (Catéchèse, Pages Temporaires, System) a sa propre base de données. Les données de catéchèse (catéchumènes, parents, notes) restent dans Baserow. Les données applicatives (profils, inscriptions en cours, sessions) sont dans SQLite catéchèse. Les pages temporaires et codes d'accès sont dans SQLite system.

**Why this priority**: Cette architecture permet l'ajout futur d'autres applications SDB (gestion paroissiale, comptabilité, événements) sans conflit de données. Elle doit être en place avant d'ajouter trop de fonctionnalités pour éviter une migration complexe.

**Independent Test**: Peut être testée en créant des données dans chaque base SQLite, en vérifiant l'isolation, puis en ajoutant une nouvelle "application test" avec sa propre base sans impact sur les existantes.

**Acceptance Scenarios**:

1. **Given** le système initialisé, **When** l'application démarre, **Then** trois fichiers SQLite sont créés: `catechese_app.db`, `temp_pages_system.db`, `core_system.db`
2. **Given** une inscription créée, **When** les données sont enregistrées, **Then** les informations de profil parent vont dans `catechese_app.db` et les codes temporaires dans `temp_pages_system.db`
3. **Given** une page temporaire générée pour collecte de documents, **When** un parent accède via lien unique, **Then** le système vérifie le code dans `temp_pages_system.db` et récupère les infos parent depuis `catechese_app.db`
4. **Given** un nouvel admin souhaitant ajouter une application "Gestion Paroissiale", **When** il initialise le nouveau module, **Then** un fichier `paroisse_app.db` est créé sans toucher aux bases existantes
5. **Given** des données catéchèse dans Baserow, **When** le système a besoin de données élève, **Then** il requête Baserow directement (pas de duplication dans SQLite)
6. **Given** une sauvegarde requise, **When** l'admin lance la sauvegarde, **Then** chaque fichier SQLite est sauvegardé séparément avec horodatage
7. **Given** une restauration de données, **When** l'admin restaure une sauvegarde, **Then** il peut choisir de restaurer uniquement une application spécifique sans affecter les autres

---

### User Story 5 - Consultation Catéchiste (Priority: P3)

Un catéchiste se connecte pour voir la liste de ses élèves assignés. Le catéchiste peut rechercher un enfant spécifique, voir les informations de contact des parents, et marquer les présences/absences.

**Why this priority**: Fonctionnalité utile mais pas critique pour le MVP. Peut être ajoutée après que le système d'inscription et de paiement soit opérationnel.

**Independent Test**: Peut être testée en assignant une classe à un catéchiste, puis en vérifiant qu'il voit uniquement ses élèves et peut effectuer les recherches et marquages de présence.

**Acceptance Scenarios**:

1. **Given** un catéchiste avec classe assignée, **When** il accède à "Ma classe", **Then** il voit la liste complète des élèves avec nom, âge, statut inscription
2. **Given** la liste des élèves affichée, **When** le catéchiste recherche par nom, **Then** le système filtre la liste en temps réel
3. **Given** un élève sélectionné, **When** le catéchiste consulte le détail, **Then** il voit nom parent, téléphone parent, date de naissance élève, année de catéchisme
4. **Given** une session de catéchisme en cours, **When** le catéchiste marque les présences, **Then** le système enregistre l'horodatage et le statut (présent/absent/retard) pour chaque élève

---

### User Story 6 - Modules de Gestion Avancés (Priority: P4 - Future)

Le système offre des modules de gestion avancés: gestion des notes (trimestre, examens), gestion des événements (messes, retraites, sorties), gestion de caisse (entrées/sorties, rapports), suivi des actions (logs auditables), génération de rapports (statistiques, finances, présences).

**Why this priority**: Fonctionnalités importantes à long terme mais non critiques pour le lancement initial. Peuvent être développées itérativement après validation du MVP.

**Independent Test**: Chaque module peut être testé indépendamment après le déploiement du MVP.

**Acceptance Scenarios**:

1. **Given** un système opérationnel avec inscriptions actives, **When** un nouveau module est activé, **Then** il s'intègre sans perturber les modules existants
2. **Given** le module Notes activé, **When** un catéchiste saisit les notes de trimestre, **Then** les parents peuvent consulter les notes de leurs enfants
3. **Given** le module Événements activé, **When** le secrétaire crée un événement, **Then** les parents reçoivent une notification et peuvent confirmer la participation
4. **Given** le module Caisse activé, **When** la trésorière enregistre une sortie, **Then** le système met à jour le solde et génère une ligne de rapport
5. **Given** le module Rapports activé, **When** le président génère un rapport annuel, **Then** le système agrège données d'inscriptions, présences, finances avec visualisations

---

### Edge Cases

- Que se passe-t-il si l'OCR échoue à extraire des informations d'un document de mauvaise qualité?
  - Le système permet la saisie manuelle complète et signale l'échec OCR dans les logs

- Comment le système gère-t-il un document dans une langue non supportée (arabe, anglais)?
  - Le système détecte la langue, alerte l'utilisateur, et active le mode saisie manuelle obligatoire

- Que se passe-t-il si un parent upload le mauvais type de document (photo d'identité au lieu d'extrait de naissance)?
  - Le système détecte le type de document via OCR, signale l'erreur, et demande le bon document

- Comment gérer un paiement Mobile Money jamais reçu par la trésorière?
  - La trésorière peut rejeter le paiement avec motif "Transaction introuvable", le parent est notifié pour vérifier et re-soumettre

- Que se passe-t-il si deux parents tentent d'inscrire le même enfant simultanément?
  - Le système détecte la duplication via nom+date de naissance, alerte le second parent, et propose de rattacher au compte existant

- Comment gérer une inscription initiée sur WhatsApp puis poursuivie sur Telegram?
  - Le système identifie le parent via numéro de téléphone ou code unique et synchronise la session entre canaux

- Que se passe-t-il si un catéchiste quitte et sa classe doit être réassignée?
  - Le Super Admin peut réassigner la classe entière à un nouveau catéchiste en une opération, les élèves sont notifiés du changement

- Comment gérer un paiement partiel (parent paie 50% immédiatement)?
  - Le système enregistre le montant partiel, met l'inscription en statut "Paiement partiel", et génère un solde restant dû avec échéance

## Requirements *(mandatory)*

### Functional Requirements

#### Gestion des Inscriptions

- **FR-001**: System MUST permettre aux parents d'initier une inscription via WhatsApp ou Telegram avec un formulaire guidé étape par étape
- **FR-002**: System MUST accepter les formats de documents suivants: PDF, JPG, PNG, HEIC avec taille maximale de 10 MB par fichier
- **FR-003**: System MUST extraire automatiquement via OCR les informations des extraits de naissance (nom, prénom, date, lieu de naissance)
- **FR-004**: System MUST extraire automatiquement via OCR les informations des extraits de baptême (date baptême, paroisse, nom prêtre)
- **FR-005**: System MUST extraire automatiquement via OCR les informations des attestations de transfert (paroisse origine, année catéchisme précédente)
- **FR-006**: System MUST présenter les informations extraites par OCR au parent pour validation ou correction avant enregistrement
- **FR-007**: System MUST générer un numéro d'inscription unique au format "CAT-2025-XXXX" où XXXX est un séquentiel
- **FR-008**: System MUST permettre la réinscription en pré-remplissant les données existantes de l'enfant depuis Baserow
- **FR-009**: System MUST détecter les doublons d'inscription via combinaison nom+prénom+date de naissance
- **FR-010**: System MUST enregistrer chaque document uploadé avec métadonnées (type document, date upload, statut OCR, validation parent)

#### Gestion des Paiements

- **FR-011**: System MUST supporter trois modes de paiement: Cash (permanence), Mobile Money (Orange Money, Wave, Free Money), Reçu papier pré-établi
- **FR-012**: System MUST permettre au parent d'uploader une capture d'écran du paiement Mobile Money comme preuve
- **FR-013**: System MUST notifier la trésorière en temps réel de chaque nouveau paiement soumis
- **FR-014**: System MUST permettre à la trésorière de voir une file d'attente de paiements à valider avec filtres par date, mode de paiement, statut
- **FR-015**: System MUST permettre à la trésorière de valider un paiement (activation inscription) ou rejeter (notification parent avec raison)
- **FR-016**: System MUST enregistrer chaque entrée de caisse avec: montant, mode paiement, émetteur, date/heure, validateur
- **FR-017**: System MUST générer un QR code ou référence unique pour les paiements cash à présenter à la permanence
- **FR-018**: System MUST supporter les paiements partiels avec calcul automatique du solde restant dû
- **FR-019**: System MUST envoyer une confirmation au parent après validation du paiement avec résumé inscription
- **FR-020**: System MUST permettre au sacristain/secrétaire d'enregistrer un paiement cash reçu en permanence

#### Système de Profils et Permissions

- **FR-021**: System MUST supporter un profil Super Admin avec accès complet à toutes les fonctionnalités et gestion des profils
- **FR-022**: System MUST supporter les profils suivants pour la catéchèse: Sacristain, Curé, Secrétaire du Curé, Président Bureau, Secrétaire Bureau, Secrétaire Adjoint Bureau, Trésorier Bureau, Trésorier Adjoint Bureau, Responsable Organisation Bureau, Chargé Relations Extérieures Bureau, Chargé Relations Extérieures Adjoint Bureau, Catéchiste, Parent
- **FR-023**: Sacristain MUST avoir les permissions: créer inscriptions, voir inscriptions, voir informations publiques
- **FR-024**: Secrétaire du Curé MUST avoir les mêmes permissions que Sacristain plus saisie numéro reçu papier
- **FR-025**: Parent MUST avoir les permissions: voir inscriptions de ses enfants, soumettre paiements, voir notes de ses enfants, demander informations
- **FR-026**: Curé MUST avoir accès lecture/modification à toutes les informations selon modules disponibles
- **FR-027**: Président Bureau, Secrétaire Général, Secrétaire Général Adjoint MUST avoir les mêmes permissions que Curé
- **FR-028**: Trésorier/Trésorier Adjoint MUST avoir les permissions: voir tous paiements, valider paiements, voir/générer rapports caisse, enregistrer entrées/sorties caisse
- **FR-029**: Catéchiste MUST avoir les permissions: voir liste élèves de sa classe, rechercher élève, voir coordonnées parents, marquer présences/absences
- **FR-030**: System MUST logger toutes les tentatives d'accès non autorisées avec horodatage, utilisateur, action tentée
- **FR-031**: System MUST permettre au Super Admin de modifier les permissions d'un profil avec effet immédiat
- **FR-032**: System MUST permettre l'authentification des parents via WhatsApp/Telegram verified account (numéro de téléphone vérifié par la plateforme) OU via code parent (depuis Baserow) pour les numéros de téléphone non présents en base de données

#### Infrastructure SQLite Multi-Applications

- **FR-033**: System MUST créer trois bases de données SQLite séparées: `catechese_app.db` (données inscriptions/profils/paiements), `temp_pages_system.db` (codes temporaires/UID), `core_system.db` (configuration système)
- **FR-034**: System MUST isoler les données de chaque application dans son fichier SQLite respectif sans cross-contamination
- **FR-035**: System MUST permettre l'ajout de nouvelles applications avec création automatique d'un nouveau fichier SQLite `{app_name}_app.db`
- **FR-036**: System MUST continuer à utiliser Baserow pour les données catéchèse (Catéchumènes table 575, Inscriptions table 574, Parents table 572, Notes table 576, Classes table 577)
- **FR-037**: System MUST synchroniser les données parent entre SQLite (inscriptions en cours) et Baserow (données officielles) une fois inscription validée
- **FR-038**: System MUST générer des sauvegardes automatiques de chaque fichier SQLite avec horodatage et rotation (conserver 30 derniers jours)
- **FR-039**: System MUST permettre la restauration sélective d'une base applicative sans affecter les autres
- **FR-040**: System MUST assurer l'intégrité référentielle entre bases SQLite via identifiants communs (user_id, inscription_id)

#### Pages Temporaires et Collecte de Données

- **FR-041**: System MUST générer des pages web temporaires avec URL unique et code d'accès à usage unique pour collecte de documents
- **FR-042**: System MUST enregistrer dans `temp_pages_system.db` les métadonnées: code, URL, date création, date expiration, utilisateur associé, statut
- **FR-043**: System MUST expirer automatiquement les pages temporaires après 7 jours ou après première utilisation (configurable)
- **FR-044**: System MUST permettre au parent d'uploader plusieurs documents sur une page temporaire en une session
- **FR-045**: System MUST notifier le créateur de la page (secrétaire/sacristain) lorsque le parent a soumis les documents

#### Consultation et Recherche

- **FR-046**: Catéchiste MUST pouvoir rechercher un élève par nom, prénom, ou numéro inscription dans toute la base
- **FR-047**: System MUST retourner les résultats de recherche avec surlignage des termes recherchés et tri par pertinence
- **FR-048**: Catéchiste MUST voir uniquement les élèves de sa classe assignée par défaut avec option "rechercher dans toute l'école" si autorisé
- **FR-049**: Parent MUST pouvoir consulter l'historique complet des inscriptions de ses enfants (années précédentes, paiements, notes)
- **FR-050**: System MUST permettre au Curé/Président de générer des listes d'élèves avec filtres: année catéchisme, classe, statut paiement, paroisse origine

#### Traçabilité et Logs

- **FR-051**: System MUST enregistrer toutes les actions utilisateur dans une table `action_logs` avec: user_id, action_type, entity_type, entity_id, timestamp, details (JSON)
- **FR-052**: System MUST enregistrer les actions suivantes: création inscription, modification inscription, upload document, validation OCR, soumission paiement, validation paiement, rejet paiement, modification profil, accès données sensibles
- **FR-053**: System MUST permettre au Super Admin de consulter les logs avec filtres: date, utilisateur, type d'action, entité concernée
- **FR-054**: System MUST conserver les logs pendant 2 ans minimum pour conformité audit
- **FR-055**: System MUST anonymiser les logs après 2 ans (remplacer identifiants par hash) tout en conservant les statistiques agrégées

#### Intégration Mobile Money

- **FR-056**: System MUST supporter les opérateurs Mobile Money suivants: Orange Money, Wave, Free Money (opérateurs actuellement utilisés, pas d'ajout MTN ou Moov pour le MVP)
- **FR-057**: System MUST extraire automatiquement via OCR les informations de la capture paiement: numéro transaction, montant, date/heure, opérateur
- **FR-058**: System MUST utiliser une approche hybride: OCR extrait automatiquement les informations du paiement (référence, montant, opérateur) depuis la capture d'écran, puis la trésorière valide manuellement en comparant avec son compte Mobile Money (informations pré-remplies pour accélérer la validation)
- **FR-059**: System MUST afficher à la trésorière lors de la validation: capture soumise par parent, informations OCR extraites, montant attendu, écart éventuel

### Key Entities

- **Inscription**: Représente une demande d'inscription d'un enfant pour une année catéchétique. Attributs: numéro unique, enfant (référence Baserow catéchumène_id), parent (référence SQLite user_id + Baserow parent_id), année catéchétique, statut (brouillon, en attente paiement, paiement partiel, active, annulée), montant total, montant payé, solde restant, documents associés, date création, date dernière modification, créateur, validateur.

- **Document**: Représente un document uploadé par un parent. Attributs: ID unique, inscription_id, type (extrait naissance, extrait baptême, attestation transfert, preuve paiement), fichier (chemin storage), format, taille, date upload, statut OCR (en attente, succès, échec, manuel), données extraites (JSON), données validées (JSON), validé par parent (boolean), date validation.

- **Paiement**: Représente un paiement effectué pour une inscription. Attributs: ID unique, inscription_id, montant, mode (cash, orange_money, wave, free_money, recu_papier), référence (numéro transaction, numéro reçu), preuve (document_id si capture), statut (en attente validation, validé, rejeté), date soumission, date validation, validateur_id, motif rejet, métadonnées (JSON avec infos opérateur, point vente, etc.).

- **Profil Utilisateur**: Représente un utilisateur du système. Attributs: user_id (UUID), nom, prénom, rôle (enum profils catéchèse), téléphone, email, canal_préféré (whatsapp, telegram), identifiant_canal (phone number, telegram_id), date création, actif (boolean), dernière connexion, permissions (JSON avec liste permissions spécifiques), metadata (JSON avec infos supplémentaires selon rôle).

- **Classe**: Représente une classe de catéchisme. Attributs: classe_id, année catéchétique, niveau (éveil, CE1, CE2, CM1, CM2, confirmation), catéchiste_id (référence user_id), catéchiste_adjoint_id, capacité maximale, effectif actuel, horaire, salle, statut (ouverte, fermée, suspendue).

- **Page Temporaire**: Représente une URL temporaire pour collecte de documents. Attributs: page_id (UUID), code d'accès (alphanumérique 8 caractères), URL complète, utilisateur_associé (user_id parent), créateur (user_id secrétaire), objet (enum: inscription, documents complémentaires, autre), date création, date expiration, date première utilisation, statut (active, utilisée, expirée, révoquée), documents collectés (array document_id).

- **Log Action**: Représente une action tracée dans le système. Attributs: log_id, user_id, action_type (enum), entity_type (inscription, paiement, document, profil), entity_id, timestamp, IP address, user_agent (canal WhatsApp/Telegram), details (JSON avec contexte action), statut (succès, échec), message erreur si échec.

- **Base de Données Application**: Représente une base SQLite pour une application. Attributs: app_name, db_filename, db_path, version schema, date création, date dernière migration, taille fichier, dernière sauvegarde, statut (active, maintenance, archived).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les parents peuvent compléter une inscription avec upload de 3 documents en moins de 10 minutes, de la connexion à la confirmation
- **SC-002**: Le taux d'extraction OCR réussie est supérieur à 85% pour les documents de bonne qualité (résolution >300 DPI, format standard)
- **SC-003**: Les validations de paiement par la trésorière sont complétées en moins de 2 minutes par transaction
- **SC-004**: Le système réduit le temps de traitement des inscriptions de 30 minutes (manuel) à 10 minutes (automatisé), soit une amélioration de 66%
- **SC-005**: Zéro perte de données lors de basculement entre bases SQLite applicatives (test avec 1000 inscriptions simultanées)
- **SC-006**: Les catéchistes trouvent un élève spécifique en moins de 30 secondes via la recherche
- **SC-007**: 95% des parents réussissent à soumettre leur preuve de paiement Mobile Money au premier essai sans assistance
- **SC-008**: Le système traite 100 inscriptions simultanées sans dégradation de performance (temps de réponse < 3 secondes)
- **SC-009**: Zéro accès non autorisé détecté dans les tests de sécurité des profils et permissions
- **SC-010**: Les pages temporaires permettent de collecter 100% des documents sans intervention manuelle de la secrétaire
- **SC-011**: Le taux de satisfaction parent atteint 90% mesuré par enquête post-inscription (facilité, rapidité, clarté)
- **SC-012**: La trésorière réduit son temps de réconciliation mensuelle de 8 heures à 2 heures grâce aux rapports automatisés
- **SC-013**: Réduction de 80% des erreurs de saisie des informations élèves grâce à l'OCR et validation parent
- **SC-014**: Le système supporte l'ajout d'une nouvelle application (ex: Gestion Paroissiale) en moins de 1 heure sans impact sur les applications existantes
- **SC-015**: Les logs d'audit permettent de tracer 100% des actions critiques (paiements, modifications données élèves) pour conformité GDPR

## Assumptions

- **Assumption 1**: Les parents ont accès à un smartphone avec appareil photo capable de prendre des photos de documents avec résolution minimale 2 MP
- **Assumption 2**: Les documents officiels (extraits de naissance, baptême) sont en langue française avec format standard sénégalais
- **Assumption 3**: Les opérateurs Mobile Money acceptés utilisent le format franc CFA (XOF) comme devise
- **Assumption 4**: La connexion internet est suffisante pour upload de fichiers jusqu'à 10 MB (3G minimum)
- **Assumption 5**: Les parents conservent leur numéro de téléphone d'une année à l'autre pour permettre la réinscription automatique
- **Assumption 6**: La trésorière a accès à ses comptes Mobile Money en temps réel pour vérification des transactions
- **Assumption 7**: Les reçus papier pré-établis ont un numéro unique séquentiel non réutilisable
- **Assumption 8**: Le système opère durant l'année scolaire sénégalaise (octobre à juin) avec pic d'inscriptions en septembre-octobre
- **Assumption 9**: Les catéchistes sont assignés à une seule classe principale mais peuvent consulter toute l'école si autorisés
- **Assumption 10**: Les données Baserow existantes sont la source de vérité pour les catéchumènes historiques (années précédentes)
