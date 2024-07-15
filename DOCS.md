### Documentation du Script de Surveillance de Répertoires et d'Appels API

---

## Technologie Utilisée

1. **Python** : Langage de programmation utilisé pour écrire le script.
2. **watchdog** : Bibliothèque Python utilisée pour surveiller les systèmes de fichiers et détecter les changements en temps réel.
3. **requests** : Bibliothèque Python pour effectuer des requêtes HTTP simples et envoyer les données à une API.
4. **dotenv** : Bibliothèque Python pour charger les variables d'environnement à partir d'un fichier `.env`.
5. **shutil** : Bibliothèque Python pour effectuer des opérations de copie et de suppression de fichiers.

---

## Les Composants

1. **Variables d'Environnement** :
    - **WATCHED_DIRS** : Liste des répertoires à surveiller, définie dans le fichier `.env`.
    - **TEMP_DIR** : Répertoire temporaire où les fichiers sont copiés avant traitement.
    - **API_URL** : URL de l'API à laquelle les données des fichiers sont envoyées.
    - **LAABS_AUTH** : Jeton d'authentification utilisé pour accéder à l'API.
    - **ARCHIVAL_PROFILE_REFERENCE** : Référence de profil d'archivage pour l'API.
    - **SERVICE_LEVEL_REFERENCE** : Référence de niveau de service pour l'API.
    - **RETENTION_RULE_CODE**, **DESCRIPTION_CLASS**, **FULL_TEXT_INDEXATION**, **DESCRIPTION_LEVEL** : Autres paramètres de métadonnées utilisés dans les requêtes API.

2. **Fonctions** :
    - `wait_for_file_availability(file_path, retries=5, delay=1)` : Attente de la disponibilité d'un fichier.
    - `copy_to_temp(file_path)` : Copie un fichier vers le répertoire temporaire.
    - `get_custom_file_name(file_path)` : Génère un nom de fichier personnalisé basé sur son répertoire et son nom d'origine.
    - `clean_temp_dir()` : Nettoie le répertoire temporaire en supprimant tous les fichiers.
    - `encode_file_to_base64(file_path)` : Encode le contenu du fichier en base64.
    - `get_mimetype(file_path)` : Détermine le type MIME d'un fichier.
    - `create_api_data(file_name)` : Crée les données pour la requête API.

3. **Classes** :
    - `Watcher` : Hérite de `FileSystemEventHandler` pour gérer les événements de création de fichiers et de répertoires.
        - `on_created(self, event)` : Gère les événements de création de fichiers ou de répertoires.
        - `process_new_directory(self, dir_path)` : Traite tous les fichiers dans un nouveau répertoire.
        - `process_file(self, file_path)` : Traite un fichier individuel.
        - `add_file_to_pending(self, file_path, encoded_content)` : Ajoute les données de fichier à la liste en attente.
        - `send_pending_files(self, file_name)` : Envoie les fichiers en attente à l'API.

---

## L'Architecture

1. **Surveillance de Répertoires** :
    - Le script utilise `watchdog` pour surveiller plusieurs répertoires spécifiés dans `WATCHED_DIRS`.
    - Pour chaque répertoire, un observateur est créé et attaché à un gestionnaire d'événements (`Watcher`).

2. **Traitement des Fichiers** :
    - Lorsqu'un fichier ou un répertoire est créé, l'événement est capturé par `Watcher`.
    - Les fichiers sont copiés dans un répertoire temporaire pour garantir leur disponibilité.
    - Le contenu des fichiers est encodé en base64 avant d'être préparé pour l'envoi à l'API.

3. **Envoi des Données à l'API** :
    - Les données encodées sont stockées dans une liste en attente.
    - Une fois la liste préparée, les données sont envoyées à l'API via une requête HTTP POST.
    - Les métadonnées et les autres informations nécessaires pour l'API sont incluses dans la requête.

---

## Le Flow

1. **Initialisation** :
    - Charger les variables d'environnement.
    - Créer le répertoire temporaire si nécessaire.

2. **Surveillance** :
    - Démarrer un observateur pour chaque répertoire spécifié.
    - Maintenir le programme en exécution avec une boucle infinie.

3. **Traitement des Événements** :
    - Sur la détection de la création d'un fichier :
        - Copier le fichier vers le répertoire temporaire.
        - Encoder le fichier en base64.
        - Ajouter les données encodées à la liste en attente.
        - Envoyer les données à l'API.

4. **Envoi à l'API** :
    - Préparer les données pour l'API.
    - Envoyer une requête POST à l'API avec les données encodées.
    - Nettoyer le répertoire temporaire après un envoi réussi.

5. **Interruption** :
    - Sur interruption manuelle (`Ctrl+C`), arrêter proprement tous les observateurs.

---

## L'Exploitation des Logs

1. **Logs de Disponibilité de Fichier** :
    - Logs indiquant les tentatives de vérification de la disponibilité du fichier et les réessais.

2. **Logs de Copie de Fichiers** :
    - Logs des fichiers copiés vers le répertoire temporaire.
    - Erreurs éventuelles lors de la copie.

3. **Logs de Traitement des Fichiers** :
    - Logs des fichiers détectés et traités par l'observateur.
    - Logs des fichiers ignorés (non valides ou temporaires).

4. **Logs d'Encodage** :
    - Logs des succès et échecs lors de l'encodage des fichiers en base64.

5. **Logs d'Envoi à l'API** :
    - Logs des tentatives d'envoi des données à l'API.
    - Réponses de l'API, incluant les succès et les erreurs.

6. **Logs de Nettoyage** :
    - Logs des opérations de nettoyage du répertoire temporaire.
    - Erreurs éventuelles lors du nettoyage.

---

### Exemple de Fichier `.env`

```dotenv
WATCHED_DIRS=/path/to/dir1,/path/to/dir2,/path/to/dir3
TEMP_DIR=/path/to/tempdir
API_URL=https://api.example.com/endpoint
LAABS_AUTH=your_auth_token
ARCHIVAL_PROFILE_REFERENCE=profile_reference
SERVICE_LEVEL_REFERENCE=service_level
RETENTION_RULE_CODE=retention_rule
DESCRIPTION_CLASS=description_class
FULL_TEXT_INDEXATION=none
DESCRIPTION_LEVEL=description_level
```
