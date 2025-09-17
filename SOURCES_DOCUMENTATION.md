# Documentation des Sources de Données SDB

## Aperçu
Ce document décrit les différentes sources de données disponibles pour le Service Diocésain de la Catéchèse (SDB) et les méthodes pour y accéder.

## 1. Base de Données Baserow

### Configuration
- **URL :** https://sdbaserow.3xperts.tech
- **Authentification :** Token d'API
- **Fichier .env :** Contient BASEROW_URL et BASEROW_AUTH_KEY

### Tables Principales

#### Catechumenes (Table ID: 575)
**Champs :**
- ID Catechumene (UUID)
- Prenoms (Texte)
- Nom (Texte)
- Baptisee (Booléen)
- Extrait De Bapteme Fourni (Booléen)
- LieuBapteme (Texte)
- Annee de naissance (Date)
- Attestation De Transfert Fournie (Booléen)
- Code Parent (Texte)
- operateur (Email)

**Endpoint API :**
```
GET https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user_field_names=true
```

#### Inscriptions (Table ID: 574)
**Champs :**
- ID Inscription (UUID)
- ID Catechumene (UUID)
- Prenoms (Texte)
- Nom (Texte)
- AnneePrecedente (Texte)
- ParoisseAnneePrecedente (Texte)
- ClasseCourante (Texte)
- Montant (Nombre)
- Paye (Nombre)
- DateInscription (Date)
- Annee Inscription (Texte)
- Resultat Final (Texte)
- Note Finale (Nombre)
- Etat (Texte)

**Endpoint API :**
```
GET https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user_field_names=true
```

#### Parents (Table ID: 572)
**Champs :**
- Téléphone (Texte)
- Prenoms (Texte)
- Actif (Booléen)
- Code Parent (Texte)
- Nom (Texte)
- Email (Texte)

**Endpoint API :**
```
GET https://sdbaserow.3xperts.tech/api/database/rows/table/572/?user_field_names=true
```

#### Notes (Table ID: 576)
- Table pour les notes des élèves
- Structure à vérifier (peut être vide)

#### Classes (Table ID: 577)
- Informations sur les classes
- Niveaux : CP, CI, CE1, CE2, CM1, CM2, 5ème, 6ème

### Méthodes de Requête

#### Recherche par Nom
```bash
source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
"https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user_field_names=true&search=Nom"
```

#### Recherche par ID
```bash
source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
"https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user_field_names=true&search=ID_Catechumene"
```

## 2. Rclone Drive (Google Drive)

### Configuration
- **Nom du remote :** sdb
- **Type :** Google Drive
- **Commande de base :** `rclone [commande] sdb:[chemin]`

### Structure des Dossiers

#### Dossier Principal
- `Annee 2024-2025/` - Documents année en cours
- `GESTION CATE APP/` - Application de gestion
- `Gestion Catechese DB/` - Base de données
- `Communions 2021/` - Archives
- `Confirmations 2021/` - Archives

#### Sous-dossiers Importants
- `Annee 2024-2025/Trimestre 1/` - Documents T1
- `Annee 2024-2025/Trimestre 2/` - Documents T2
- `GESTION CATE APP/S_IMPRESSIONS/Partage/` - Carnets générés
- `GESTION CATE APP/S_TEMPLATES/` - Modèles de documents

### Types de Fichiers

#### Extraits de Baptême (EB)
- Format : PDF, JPG, JPEG, PNG
- Nom convention : `EB - Nom Prénom.ext`
- Emplacement : `Annee 2024-2025/`

#### Attestations de Catéchèse
- Format : PDF
- Nom convention : `attestation_catechese Nom Prénom.pdf`
- Emplacement : `Annee 2024-2025/`

#### Carnets de Catéchisme
- Format : PDF
- Nom convention : `CARNET-Niveau_Nom Prénom.pdf`
- Emplacement : `GESTION CATE APP/S_IMPRESSIONS/Partage/`

### Méthodes de Requête

#### Recherche par Nom
```bash
rclone ls sdb: --include "*Nom*" --include "*.pdf" --include "*.jpg"
```

#### Recherche par Type de Document
```bash
rclone ls sdb: --include "EB *" --include "attestation*"
```

#### Téléchargement de Fichier
```bash
rclone copy sdb:"chemin/du/fichier.pdf" ./
```

## 3. Fichiers Locaux

### Fichiers de Configuration
- `.env` - Variables d'environnement
- `SOURCES_DOCUMENTATION.md` - Ce document

### Scripts Utiles
- `setup_rclone_gdrive.sh` - Configuration rclone
- `backup_to_gdrive.sh` - Script de sauvegarde
- `rsync_backup.sh` - Script rsync

## 4. Workflows Courants

### Recherche d'Information d'un Élève

1. **Recherche dans Baserow :**
   ```bash
   # Chercher dans Catechumenes
   source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
   "https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user_field_names=true&search=Nom"
   ```

2. **Récupérer les inscriptions :**
   ```bash
   source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
   "https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user_field_names=true&search=ID_Catechumene"
   ```

3. **Chercher les documents associés :**
   ```bash
   rclone ls sdb: --include "*Nom*" --include "*.pdf" --include "*.jpg"
   ```

4. **Récupérer les informations du parent :**
   ```bash
   source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
   "https://sdbaserow.3xperts.tech/api/database/rows/table/572/?user_field_names=true&search=CodeParent"
   ```

### Génération d'Attestation

1. Collecter toutes les informations de l'élève
2. Vérifier les notes et résultats
3. Confirmer le statut de baptême
4. Rédiger l'attestation avec toutes les informations
5. Signer et dater le document

### Recherche d'Extraits de Baptême

1. **Recherche par nom :**
   ```bash
   rclone ls sdb: --include "*Nom*" --include "EB *"
   ```

2. **Recherche par type :**
   ```bash
   rclone ls sdb: --include "EB *" --include "*.pdf" --include "*.jpg"
   ```

## 5. Bonnes Pratiques

### Sécurité
- Ne jamais exposer les tokens d'API
- Utiliser le fichier `.env` pour les credentials
- Limiter les permissions des tokens

### Performance
- Utiliser les filtres de recherche quand c'est possible
- Éviter de télécharger des fichiers inutilement
- Privilégier les requêtes spécifiques

### Organisation
- Suivre les conventions de nommage
- Maintenir la documentation à jour
- Archiver correctement les anciennes données

## 6. Dépannage

### Problèmes Communs
- **Token invalide :** Vérifier le fichier .env
- **Fichier introuvable :** Vérifier le chemin exact
- **Permissions insuffisantes :** Vérifier les droits d'accès

### Ressources
- Documentation Baserow API
- Documentation rclone
- Support technique SDC

---
*Dernière mise à jour : $(date)*
*Version : 1.0*