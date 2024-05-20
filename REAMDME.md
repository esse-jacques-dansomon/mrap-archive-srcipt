## Deploy

### Étape 1: Préparer le serveur

1. **Connexion au serveur** :
   Connectez-vous à votre serveur via SSH.

   ```bash
   ssh username@your_server_ip
   ```

2. **Mettre à jour le système** :
   Assurez-vous que votre système est à jour.

   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

3. **Installer Python** :
   Vérifiez si Python est installé. Si ce n'est pas le cas, installez-le.

   ```bash
   sudo apt install python3 python3-pip -y
   ```

### Étape 2: Configurer l'environnement

1. **Cloner le repository:

   ```bash
   git clone https://github.com/mrap-achive-script
   cd mrap-achive-script
   ```

2. **Créer un environnement virtuel** (optionnel mais recommandé) :

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Installer les dépendances** :

   ```bash
   pip install -r requirements.txt
   ```

### Étape 4: Configurer le script

Copier .env.local en .env et mettez les config
```bash
cp .env.local .env
nano .env
```
### Étape 5: Tester le script

Testez votre script pour vérifier qu'il fonctionne correctement.

```bash
python3 main.py
```

### Étape 6: Configurer le script pour s'exécuter en arrière-plan

Pour que le script s'exécute en arrière-plan et redémarre automatiquement en cas de redémarrage du serveur, vous pouvez utiliser `systemd` pour créer un service.

1. **Créer un fichier de service systemd** :

   ```bash
   sudo nano /etc/systemd/system/mrap-archive-script.service
   ```

2. **Ajouter la configuration suivante** :

   ```ini
   [Unit]
   Description=File Watcher Service
   After=network.target

   [Service]
   User=username
   WorkingDirectory=/home/username/mrap-archive-script
   ExecStart=/home/username/mrap-archive-script/venv/bin/python /home/username/mrap-archive-script/your_script.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Remplacez `username` par votre nom d'utilisateur et ajustez les chemins si nécessaire.

3. **Recharger les services systemd** :

   ```bash
   sudo systemctl daemon-reload
   ```

4. **Démarrer et activer le service** :

   ```bash
   sudo systemctl start mrap-archive-script.service
   sudo systemctl enable mrap-archive-script.service
   ```

5. **Vérifier le statut du service** :

   ```bash
   sudo systemctl status mrap-archive-script.service
   ```

Cela vous permettra de déployer et d'exécuter votre script de surveillance en arrière-plan sur un serveur Linux. Le script sera automatiquement redémarré en cas de problème ou de redémarrage du serveur.