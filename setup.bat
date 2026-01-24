@echo off
REM Script de configuration du projet pour Windows

echo Installation de Lyrion Playcount Sync
echo ======================================
echo.

REM Vérifier Python
python --version
if %errorlevel% neq 0 (
    echo Erreur: Python n'est pas installé ou non trouvé dans PATH
    exit /b 1
)

REM Créer l'environnement virtuel
if exist venv (
    echo Info: Environnement virtuel existant trouvé
) else (
    echo Creation de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Mettre à jour pip
echo Mise à jour de pip...
python -m pip install --upgrade pip

REM Installer les dépendances
echo Installation des dépendances...
pip install -r requirements.txt

REM Créer la configuration
if exist config.yaml (
    echo Info: Fichier config.yaml existant trouvé
) else (
    echo Creation du fichier config.yaml...
    copy config.yaml.example config.yaml
    echo Attention: N'oubliez pas de configurer config.yaml avec vos chemins!
)

echo.
echo Installation terminee!
echo.
echo Prochaines etapes:
echo 1. Configurer config.yaml avec vos chemins Lyrion
echo 2. Lancer l'application: python -m src.main
echo.
