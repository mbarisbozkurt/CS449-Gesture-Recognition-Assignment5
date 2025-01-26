import cv2
import numpy as np
from datetime import datetime
from config import *

class UIRenderer:
    def __init__(self, frame_width, frame_height):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.menu_items = []

    def create_gradient_background(self):
        gradient = np.zeros((self.frame_height, self.frame_width, 3), np.uint8)
        for i in range(self.frame_height):
            value = int(18 + (i/self.frame_height)*10)
            gradient[i] = [value, value, value]
        return gradient

    def draw_modern_ui(self, overlay, cursor_x, cursor_y, scroll_pos, current_song, playlist_songs, is_clicking=False):
        # Create gradient background that matches the overlay size
        gradient_bg = np.zeros(overlay.shape, np.uint8)
        for i in range(overlay.shape[0]):
            value = int(18 + (i/overlay.shape[0])*10)
            gradient_bg[i] = [value, value, value]
        overlay[:] = gradient_bg

        # Create and resize sidebar gradient
        sidebar_gradient = np.zeros((overlay.shape[0], SIDEBAR_WIDTH, 3), np.uint8)
        for i in range(overlay.shape[0]):
            value = int(18 + (i/overlay.shape[0])*10)
            sidebar_gradient[i] = [value, value, value]
        
        # Apply sidebar gradient
        overlay[:, :SIDEBAR_WIDTH] = sidebar_gradient
        
        # Draw current time
        self._draw_current_time(overlay)
        
        # Draw Now Playing text at the top
        if current_song:
            font = cv2.FONT_HERSHEY_SIMPLEX
            if current_song.is_playing:
                status_text = f"Now Playing: {current_song.title} - {current_song.artist}"
            else:
                status_text = f"Paused: {current_song.title} - {current_song.artist}"
            
            # Y pozisyonunu biraz yukarı al
            text_y = TOP_BAR_HEIGHT//2 + 10
            
            # Siyah gölge efekti için önce siyah renkle yaz
            cv2.putText(overlay, status_text,
                       (SIDEBAR_WIDTH + CONTENT_PADDING + 2, text_y + 2),
                       font, 1.0, (0, 0, 0), 3, cv2.LINE_AA)
            
            # Sonra ana metni yaz
            cv2.putText(overlay, status_text,
                       (SIDEBAR_WIDTH + CONTENT_PADDING, text_y),
                       font, 1.0, ACCENT_COLOR if current_song.is_playing else TEXT_COLOR_SECONDARY, 2, cv2.LINE_AA)
        
        # Draw menu items
        self._draw_menu_items(overlay, cursor_x, cursor_y)
        
        # Draw current song info
        self._draw_current_song(overlay, current_song, cursor_x, cursor_y)
        
        # Draw playlist
        self._draw_playlist(overlay, cursor_x, cursor_y, scroll_pos, playlist_songs)
        
        # Draw cursor
        self._draw_cursor(overlay, cursor_x, cursor_y, is_clicking)

    def _draw_current_time(self, overlay):
        current_time = datetime.now().strftime("%H:%M")
        font = cv2.FONT_HERSHEY_SIMPLEX
        time_size = cv2.getTextSize(current_time, font, 1.2, 2)[0]
        cv2.putText(overlay, current_time, 
                   (self.frame_width - time_size[0] - 60, TOP_BAR_HEIGHT//2 + 12),
                   font, 1.2, TEXT_COLOR, 2, cv2.LINE_AA)

    def _draw_menu_items(self, overlay, cursor_x, cursor_y):
        font = cv2.FONT_HERSHEY_SIMPLEX
        menu_start_y = 120
        
        for i, item in enumerate(self.menu_items):
            y_pos = menu_start_y + i * MENU_ITEM_SPACING
            is_hovered = cursor_y is not None and abs(cursor_y - y_pos) < 20 and cursor_x < SIDEBAR_WIDTH
            
            if is_hovered:
                cv2.rectangle(overlay, (20, y_pos - 25), (SIDEBAR_WIDTH - 20, y_pos + 15),
                            HOVER_COLOR, -1)
                color = ACCENT_COLOR
            else:
                color = TEXT_COLOR

            cv2.putText(overlay, item, (40, y_pos), font, 1.0, color, 2, cv2.LINE_AA)

    def _draw_current_song(self, overlay, current_song, cursor_x, cursor_y):
        if current_song is None:
            # Eğer çalan şarkı yoksa varsayılan bir mesaj göster
            font = cv2.FONT_HERSHEY_SIMPLEX
            song_y = self.frame_height - 140

            # Ana arka plan
            cv2.rectangle(overlay, (10, song_y - 30), (SIDEBAR_WIDTH - 10, song_y + 70),
                         SECONDARY_COLOR, -1)

            # Başlık arka planı
            cv2.rectangle(overlay, (10, song_y - 30), (SIDEBAR_WIDTH - 10, song_y + 5),
                         (25, 25, 25), -1)

            # Varsayılan mesaj
            cv2.putText(overlay, "Şarkı seçilmedi", (25, song_y), 
                        font, 0.9, TEXT_COLOR, 2, cv2.LINE_AA)
            
            cv2.putText(overlay, "Bir şarkı seçin", (25, song_y + 30), 
                        font, 0.7, TEXT_COLOR_SECONDARY, 2, cv2.LINE_AA)
            return

        font = cv2.FONT_HERSHEY_SIMPLEX
        song_y = self.frame_height - 140

        # Ana arka plan
        cv2.rectangle(overlay, (10, song_y - 30), (SIDEBAR_WIDTH - 10, song_y + 70),
                     SECONDARY_COLOR, -1)

        # Başlık arka planı
        cv2.rectangle(overlay, (10, song_y - 30), (SIDEBAR_WIDTH - 10, song_y + 5),
                     (25, 25, 25), -1)

        # Şarkı başlığı - daha küçük font
        cv2.putText(overlay, current_song.title, (25, song_y), 
                    font, 0.9, TEXT_COLOR, 2, cv2.LINE_AA)
        
        # Sanatçı adı - daha küçük ve yukarı
        cv2.putText(overlay, current_song.artist, (25, song_y + 30), 
                    font, 0.7, TEXT_COLOR_SECONDARY, 2, cv2.LINE_AA)

        # Progress bar - yukarı
        progress_width = SIDEBAR_WIDTH - 50
        progress_y = song_y + 50

        # Progress bar arka plan
        cv2.rectangle(overlay, (25, progress_y), (25 + progress_width, progress_y + 3),
                     (40, 40, 40), -1)

        # Progress bar aktif kısım
        progress = int(progress_width * current_song.progress)
        if progress > 0:
            cv2.rectangle(overlay, (25, progress_y), (25 + progress, progress_y + 3),
                         ACCENT_COLOR, -1)

        # Kontrol butonları için ortak y pozisyonu
        controls_y = song_y + 20

        # Durdur butonu - hover alanını genişlet
        pause_x = SIDEBAR_WIDTH - 120
        pause_hover_area = {
            'x1': pause_x - 50,  # Biraz daha geniş hover alanı
            'y1': controls_y - 30,  # Biraz daha yüksek hover alanı
            'x2': pause_x + 50,
            'y2': controls_y + 30
        }
        is_pause_hovered = (cursor_x >= pause_hover_area['x1'] and cursor_x <= pause_hover_area['x2'] and 
                          cursor_y >= pause_hover_area['y1'] and cursor_y <= pause_hover_area['y2'])
        
        cv2.rectangle(overlay, (pause_x - 45, controls_y - 25), (pause_x + 45, controls_y + 25),
                     HOVER_COLOR if current_song.is_playing and is_pause_hovered else (40, 40, 40), -1)
        cv2.rectangle(overlay, (pause_x - 45, controls_y - 25), (pause_x + 45, controls_y + 25),
                     ACCENT_COLOR, 2)
        cv2.putText(overlay, "DURDUR", (pause_x - 40, controls_y + 8),
                   font, 0.7, TEXT_COLOR, 2, cv2.LINE_AA)

        # Devam et butonu - hover alanını genişlet
        play_x = SIDEBAR_WIDTH - 35
        play_hover_area = {
            'x1': play_x - 50,  # Biraz daha geniş hover alanı
            'y1': controls_y - 30,  # Biraz daha yüksek hover alanı
            'x2': play_x + 50,
            'y2': controls_y + 30
        }
        is_play_hovered = (cursor_x >= play_hover_area['x1'] and cursor_x <= play_hover_area['x2'] and 
                         cursor_y >= play_hover_area['y1'] and cursor_y <= play_hover_area['y2'])
        
        cv2.rectangle(overlay, (play_x - 45, controls_y - 25), (play_x + 45, controls_y + 25),
                     HOVER_COLOR if not current_song.is_playing and is_play_hovered else (40, 40, 40), -1)
        cv2.rectangle(overlay, (play_x - 45, controls_y - 25), (play_x + 45, controls_y + 25),
                     ACCENT_COLOR, 2)
        cv2.putText(overlay, "DEVAM", (play_x - 35, controls_y + 8),
                   font, 0.7, TEXT_COLOR, 2, cv2.LINE_AA)

    def _draw_playlist(self, overlay, cursor_x, cursor_y, scroll_pos, playlist_songs):
        font = cv2.FONT_HERSHEY_SIMPLEX
        content_x = SIDEBAR_WIDTH + CONTENT_PADDING
        content_y = TOP_BAR_HEIGHT + CONTENT_PADDING - int(scroll_pos)
        
        # Draw header
        header_text = "Your Playlist"
        cv2.putText(overlay, header_text, (content_x + 2, content_y + 2), 
                    font, 2.0, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(overlay, header_text, (content_x, content_y), 
                    font, 2.0, TEXT_COLOR, 3, cv2.LINE_AA)
        
        # Draw songs
        for i, song in enumerate(playlist_songs):
            item_y = content_y + 100 + i * SONG_ITEM_HEIGHT
            
            if item_y < TOP_BAR_HEIGHT or item_y > self.frame_height:
                continue
                
            is_hovered = cursor_y is not None and item_y - 40 < cursor_y < item_y + 40
            if is_hovered:
                cv2.rectangle(overlay, 
                            (content_x - 40, item_y - 45),
                            (self.frame_width - CONTENT_PADDING, item_y + 45),
                            HOVER_COLOR, -1)
            
            # Oynat butonu
            play_x = content_x + 40
            play_y = item_y
            
            # Oynat butonu arka planı (daire)
            cv2.circle(overlay, (play_x, play_y), 35, 
                      HOVER_COLOR if hasattr(song, 'is_playing') and song.is_playing else (40, 40, 40), -1)
            cv2.circle(overlay, (play_x, play_y), 35, ACCENT_COLOR, 2)
            
            # Play ikonu (üçgen)
            triangle_size = 25
            pts = np.array([
                [play_x - triangle_size//2, play_y - triangle_size],
                [play_x - triangle_size//2, play_y + triangle_size],
                [play_x + triangle_size, play_y]
            ], np.int32)
            cv2.fillPoly(overlay, [pts], TEXT_COLOR)

            # Durdur butonu
            pause_x = content_x + 130
            pause_y = item_y
            
            # Durdur butonu arka planı (daire)
            cv2.circle(overlay, (pause_x, pause_y), 35, 
                      HOVER_COLOR if hasattr(song, 'is_playing') and song.is_playing else (40, 40, 40), -1)
            cv2.circle(overlay, (pause_x, pause_y), 35, ACCENT_COLOR, 2)
            
            # Pause ikonu (iki dikey çizgi)
            bar_width = 8
            bar_height = 30
            cv2.rectangle(overlay, 
                         (pause_x - bar_width - 6, pause_y - bar_height//2),
                         (pause_x - 6, pause_y + bar_height//2),
                         TEXT_COLOR, -1)
            cv2.rectangle(overlay, 
                         (pause_x + 6, pause_y - bar_height//2),
                         (pause_x + bar_width + 6, pause_y + bar_height//2),
                         TEXT_COLOR, -1)
            
            title_color = ACCENT_COLOR if is_hovered else TEXT_COLOR
            cv2.putText(overlay, song.title, (content_x + 200, item_y), 
                       font, 1.0, title_color, 2, cv2.LINE_AA)
            
            cv2.putText(overlay, song.artist, (content_x + 650, item_y),
                       font, 0.9, TEXT_COLOR_SECONDARY, 2, cv2.LINE_AA)
            
            duration_x = self.frame_width - 120
            cv2.putText(overlay, song.duration, (duration_x, item_y),
                       font, 0.9, TEXT_COLOR_SECONDARY, 2, cv2.LINE_AA)

    def _draw_cursor(self, overlay, cursor_x, cursor_y, is_clicking):
        if cursor_x != -1 and cursor_y != -1:
            cv2.circle(overlay, (cursor_x, cursor_y), 20, CURSOR_OUTLINE_COLOR, 3)
            cursor_color = (0, 255, 0) if is_clicking else ACCENT_COLOR
            cv2.circle(overlay, (cursor_x, cursor_y), 16, (*cursor_color, 255), -1)
            cv2.circle(overlay, (cursor_x, cursor_y), 10, cursor_color, -1) 