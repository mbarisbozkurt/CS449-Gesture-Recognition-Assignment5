import cv2
import numpy as np
from datetime import datetime
from config import *

class UIRenderer:
    def __init__(self, frame_width, frame_height):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.menu_items = ["Home", "Search", "Library", "Playlists", "Settings"]

    def create_gradient_background(self):
        gradient = np.zeros((self.frame_height, self.frame_width, 3), np.uint8)
        for i in range(self.frame_height):
            value = int(18 + (i/self.frame_height)*10)
            gradient[i] = [value, value, value]
        return gradient

    def draw_modern_ui(self, overlay, cursor_x, cursor_y, scroll_pos, current_song, playlist_songs, is_clicking=False):
        # Create gradient background
        gradient_bg = self.create_gradient_background()
        overlay[:] = gradient_bg

        # Create and resize sidebar gradient
        sidebar_gradient = self.create_gradient_background()
        sidebar = sidebar_gradient[:, :SIDEBAR_WIDTH]
        
        # Apply sidebar gradient
        try:
            overlay[:, :SIDEBAR_WIDTH] = sidebar
        except ValueError as e:
            print(f"Warning: Could not apply sidebar gradient. Frame size: {overlay.shape}, Sidebar size: {sidebar.shape}")
            # Fallback: Use solid color for sidebar
            overlay[:, :SIDEBAR_WIDTH] = BACKGROUND_COLOR
        
        # Draw current time
        self._draw_current_time(overlay)
        
        # Draw menu items
        self._draw_menu_items(overlay, cursor_x, cursor_y)
        
        # Draw current song info
        self._draw_current_song(overlay, current_song)
        
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

    def _draw_current_song(self, overlay, current_song):
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
                
            is_hovered = cursor_y is not None and item_y - 25 < cursor_y < item_y + 25
            if is_hovered:
                cv2.rectangle(overlay, 
                            (content_x - 20, item_y - 30),
                            (self.frame_width - CONTENT_PADDING, item_y + 20),
                            HOVER_COLOR, -1)
            
            title_color = ACCENT_COLOR if is_hovered else TEXT_COLOR
            cv2.putText(overlay, song.title, (content_x, item_y), 
                       font, 1.0, title_color, 2, cv2.LINE_AA)
            
            cv2.putText(overlay, song.artist, (content_x + 400, item_y),
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