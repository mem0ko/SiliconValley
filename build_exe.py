import os
import sys
import subprocess
import shutil
from PyInstaller.__main__ import run

# Configuration
app_name = "SiliconValley"
main_script = "main.py"
resources_dir = "resources"
dist_dir = "dist"

# Créer le dossier de distribution
if not os.path.exists(dist_dir):
    os.makedirs(dist_dir)

# Nettoyer les builds précédents
if os.path.exists("build"):
    shutil.rmtree("build")

# Options PyInstaller
opts = [
    main_script,
    '--onefile',
    '--windowed',
    '--name', app_name,
    '--add-data', f'{resources_dir};resources',
    '--distpath', dist_dir,
    '--hidden-import', 'pygame._sdl2.audio',
]

# Construire l'exécutable
run(opts)

print(f"L'exécutable a été créé dans le dossier {dist_dir}")