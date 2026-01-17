import pygame
import sys
import os
import subprocess
import threading
import time
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

# Définir l'icône de la fenêtre
try:
    icon = pygame.image.load(resource_path("SiliconValley.png"))
    pygame.display.set_icon(icon)
except:
    print("Impossible de charger l'icône de l'application")

# Définir l'icône de l'application au niveau du système (Windows seulement)
if os.name == 'nt':
    try:
        # Obtenir le handle de la fenêtre
        hwnd = pygame.display.get_wm_info()['window']
        
        # Définir l'icône de l'application
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SiliconValley.Downloader.1.0")
    except Exception as e:
        print(f"Impossible de définir l'icône système: {e}")

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

# Variables de l'application
APP_NAME = "SiliconValley"
output_dir = ""
format_choice = "mp4"
download_mode = "single"
current_step = "enter_url"
status_message = ""
urls_file_path = ""
music_playing = False
music_thread = None
muted = False
downloading = False
download_thread = None
icon = "resources"
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
last_progress_update = 0  # Pour suivre le dernier moment où la progression a été mise à jour

# Initialisation des dossiers
def init_directories():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    base_dir = os.path.join(base_path, APP_NAME)
    os.makedirs(base_dir, exist_ok=True)
    
    tools_path = os.path.join(base_dir, "Tools")
    os.makedirs(tools_path, exist_ok=True)
    
    resources = {
        "yt-dlp.exe": os.path.join(tools_path, "yt-dlp.exe"),
        "ffmpeg.exe": os.path.join(tools_path, "ffmpeg.exe")
    }
    
    for res_name, res_path in resources.items():
        if not os.path.exists(res_path):
            try:
                import shutil
                source_paths = [
                    resource_path(f"resources/{res_name}"),
                    os.path.join(base_path, "resources", res_name),
                    os.path.join(resources_path, res_name)
                ]
                
                for source_path in source_paths:
                    if os.path.exists(source_path):
                        shutil.copy(source_path, res_path)
                        break
            except Exception as e:
                print(f"Erreur lors de la copie de {res_name}: {e}")
    
    return base_dir, tools_path

# Charger l'image de fond
def load_background():
    global background_image
    try:
        bg_path = resource_path("resources/images/background.png")
        background_image = pygame.image.load(bg_path).convert()
        if background_image.get_size() != (WIDTH, HEIGHT):
            background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
    except Exception as e:
        print(f"Erreur lors du chargement de l'image de fond: {e}")
        background_image = None

# Charger le logo
def load_logo():
    global logo_image
    try:
        logo_path = resource_path("resources/images/SILICON_VALLEY.png")
        logo_image = pygame.image.load(logo_path).convert_alpha()
    except Exception as e:
        print(f"Erreur lors du chargement du logo: {e}")
        logo_image = None

# Charger l'image device (sans redimensionnement)
def load_device_image():
    global device_image
    try:
        device_path = resource_path("resources/images/devicelock.png")
        device_image = pygame.image.load(device_path).convert_alpha()
        # On ne redimensionne pas l'image pour garder son format d'origine
    except Exception as e:
        print(f"Erreur lors du chargement de l'image device: {e}")
        device_image = None

# Charger l'image du bouton mute
def load_mute_button_image():
    global mute_button_image
    try:
        mute_path = resource_path("resources/icons/buttons/mute.png")
        mute_button_image = pygame.image.load(mute_path).convert_alpha()
        if mute_button_image.get_size() != (30, 30):
            mute_button_image = pygame.transform.scale(mute_button_image, (30, 30))
    except Exception as e:
        print(f"Erreur lors du chargement de l'image du bouton mute: {e}")
        mute_button_image = None

# Charger l'image du bouton quit
def load_quit_button_image():
    global quit_button_image
    try:
        quit_path = resource_path("resources/icons/buttons/QUIT.png")
        quit_button_image = pygame.image.load(quit_path).convert_alpha()
        if quit_button_image.get_size() != (30, 30):
            quit_button_image = pygame.transform.scale(quit_button_image, (30, 30))
    except Exception as e:
        print(f"Erreur lors du chargement de l'image du bouton quit: {e}")
        quit_button_image = None

# Initialisation
BASE_DIR, TOOLS_PATH = init_directories()
YTDLP = os.path.join(TOOLS_PATH, "yt-dlp.exe")
FFMPEG = os.path.join(TOOLS_PATH, "ffmpeg.exe")
ERROR_LOG = os.path.join(TOOLS_PATH, "error.log")

load_background()
load_logo()
load_device_image()
load_mute_button_image()
load_quit_button_image()

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

# Fonction de téléchargement unique avec surveillance de progression
def download_single_video():
    global status_message, downloading, progress, progress_text, current_step, last_progress_update
    
    try:
        downloading = True
        progress = 0.0
        progress_text = "Initialisation..."
        last_progress_update = time.time()
        
        if not single_url.strip():
            status_message = "Erreur: Aucune URL fournie"
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
        
        # Lire la sortie en temps réel pour détecter la progression
        for line in process.stdout:
            if "ETA" in line and "%" in line:
                # Essayer d'extraire le pourcentage de progression
                try:
                    percent_str = line.split("[download]")[1].split("%")[0].strip()
                    new_progress = float(percent_str) / 100.0
                    if new_progress > progress:
                        progress = new_progress
                        last_progress_update = time.time()
                        progress_text = f"Téléchargement... {int(progress*100)}%"
                except:
                    pass
            elif "Deleting original file" in line or "100%" in line:
                progress = 1.0
                last_progress_update = time.time()
                progress_text = "Finalisation..."
                break
        
        process.wait()
        
        if process.returncode == 0:
            progress = 1.0
            progress_text = "Téléchargement terminé!"
            status_message = "Téléchargement terminé avec succès!"
            # Forcer une mise à jour finale
            last_progress_update = time.time()
            time.sleep(0.5)  # Petit délai pour afficher la progression complète
            current_step = "finished"
        else:
            progress = 0.0
            progress_text = "Erreur lors du téléchargement"
            status_message = "Erreur lors du téléchargement"
            
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
        time.sleep(0.5)  # Petit délai pour afficher la progression complète
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
        # Fallback si l'image n'est pas chargée
        pygame.draw.circle(surface, CYAN, quit_button_rect.center, 15)
        pygame.draw.circle(surface, BLACK, quit_button_rect.center, 15, 2)
        
        # Dessiner le X
        center_x, center_y = quit_button_rect.center
        pygame.draw.line(surface, BLACK, (center_x - 6, center_y - 6), (center_x + 6, center_y + 6), 2)
        pygame.draw.line(surface, BLACK, (center_x + 6, center_y - 6), (center_x - 6, center_y + 6), 2)
    
    return quit_button_rect

# Fonction pour dessiner le bouton mute avec image (positionné sous le bouton de fermeture)
def draw_mute_button(surface):
    mute_button_rect = pygame.Rect(WIDTH - 40, 50, 30, 30)
    
    if mute_button_image:
        surface.blit(mute_button_image, mute_button_rect)
    else:
        # Fallback si l'image n'est pas chargée
        pygame.draw.circle(surface, TURQUOISE, mute_button_rect.center, 15)
        pygame.draw.circle(surface, BLACK, mute_button_rect.center, 15, 2)
        
        # Dessiner l'icône de son ou muet
        if muted:
            # Icône muet
            pygame.draw.line(surface, BLACK, (mute_button_rect.centerx - 5, mute_button_rect.centery - 5), 
                             (mute_button_rect.centerx + 5, mute_button_rect.centery + 5), 2)
        else:
            # Icône son
            pygame.draw.polygon(surface, BLACK, [
                (mute_button_rect.centerx - 4, mute_button_rect.centery - 2),
                (mute_button_rect.centerx - 4, mute_button_rect.centery + 2),
                (mute_button_rect.centerx, mute_button_rect.centery + 4),
                (mute_button_rect.centerx, mute_button_rect.centery - 4)
            ])
            # Ondes sonores
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

# Démarrer la musique
start_background_music()

# Boucle principale
running = True
clock = pygame.time.Clock()

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        
        # Bouton fermeture
        if event.type == MOUSEBUTTONDOWN:
            quit_rect = draw_quit_button(screen)
            if quit_rect.collidepoint(event.pos):
                running = False
            
            # Bouton mute
            mute_rect = draw_mute_button(screen)
            if mute_rect.collidepoint(event.pos):
                toggle_mute()
        
        # Gestion des inputs
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
                # Logique pour les fichiers multiples (à implémenter)
        
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
                        # Démarrer le téléchargement
                        download_thread = threading.Thread(target=download_single_video)
                        download_thread.daemon = True
                        download_thread.start()
                    
                    root.destroy()
                except Exception as e:
                    print(f"Erreur: {e}")
        
        elif current_step == "finished":
            if restart_button.handle_event(event):
                # Réinitialiser pour recommencer
                current_step = "enter_url"
                single_url = ""
                start_time = ""
                end_time = ""
                progress = 0.0
                progress_text = ""
                url_input.text = ""
                url_input.select_all = False
            
            if exit_button.handle_event(event):
                running = False
    
    # Mise à jour des états de survol
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
    
    # Dessin
    if background_image:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(BLACK)
    
    # Afficher l'image device à gauche sans redimensionnement
    if device_image:
        screen.blit(device_image, (0, 0))
    
    # Logo Silicon Valley en haut (ne pas changer)
    if logo_image:
        logo_rect = logo_image.get_rect()
        logo_rect.center = (WIDTH//2, 60)
        screen.blit(logo_image, logo_rect)
    
    # Affichage des instructions selon l'étape
    if current_step == "enter_url":
        instructions_text = big_font.render("Enter URL and press YES to continue:", True, TURQUOISE)
        screen.blit(instructions_text, (495, 180))
        
        # URL input box
        url_input.draw(screen)
        
        # Boutons
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
        
        # Vérifier si la progression est bloquée
        current_time = time.time()
        if current_time - last_progress_update > 10 and progress < 1.0:  # 10 secondes sans mise à jour
            progress_text = "Problème de connexion..."
        
        # Barre de progression
        progress_bar.set_progress(progress)
        progress_bar.draw(screen)
        
        # Texte de progression
        progress_text_surface = font.render(progress_text, True, WHITE)
        screen.blit(progress_text_surface, (540, 285))
    
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