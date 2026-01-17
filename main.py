import pygame
import sys
import os
import subprocess
import threading
import time
import urllib.request
import json
import shutil
from pygame.locals import *

# Ajouter le chemin des ressources au système
if getattr(sys, 'frozen', False):
    # Mode exécutable (Nuitka ou PyInstaller)
    base_path = sys._MEIPASS
else:
    # Mode développement ou portable
    base_path = os.path.dirname(os.path.abspath(__file__))

# Ajouter le chemin des ressources
resources_path = os.path.join(base_path, 'resources')
if resources_path not in sys.path:
    sys.path.insert(0, resources_path)

# Pour Windows: définir l'icône de l'application au niveau du système
if os.name == 'nt':
    import ctypes
    from ctypes import wintypes

# Chemins des ressources
def resource_path(relative_path):
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    exe_resource = os.path.join(exe_dir, relative_path)
    
    if os.path.exists(exe_resource):
        return exe_resource
    
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    resource_file = os.path.join(base_path, relative_path)
    if os.path.exists(resource_file):
        return resource_file
    
    return relative_path

# Initialisation de Pygame
pygame.init()
pygame.mixer.init()

# Configuration de la fenêtre sans bordure
WIDTH, HEIGHT = 1092, 382
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("Silicon Valley Downloader")

# --- GESTION DE L'ICÔNE ---
print("\n" + "="*50)
print("Initialisation de l'icône...")

def load_application_icon():
    """Charge l'icône de l'application depuis plusieurs emplacements possibles"""
    
    icon_paths = [
        os.path.join(os.path.dirname(sys.executable), "SiliconValley.ico"),
        os.path.join(os.path.dirname(sys.executable), "resources", "SiliconValley.ico"),
        os.path.join(os.path.dirname(sys.executable), "SiliconValley.png"),
        os.path.join(os.path.dirname(sys.executable), "resources", "SiliconValley.png"),
        
        os.path.join(sys._MEIPASS, "SiliconValley.ico") if hasattr(sys, '_MEIPASS') else "",
        os.path.join(sys._MEIPASS, "resources", "SiliconValley.ico") if hasattr(sys, '_MEIPASS') else "",
        os.path.join(sys._MEIPASS, "SiliconValley.png") if hasattr(sys, '_MEIPASS') else "",
        os.path.join(sys._MEIPASS, "resources", "SiliconValley.png") if hasattr(sys, '_MEIPASS') else "",
        
        "SiliconValley.ico",
        "resources/SiliconValley.ico",
        "SiliconValley.png",
        "resources/SiliconValley.png",
        
        resource_path("SiliconValley.ico"),
        resource_path("resources/SiliconValley.ico"),
        resource_path("SiliconValley.png"),
        resource_path("resources/SiliconValley.png"),
    ]
    
    icon_paths = [p for p in icon_paths if p]
    
    for icon_path in icon_paths:
        if os.path.exists(icon_path):
            try:
                icon = pygame.image.load(icon_path)
                pygame.display.set_icon(icon)
                print(f"  ✓ Icône chargée : {os.path.basename(icon_path)}")
                return True
            except:
                continue
    
    print("  ✗ Aucune icône valide trouvée")
    return False

# Charger l'icône
if not load_application_icon():
    print("  ⚠ Utilisation de l'icône par défaut de Pygame")

# Pour Windows: définir l'AppUserModelID
if os.name == 'nt':
    try:
        hwnd = pygame.display.get_wm_info()['window']
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SiliconValley.Downloader.1.0")
        print("  ✓ AppUserModelID défini")
    except Exception as e:
        print(f"  ✗ Erreur AppUserModelID : {e}")

print("="*50 + "\n")

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
BLUE = (0, 150, 255)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
TURQUOISE = (64, 224, 208)

# Police
font = pygame.font.SysFont('Arial', 12)
big_font = pygame.font.SysFont('Arial', 14)
loading_font = pygame.font.SysFont('Arial', 16)

# Variables de l'application
APP_NAME = "SiliconValley"
output_dir = ""
format_choice = "mp4"
download_mode = "single"
current_step = "loading"  # Changé de "enter_url" à "loading"
status_message = ""
urls_file_path = ""
music_playing = False
music_thread = None
muted = False
downloading = False
download_thread = None
background_image = None
logo_image = None
device_image = None
single_url = ""
start_time = ""
end_time = ""
progress = 0.0
progress_text = ""
restart_after_download = False
mute_button_image = None
quit_button_image = None
last_progress_update = 0
updating = False
update_status = ""
download_completed = False
loading_progress = 0.0
loading_message = "Initialisation..."
loading_steps = 6  # Nombre d'étapes de chargement
loading_background_image = None  # Image de fond pour l'écran de chargement
loading_logo_image = None  # Logo pour l'écran de chargement

# Variables globales pour les outils
BASE_DIR = ""
TOOLS_PATH = ""
YTDLP = ""
FFMPEG = ""
ERROR_LOG = ""

# CHARGEMENT DES IMAGES DE L'ÉCRAN DE CHARGEMENT (IMMÉDIATEMENT)
def load_loading_screen_images():
    """Charge les images pour l'écran de chargement immédiatement"""
    global loading_background_image, loading_logo_image
    
    print("Chargement des images pour l'écran de chargement...")
    
    # Charger l'image de fond
    try:
        bg_path = resource_path("resources/images/background.png")
        if os.path.exists(bg_path):
            loading_background_image = pygame.image.load(bg_path).convert()
            if loading_background_image.get_size() != (WIDTH, HEIGHT):
                loading_background_image = pygame.transform.scale(loading_background_image, (WIDTH, HEIGHT))
            print("  ✓ Background chargé")
        else:
            print(f"  ✗ Fichier non trouvé: {bg_path}")
    except Exception as e:
        print(f"  ✗ Erreur chargement background: {e}")
        loading_background_image = None
    
    # Charger le logo
    try:
        logo_path = resource_path("resources/images/SILICON_VALLEY.png")
        if os.path.exists(logo_path):
            loading_logo_image = pygame.image.load(logo_path).convert_alpha()
            print("  ✓ Logo chargé")
        else:
            print(f"  ✗ Fichier non trouvé: {logo_path}")
    except Exception as e:
        print(f"  ✗ Erreur chargement logo: {e}")
        loading_logo_image = None
    
    return loading_background_image is not None or loading_logo_image is not None

# Fonction d'initialisation avec progression
def init_directories_with_progress():
    global BASE_DIR, TOOLS_PATH, YTDLP, FFMPEG, ERROR_LOG, loading_progress, loading_message, updating, update_status
    
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    loading_progress = 0.1
    loading_message = "Création des dossiers..."
    
    base_dir = os.path.join(base_path, APP_NAME)
    os.makedirs(base_dir, exist_ok=True)
    
    tools_path = os.path.join(base_dir, "Tools")
    os.makedirs(tools_path, exist_ok=True)
    
    loading_progress = 0.2
    loading_message = "Vérification de FFmpeg..."
    
    # Chemins des exécutables
    ytdlp_path = os.path.join(tools_path, "yt-dlp.exe")
    ffmpeg_path = os.path.join(tools_path, "ffmpeg.exe")
    
    # Copier ffmpeg s'il n'existe pas
    if not os.path.exists(ffmpeg_path):
        try:
            source_paths = [
                resource_path(f"resources/ffmpeg.exe"),
                os.path.join(base_path, "resources", "ffmpeg.exe"),
                os.path.join(resources_path, "ffmpeg.exe")
            ]
            
            for source_path in source_paths:
                if os.path.exists(source_path):
                    shutil.copy(source_path, ffmpeg_path)
                    break
        except Exception as e:
            print(f"Erreur lors de la copie de ffmpeg.exe: {e}")
    
    loading_progress = 0.4
    loading_message = "Vérification de yt-dlp..."
    
    # Vérifier et mettre à jour yt-dlp
    try:
        updating = True
        
        # Vérifier la version locale de yt-dlp
        local_version = None
        if os.path.exists(ytdlp_path):
            try:
                result = subprocess.run([ytdlp_path, "--version"], 
                                      capture_output=True, 
                                      text=True, 
                                      creationflags=subprocess.CREATE_NO_WINDOW,
                                      timeout=5)
                if result.returncode == 0:
                    local_version = result.stdout.strip()
                    loading_message = f"yt-dlp v{local_version} détecté"
            except:
                pass
        
        loading_progress = 0.5
        loading_message = "Vérification des mises à jour..."
        
        # Récupérer la dernière version depuis GitHub
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get('tag_name', '').replace('v', '')
                
                if local_version != latest_version:
                    loading_message = f"Mise à jour vers v{latest_version}..."
                    loading_progress = 0.6
                    
                    # Télécharger la dernière version
                    download_url = None
                    for asset in data.get('assets', []):
                        if asset.get('name') == 'yt-dlp.exe':
                            download_url = asset.get('browser_download_url')
                            break
                    
                    if download_url:
                        temp_path = ytdlp_path + ".new"
                        urllib.request.urlretrieve(download_url, temp_path)
                        
                        if os.path.exists(ytdlp_path):
                            os.remove(ytdlp_path)
                        os.rename(temp_path, ytdlp_path)
                        
                        loading_message = f"yt-dlp mis à jour (v{latest_version})"
                    else:
                        loading_message = "Utilisation de la version locale"
                else:
                    loading_message = "yt-dlp est à jour"
                    
        except Exception as e:
            loading_message = "Connexion impossible, version locale utilisée"
    
    except Exception as e:
        loading_message = f"Erreur mise à jour: {e}"
    
    loading_progress = 0.8
    loading_message = "Installation de yt-dlp..."
    
    # Copier yt-dlp s'il n'existe pas
    if not os.path.exists(ytdlp_path):
        try:
            source_paths = [
                resource_path(f"resources/yt-dlp.exe"),
                os.path.join(base_path, "resources", "yt-dlp.exe"),
                os.path.join(resources_path, "yt-dlp.exe")
            ]
            
            for source_path in source_paths:
                if os.path.exists(source_path):
                    shutil.copy(source_path, ytdlp_path)
                    loading_message = "yt-dlp installé"
                    break
        except Exception as e:
            loading_message = f"Erreur installation yt-dlp: {e}"
    
    updating = False
    loading_progress = 1.0
    loading_message = "Prêt!"
    
    return base_dir, tools_path

# Charger les images pour l'interface principale
def load_all_images():
    global background_image, logo_image, device_image, mute_button_image, quit_button_image
    
    # Charger l'image de fond (même que l'écran de chargement)
    background_image = loading_background_image
    
    # Charger le logo (même que l'écran de chargement)
    logo_image = loading_logo_image
    
    # Charger l'image device
    try:
        device_path = resource_path("resources/images/devicelock.png")
        device_image = pygame.image.load(device_path).convert_alpha()
        print("  ✓ Device image chargée")
    except Exception as e:
        print(f"  ✗ Erreur chargement device: {e}")
        device_image = None
    
    # Charger l'image du bouton mute
    try:
        mute_path = resource_path("resources/icons/buttons/mute.png")
        mute_button_image = pygame.image.load(mute_path).convert_alpha()
        if mute_button_image.get_size() != (30, 30):
            mute_button_image = pygame.transform.scale(mute_button_image, (30, 30))
        print("  ✓ Mute button chargé")
    except Exception as e:
        print(f"  ✗ Erreur chargement bouton mute: {e}")
        mute_button_image = None
    
    # Charger l'image du bouton quit
    try:
        quit_path = resource_path("resources/icons/buttons/QUIT.png")
        quit_button_image = pygame.image.load(quit_path).convert_alpha()
        if quit_button_image.get_size() != (30, 30):
            quit_button_image = pygame.transform.scale(quit_button_image, (30, 30))
        print("  ✓ Quit button chargé")
    except Exception as e:
        print(f"  ✗ Erreur chargement bouton quit: {e}")
        quit_button_image = None

# Fonction pour dessiner l'écran de chargement avec le background et logo
def draw_loading_screen():
    # Afficher l'image de fond
    if loading_background_image:
        screen.blit(loading_background_image, (0, 0))
    else:
        screen.fill(BLACK)
    
    # Afficher le logo SILICON_VALLEY en haut
    if loading_logo_image:
        logo_rect = loading_logo_image.get_rect()
        logo_rect.center = (WIDTH//2, 60)
        screen.blit(loading_logo_image, logo_rect)
    
    # Message de chargement sous le logo
    loading_text = loading_font.render(loading_message, True, TURQUOISE)
    text_x = WIDTH//2 - loading_text.get_width()//2
    text_y = 180
    screen.blit(loading_text, (text_x, text_y))
    
    # Barre de progression
    bar_width = 400
    bar_height = 20
    bar_x = WIDTH//2 - bar_width//2
    bar_y = 220
    
    # Fond de la barre
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height), 2)
    
    # Progression
    fill_width = int(bar_width * loading_progress)
    if fill_width > 0:
        pygame.draw.rect(screen, CYAN, (bar_x, bar_y, fill_width, bar_height))
    
    # Pourcentage
    percent_text = font.render(f"{int(loading_progress * 100)}%", True, WHITE)
    percent_x = WIDTH//2 - percent_text.get_width()//2
    percent_y = bar_y + bar_height + 10
    screen.blit(percent_text, (percent_x, percent_y))

# Fonction d'initialisation dans un thread
def initialization_thread():
    global BASE_DIR, TOOLS_PATH, YTDLP, FFMPEG, ERROR_LOG, current_step, background_image, logo_image
    
    # Initialiser les dossiers et outils
    BASE_DIR, TOOLS_PATH = init_directories_with_progress()
    YTDLP = os.path.join(TOOLS_PATH, "yt-dlp.exe")
    FFMPEG = os.path.join(TOOLS_PATH, "ffmpeg.exe")
    ERROR_LOG = os.path.join(TOOLS_PATH, "error.log")
    
    # Charger les images restantes
    load_all_images()
    
    # Démarrer la musique
    start_background_music()
    
    # Petite pause pour voir l'écran de chargement à 100%
    time.sleep(0.5)
    
    # Passer à l'étape suivante
    current_step = "enter_url"

# Fonction pour jouer de la musique
def music_loop():
    global music_playing
    music_file = resource_path("resources/background.mp3")
    if os.path.exists(music_file):
        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.play(-1)
            if not muted:
                pygame.mixer.music.set_volume(0.7)
            while music_playing:
                time.sleep(0.1)
        except Exception as e:
            print(f"Erreur lors de la lecture de la musique: {e}")

def start_background_music():
    global music_playing, music_thread
    if not music_playing:
        music_playing = True
        music_thread = threading.Thread(target=music_loop)
        music_thread.daemon = True
        music_thread.start()

def toggle_mute():
    global muted
    if muted:
        muted = False
        pygame.mixer.music.set_volume(0.7)
        return False
    else:
        muted = True
        pygame.mixer.music.set_volume(0.0)
        return True

def stop_background_music():
    global music_playing
    if music_playing:
        pygame.mixer.music.stop()
        music_playing = False

def get_clipboard_text():
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        clipboard_text = root.clipboard_get()
        root.destroy()
        return clipboard_text
    except Exception as e:
        return ""

# Lire le fichier URLs avec timecodes
def parse_urls_file(file_path):
    urls_data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 1:
                    url = parts[0]
                    start_time = parts[1] if len(parts) > 1 else None
                    end_time = parts[2] if len(parts) > 2 else None
                    urls_data.append({
                        'url': url,
                        'start_time': start_time,
                        'end_time': end_time,
                        'line': line_num
                    })
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier URLs: {e}")
    
    return urls_data

# Fonction de téléchargement unique avec surveillance de progression améliorée
def download_single_video():
    global status_message, downloading, progress, progress_text, current_step, last_progress_update, download_completed
    
    try:
        downloading = True
        download_completed = False
        progress = 0.0
        progress_text = "Initialisation..."
        last_progress_update = time.time()
        
        if not single_url.strip():
            status_message = "Erreur: Aucune URL fournie"
            downloading = False
            return
        
        progress = 0.1
        progress_text = "Préparation du téléchargement..."
        last_progress_update = time.time()
        
        if format_choice == "mp4":
            format_opts = ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4"]
        else:
            format_opts = ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
        
        clip_opts = []
        if start_time.strip() and end_time.strip():
            clip_opts = ["--download-sections", f"*{start_time.strip()}-{end_time.strip()}"]
        
        progress = 0.2
        progress_text = "Démarrage du téléchargement..."
        last_progress_update = time.time()
        
        command = [
            YTDLP,
            *format_opts,
            *clip_opts,
            "--no-download-archive",
            "--progress",
            "--newline",
            "--no-warnings",
            "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
            single_url.strip()
        ]
        
        progress = 0.3
        progress_text = "Téléchargement en cours..."
        last_progress_update = time.time()
        
        # Utiliser Popen pour pouvoir lire la progression en temps réel
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        last_update_time = time.time()
        progress_lines = []
        
        # Lire la sortie en temps réel pour détecter la progression
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                progress_lines.append(line)
                
                # Essayer d'extraire le pourcentage de progression
                if "[download]" in line and "%" in line:
                    try:
                        # Chercher le pourcentage dans la ligne
                        percent_str = ""
                        for part in line.split():
                            if "%" in part:
                                percent_str = part.replace("%", "")
                                break
                        
                        if percent_str:
                            new_progress = float(percent_str) / 100.0
                            if new_progress > progress:
                                progress = new_progress
                                last_progress_update = time.time()
                                last_update_time = time.time()
                                progress_text = f"Téléchargement... {int(progress*100)}%"
                    except:
                        pass
                
                # Détecter la fin du téléchargement
                if "100%" in line or "Deleting original file" in line or "Merging formats" in line:
                    progress = 1.0
                    last_progress_update = time.time()
                    progress_text = "Finalisation..."
                    break
            
            # Vérifier si le processus est terminé
            if process.poll() is not None:
                break
        
        # Attendre la fin du processus
        process.wait()
        return_code = process.returncode
        
        # Vérifier le résultat
        if return_code == 0:
            progress = 1.0
            progress_text = "Téléchargement terminé!"
            status_message = "Téléchargement terminé avec succès!"
            download_completed = True
            # Forcer une mise à jour finale
            last_progress_update = time.time()
            time.sleep(1)
            current_step = "finished"
        else:
            progress = 0.0
            progress_text = "Erreur lors du téléchargement"
            status_message = f"Erreur: Code de retour {return_code}"
            
    except Exception as e:
        progress = 0.0
        progress_text = f"Erreur: {str(e)}"
        status_message = f"Erreur: {str(e)}"
    finally:
        downloading = False

# Fonction de téléchargement multiple
def download_multiple_videos():
    global status_message, downloading, progress, progress_text, current_step, last_progress_update
    
    try:
        downloading = True
        urls_data = parse_urls_file(urls_file_path)
        last_progress_update = time.time()
        
        if not urls_data:
            status_message = "Erreur: Aucune URL valide dans le fichier"
            return
        
        total_urls = len(urls_data)
        
        for i, url_data in enumerate(urls_data, 1):
            progress = i / total_urls
            progress_text = f"Téléchargement {i}/{total_urls}"
            last_progress_update = time.time()
            
            if format_choice == "mp4":
                format_opts = ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", "--merge-output-format", "mp4"]
            else:
                format_opts = ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
            
            clip_opts = []
            if url_data['start_time'] and url_data['end_time']:
                clip_opts = ["--download-sections", f"*{url_data['start_time']}-{url_data['end_time']}"]
            
            command = [
                YTDLP,
                *format_opts,
                *clip_opts,
                "--no-download-archive",
                "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
                url_data['url']
            ]
            
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=300
            )
        
        progress = 1.0
        progress_text = f"Terminé! {total_urls} fichiers traités"
        status_message = f"Téléchargement terminé! {total_urls} fichiers traités"
        last_progress_update = time.time()
        time.sleep(0.5)
        current_step = "finished"
        
    except Exception as e:
        progress = 0.0
        progress_text = f"Erreur: {str(e)}"
        status_message = f"Erreur: {str(e)}"
    finally:
        downloading = False

# Classes d'interface
class FuturisticButton:
    def __init__(self, x, y, width, height, text, color=DARK_GRAY, border_color=CYAN):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.border_color = border_color
        self.is_hovered = False
        self.is_pressed = False
        
    def draw(self, surface):
        # Effet de brillance si survolé
        if self.is_hovered:
            glow_color = (self.border_color[0], self.border_color[1], self.border_color[2], 50)
            glow_surface = pygame.Surface((self.rect.width + 4, self.rect.height + 4), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect(), border_radius=3)
            surface.blit(glow_surface, (self.rect.x - 2, self.rect.y - 2))
        
        # Corps du bouton
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1)
        
        # Texte
        text_surface = font.render(self.text, True, self.border_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.is_pressed = True
            return True
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.is_pressed = False
        return False

class FuturisticInputBox:
    def __init__(self, x, y, width, height, placeholder=''):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ''
        self.placeholder = placeholder
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.select_all = False
        
    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos)
            
            # Réinitialiser la sélection quand on clique
            if self.active and not was_active:
                self.select_all = False
                
        if event.type == KEYDOWN and self.active:
            if event.key == K_a and pygame.key.get_mods() & KMOD_CTRL:
                # Ctrl+A pour sélectionner tout le texte
                self.select_all = True
            elif event.key == K_BACKSPACE:
                if self.select_all:
                    self.text = ''
                    self.select_all = False
                else:
                    self.text = self.text[:-1]
            elif event.key == K_v and pygame.key.get_mods() & KMOD_CTRL:
                clipboard = get_clipboard_text()
                if clipboard:
                    if self.select_all:
                        self.text = clipboard
                        self.select_all = False
                    else:
                        self.text += clipboard
            elif event.unicode.isprintable():
                if self.select_all:
                    self.text = event.unicode
                    self.select_all = False
                else:
                    self.text += event.unicode
            else:
                self.select_all = False
        return self.text
        
    def draw(self, surface):
        # Fond noir avec bordure cyan
        pygame.draw.rect(surface, BLACK, self.rect)
        border_color = CYAN if self.active else GRAY
        pygame.draw.rect(surface, border_color, self.rect, 1)
        
        # Texte ou placeholder
        display_text = self.text if self.text else self.placeholder
        text_color = WHITE if self.text else GRAY
        
        # Si le texte est sélectionné, afficher avec un fond de sélection
        if self.select_all and self.active and self.text:
            text_width = font.size(self.text)[0]
            highlight_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 3, text_width, self.rect.height - 6)
            pygame.draw.rect(surface, BLUE, highlight_rect)
            text_color = WHITE
        
        text_surface = font.render(display_text, True, text_color)
        surface.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        
        # Curseur clignotant
        if self.active and not self.select_all:
            self.cursor_timer += 1
            if self.cursor_timer > 30:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
            
            if self.cursor_visible:
                cursor_x = self.rect.x + 5 + font.size(self.text)[0]
                pygame.draw.line(surface, CYAN, (cursor_x, self.rect.y + 3), (cursor_x, self.rect.bottom - 3))

class ProgressBar:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.progress = 0.0
        
    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
        
    def draw(self, surface):
        # Fond noir
        pygame.draw.rect(surface, BLACK, self.rect)
        pygame.draw.rect(surface, GRAY, self.rect, 1)
        
        # Barre de progression cyan
        if self.progress > 0:
            fill_width = int(self.rect.width * self.progress)
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, CYAN, fill_rect)

# Fonction pour dessiner le bouton de fermeture avec image
def draw_quit_button(surface):
    quit_button_rect = pygame.Rect(WIDTH - 40, 10, 30, 30)
    
    if quit_button_image:
        surface.blit(quit_button_image, quit_button_rect)
    else:
        pygame.draw.circle(surface, CYAN, quit_button_rect.center, 15)
        pygame.draw.circle(surface, BLACK, quit_button_rect.center, 15, 2)
        
        center_x, center_y = quit_button_rect.center
        pygame.draw.line(surface, BLACK, (center_x - 6, center_y - 6), (center_x + 6, center_y + 6), 2)
        pygame.draw.line(surface, BLACK, (center_x + 6, center_y - 6), (center_x - 6, center_y + 6), 2)
    
    return quit_button_rect

# Fonction pour dessiner le bouton mute avec image
def draw_mute_button(surface):
    mute_button_rect = pygame.Rect(WIDTH - 40, 50, 30, 30)
    
    if mute_button_image:
        surface.blit(mute_button_image, mute_button_rect)
    else:
        pygame.draw.circle(surface, TURQUOISE, mute_button_rect.center, 15)
        pygame.draw.circle(surface, BLACK, mute_button_rect.center, 15, 2)
        
        if muted:
            pygame.draw.line(surface, BLACK, (mute_button_rect.centerx - 5, mute_button_rect.centery - 5), 
                             (mute_button_rect.centerx + 5, mute_button_rect.centery + 5), 2)
        else:
            pygame.draw.polygon(surface, BLACK, [
                (mute_button_rect.centerx - 4, mute_button_rect.centery - 2),
                (mute_button_rect.centerx - 4, mute_button_rect.centery + 2),
                (mute_button_rect.centerx, mute_button_rect.centery + 4),
                (mute_button_rect.centerx, mute_button_rect.centery - 4)
            ])
            pygame.draw.arc(surface, BLACK, (mute_button_rect.centerx - 2, mute_button_rect.centery - 6, 12, 12), 0, 1.5, 1)
            pygame.draw.arc(surface, BLACK, (mute_button_rect.centerx - 6, mute_button_rect.centery - 10, 20, 20), 0, 1.2, 1)
    
    return mute_button_rect

# Création des éléments d'interface
url_input = FuturisticInputBox(540, 208, 540, 25, "Enter URL here...")

# Boutons principaux
yes_button = FuturisticButton(540, 240, 80, 25, "yes")
no_button = FuturisticButton(630, 240, 80, 25, "no") 
paste_button = FuturisticButton(720, 240, 80, 25, "paste link")
choose_folder_button = FuturisticButton(810, 240, 120, 25, "Choose folder...")
restart_button = FuturisticButton(540, 340, 120, 25, "Restart")
exit_button = FuturisticButton(670, 340, 120, 25, "Exit")

# Boutons de format
mp4_button = FuturisticButton(540, 275, 80, 25, "MP4")
mp3_button = FuturisticButton(630, 275, 80, 25, "MP3")

# Boutons de mode
full_button = FuturisticButton(540, 275, 80, 25, "Full")
clip_button = FuturisticButton(630, 275, 80, 25, "Clip")

# Timecode inputs
start_time_input = FuturisticInputBox(540, 310, 80, 25, "Start")
end_time_input = FuturisticInputBox(630, 310, 80, 25, "End")

# Barre de progression
progress_bar = ProgressBar(540, 305, 540, 20)

# CHARGER LES IMAGES POUR L'ÉCRAN DE CHARGEMENT AVANT DE DÉMARRER
load_loading_screen_images()

# Démarrer le thread d'initialisation
init_thread = threading.Thread(target=initialization_thread)
init_thread.daemon = True
init_thread.start()

# Boucle principale
running = True
clock = pygame.time.Clock()

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        
        # Bouton fermeture (seulement si pas en chargement)
        if event.type == MOUSEBUTTONDOWN and current_step != "loading":
            quit_rect = draw_quit_button(screen)
            if quit_rect.collidepoint(event.pos):
                running = False
            
            # Bouton mute
            mute_rect = draw_mute_button(screen)
            if mute_rect.collidepoint(event.pos):
                toggle_mute()
        
        # Gestion des inputs (seulement si pas en chargement)
        if current_step != "loading":
            if current_step == "enter_url":
                single_url = url_input.handle_event(event) or single_url
            elif current_step == "timecode":
                start_time = start_time_input.handle_event(event) or start_time
                end_time = end_time_input.handle_event(event) or end_time
        
        # Gestion des boutons selon l'étape actuelle
        if current_step == "enter_url":
            if paste_button.handle_event(event):
                clipboard = get_clipboard_text()
                if clipboard:
                    single_url = clipboard
                    url_input.text = clipboard
                    url_input.select_all = True
            
            if yes_button.handle_event(event) and single_url.strip():
                current_step = "choose_format"
            
            if no_button.handle_event(event):
                current_step = "multiple_files"
        
        elif current_step == "choose_format":
            if mp4_button.handle_event(event):
                format_choice = "mp4"
                current_step = "choose_mode"
            
            if mp3_button.handle_event(event):
                format_choice = "mp3"
                current_step = "choose_mode"
        
        elif current_step == "choose_mode":
            if full_button.handle_event(event):
                current_step = "choose_destination"
            
            if clip_button.handle_event(event):
                current_step = "timecode"
        
        elif current_step == "timecode":
            if yes_button.handle_event(event):
                current_step = "choose_destination"
        
        elif current_step == "choose_destination":
            if choose_folder_button.handle_event(event):
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    
                    root = tk.Tk()
                    root.withdraw()
                    folder_selected = filedialog.askdirectory(title="Choisir le dossier de destination")
                    if folder_selected:
                        output_dir = folder_selected
                        current_step = "download"
                        download_thread = threading.Thread(target=download_single_video)
                        download_thread.daemon = True
                        download_thread.start()
                    
                    root.destroy()
                except Exception as e:
                    print(f"Erreur: {e}")
        
        elif current_step == "finished":
            if restart_button.handle_event(event):
                current_step = "enter_url"
                single_url = ""
                start_time = ""
                end_time = ""
                progress = 0.0
                progress_text = ""
                url_input.text = ""
                url_input.select_all = False
                download_completed = False
            
            if exit_button.handle_event(event):
                running = False
    
    # Mise à jour des états de survol (seulement si pas en chargement)
    if current_step != "loading":
        yes_button.check_hover(mouse_pos)
        no_button.check_hover(mouse_pos)
        paste_button.check_hover(mouse_pos)
        choose_folder_button.check_hover(mouse_pos)
        mp4_button.check_hover(mouse_pos)
        mp3_button.check_hover(mouse_pos)
        full_button.check_hover(mouse_pos)
        clip_button.check_hover(mouse_pos)
        restart_button.check_hover(mouse_pos)
        exit_button.check_hover(mouse_pos)
    
    # Dessin selon l'étape
    if current_step == "loading":
        # Écran de chargement avec background et logo
        draw_loading_screen()
        
    else:
        # Interface normale
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(BLACK)
        
        # Afficher l'image device à gauche sans redimensionnement
        if device_image:
            screen.blit(device_image, (0, 0))
        
        # Logo Silicon Valley en haut
        if logo_image:
            logo_rect = logo_image.get_rect()
            logo_rect.center = (WIDTH//2, 60)
            screen.blit(logo_image, logo_rect)
        
        # Affichage des instructions selon l'étape
        if current_step == "enter_url":
            instructions_text = big_font.render("Enter URL and press YES to continue:", True, TURQUOISE)
            screen.blit(instructions_text, (495, 180))
            
            url_input.draw(screen)
            yes_button.draw(screen)
            no_button.draw(screen)
            paste_button.draw(screen)
        
        elif current_step == "choose_format":
            instructions_text = big_font.render("Choose format (MP4 or MP3):", True, TURQUOISE)
            screen.blit(instructions_text, (495, 180))
            
            mp4_button.draw(screen)
            mp3_button.draw(screen)
        
        elif current_step == "choose_mode":
            instructions_text = big_font.render("Download full video or clip section?", True, TURQUOISE)
            screen.blit(instructions_text, (495, 180))
            
            full_button.draw(screen)
            clip_button.draw(screen)
        
        elif current_step == "timecode":
            instructions_text = big_font.render("Enter start and end timecodes (HH:MM:SS):", True, TURQUOISE)
            screen.blit(instructions_text, (495, 180))
            
            start_time_input.draw(screen)
            end_time_input.draw(screen)
            yes_button.draw(screen)
        
        elif current_step == "choose_destination":
            instructions_text = big_font.render("Choose destination folder:", True, TURQUOISE)
            screen.blit(instructions_text, (495, 180))
            
            choose_folder_button.draw(screen)
        
        elif current_step == "download":
            instructions_text = big_font.render("Downloading...", True, TURQUOISE)
            screen.blit(instructions_text, (495, 180))
            
            current_time = time.time()
            if current_time - last_progress_update > 30 and progress < 1.0 and not download_completed:
                progress_text = "Problème de connexion... Réessayez"
                if downloading:
                    progress = 0.0
            
            progress_bar.set_progress(progress)
            progress_bar.draw(screen)
            
            progress_text_surface = font.render(progress_text, True, WHITE)
            screen.blit(progress_text_surface, (540, 285))
            
            if not downloading and download_completed and current_time - last_progress_update > 2:
                current_step = "finished"
        
        elif current_step == "finished":
            instructions_text = big_font.render("Download completed! What do you want to do?", True, TURQUOISE)
            screen.blit(instructions_text, (495, 180))
            
            restart_button.draw(screen)
            exit_button.draw(screen)
        
        # Bouton de fermeture avec image
        draw_quit_button(screen)
        
        # Bouton mute avec image
        draw_mute_button(screen)
        
        # Status en bas à gauche
        if output_dir:
            status_surface = font.render(f"Destination: {os.path.basename(output_dir)}", True, CYAN)
            screen.blit(status_surface, (10, HEIGHT - 20))
    
    pygame.display.flip()
    clock.tick(60)

stop_background_music()
pygame.quit()
sys.exit()