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

    def draw_modern_ui(self, frame, cursor_x, cursor_y, scroll_pos, current_song, playlist_songs, is_clicking=False):
        # Create a larger canvas to hold both camera feed and UI
        canvas = np.zeros((self.frame_height, self.frame_width * 2, 3), np.uint8)
        
        # Create a darker gradient background for the UI part
        gradient_bg = np.zeros((self.frame_height, self.frame_width, 3), np.uint8)
        for i in range(self.frame_height):
            value = int(12 + (i/self.frame_height)*8)  # Darker gradient
            gradient_bg[i] = [value, value, value]

        # Resize camera frame to match canvas dimensions
        resized_frame = cv2.resize(frame, (self.frame_width, self.frame_height))

        # Place camera feed on the left side
        canvas[:, :self.frame_width] = resized_frame

        # Place UI on the right side with a modern dark theme
        canvas[:, self.frame_width:] = gradient_bg

        # Create and resize sidebar with a slightly lighter gradient
        sidebar_gradient = np.zeros((self.frame_height, SIDEBAR_WIDTH, 3), np.uint8)
        for i in range(self.frame_height):
            value = int(15 + (i/self.frame_height)*10)
            sidebar_gradient[i] = [value, value, value]
        
        # Apply sidebar gradient with a subtle border
        canvas[:, self.frame_width:self.frame_width + SIDEBAR_WIDTH] = sidebar_gradient
        cv2.line(canvas, 
                (self.frame_width + SIDEBAR_WIDTH, 0), 
                (self.frame_width + SIDEBAR_WIDTH, self.frame_height), 
                (30, 30, 30), 2)

        # Draw a subtle top bar
        cv2.rectangle(canvas, 
                     (self.frame_width, 0), 
                     (self.frame_width * 2, TOP_BAR_HEIGHT), 
                     (20, 20, 20), -1)
        cv2.line(canvas, 
                (self.frame_width, TOP_BAR_HEIGHT), 
                (self.frame_width * 2, TOP_BAR_HEIGHT), 
                (30, 30, 30), 2)

        # Adjust cursor coordinates for the UI part if cursor is on the right side
        ui_cursor_x = cursor_x
        if cursor_x > self.frame_width:
            ui_cursor_x = cursor_x - self.frame_width

        # Draw UI elements on the right side
        self._draw_current_time(canvas, self.frame_width)
        
        # Draw Now Playing text at the top with enhanced styling
        if current_song:
            font = cv2.FONT_HERSHEY_SIMPLEX
            if current_song.is_playing:
                status_text = f"Now Playing: {current_song.title} - {current_song.artist}"
            else:
                status_text = f"Paused: {current_song.title} - {current_song.artist}"
            
            text_y = TOP_BAR_HEIGHT//2 + 10
            
            # Enhanced text shadow
            cv2.putText(canvas, status_text,
                       (self.frame_width + SIDEBAR_WIDTH + CONTENT_PADDING + 2, text_y + 2),
                       font, 1.0, (0, 0, 0), 4, cv2.LINE_AA)
            
            # Brighter main text
            cv2.putText(canvas, status_text,
                       (self.frame_width + SIDEBAR_WIDTH + CONTENT_PADDING, text_y),
                       font, 1.0, (*ACCENT_COLOR, 255) if current_song.is_playing else (*TEXT_COLOR_SECONDARY, 255), 2, cv2.LINE_AA)

        # Draw menu items, current song, and playlist with adjusted x coordinates
        self._draw_menu_items(canvas, ui_cursor_x, cursor_y, self.frame_width)
        self._draw_current_song(canvas, current_song, ui_cursor_x, cursor_y, self.frame_width)
        self._draw_playlist(canvas, ui_cursor_x, cursor_y, scroll_pos, playlist_songs, self.frame_width, current_song)
        
        # Draw cursor on both sides with enhanced visual
        if cursor_x != -1 and cursor_y != -1:
            # Draw cursor on camera feed side
            cv2.circle(canvas, (cursor_x, cursor_y), 22, (*CURSOR_OUTLINE_COLOR, 150), 2)  # Outer ring
            cursor_color = (0, 255, 0) if is_clicking else ACCENT_COLOR
            cv2.circle(canvas, (cursor_x, cursor_y), 18, (*cursor_color, 200), -1)  # Main circle
            cv2.circle(canvas, (cursor_x, cursor_y), 12, (*cursor_color, 255), -1)  # Inner circle

        return canvas

    def _draw_current_time(self, overlay, ui_offset):
        current_time = datetime.now().strftime("%H:%M")
        font = cv2.FONT_HERSHEY_SIMPLEX
        time_size = cv2.getTextSize(current_time, font, 1.2, 2)[0]
        cv2.putText(overlay, current_time, 
                   (ui_offset + self.frame_width - time_size[0] - 60, TOP_BAR_HEIGHT//2 + 12),
                   font, 1.2, TEXT_COLOR, 2, cv2.LINE_AA)

    def _draw_menu_items(self, overlay, cursor_x, cursor_y, ui_offset):
        font = cv2.FONT_HERSHEY_SIMPLEX
        menu_start_y = 120
        
        for i, item in enumerate(self.menu_items):
            y_pos = menu_start_y + i * MENU_ITEM_SPACING
            is_hovered = cursor_y is not None and abs(cursor_y - y_pos) < 20 and cursor_x < SIDEBAR_WIDTH
            
            if is_hovered:
                cv2.rectangle(overlay, (ui_offset + 20, y_pos - 25), (ui_offset + SIDEBAR_WIDTH - 20, y_pos + 15),
                            HOVER_COLOR, -1)
                color = ACCENT_COLOR
            else:
                color = TEXT_COLOR

            cv2.putText(overlay, item, (ui_offset + 40, y_pos), font, 1.0, color, 2, cv2.LINE_AA)

    def _draw_current_song(self, overlay, current_song, cursor_x, cursor_y, ui_offset):
        # Sol alttaki kontrol butonlarını kaldırdık, bu fonksiyon artık boş
        pass

    def _draw_playlist(self, overlay, cursor_x, cursor_y, scroll_pos, playlist_songs, ui_offset, current_song=None):
        font = cv2.FONT_HERSHEY_SIMPLEX
        content_x = ui_offset + SIDEBAR_WIDTH + CONTENT_PADDING
        content_y = TOP_BAR_HEIGHT + CONTENT_PADDING + 100 - int(scroll_pos)  # 50'den 100'e çıkardık - daha aşağıda başlayacak
        
        # Draw header with enhanced styling
        header_text = "Your Playlist"
        # Draw header background
        cv2.rectangle(overlay, 
                     (content_x - 40, content_y - 40),
                     (ui_offset + self.frame_width - CONTENT_PADDING, content_y + 40),
                     (20, 20, 20), -1)
        # Draw header text with enhanced shadow
        cv2.putText(overlay, header_text, (content_x + 3, content_y + 3), 
                    font, 2.0, (0, 0, 0), 5, cv2.LINE_AA)
        cv2.putText(overlay, header_text, (content_x, content_y), 
                    font, 2.0, (*TEXT_COLOR, 255), 3, cv2.LINE_AA)
        
        # Draw songs with enhanced styling
        last_item_y = 0  # Son şarkının y pozisyonunu takip etmek için
        for i, song in enumerate(playlist_songs):
            item_y = content_y + 120 + i * SONG_ITEM_HEIGHT  # 100'den 120'ye çıkardık - şarkılar arası mesafe artacak
            last_item_y = item_y  # Son şarkının pozisyonunu güncelle
            
            if item_y < TOP_BAR_HEIGHT or item_y > self.frame_height:
                continue
                
            is_hovered = cursor_y is not None and item_y - 40 < cursor_y < item_y + 40
            if is_hovered:
                # Enhanced hover effect
                cv2.rectangle(overlay, 
                            (content_x - 40, item_y - 45),
                            (ui_offset + self.frame_width - CONTENT_PADDING, item_y + 45),
                            (*HOVER_COLOR, 100), -1)
                cv2.rectangle(overlay, 
                            (content_x - 40, item_y - 45),
                            (ui_offset + self.frame_width - CONTENT_PADDING, item_y + 45),
                            (*HOVER_COLOR, 150), 2)
            
            # Enhanced play button
            play_x = content_x + 40
            play_y = item_y
            
            # Play button background with gradient effect
            cv2.circle(overlay, (play_x, play_y), 35, 
                      (*HOVER_COLOR, 150) if hasattr(song, 'is_playing') and song.is_playing else (30, 30, 30), -1)
            cv2.circle(overlay, (play_x, play_y), 35, (*ACCENT_COLOR, 255), 2)
            
            # Enhanced play triangle
            triangle_size = 25
            pts = np.array([
                [play_x - triangle_size//2, play_y - triangle_size],
                [play_x - triangle_size//2, play_y + triangle_size],
                [play_x + triangle_size, play_y]
            ], np.int32)
            cv2.fillPoly(overlay, [pts], (*TEXT_COLOR, 255))

            # Enhanced pause button
            pause_x = content_x + 130
            pause_y = item_y
            
            cv2.circle(overlay, (pause_x, pause_y), 35, 
                      (*HOVER_COLOR, 150) if hasattr(song, 'is_playing') and song.is_playing else (30, 30, 30), -1)
            cv2.circle(overlay, (pause_x, pause_y), 35, (*ACCENT_COLOR, 255), 2)
            
            # Enhanced pause bars
            bar_width = 8
            bar_height = 30
            cv2.rectangle(overlay, 
                         (pause_x - bar_width - 6, pause_y - bar_height//2),
                         (pause_x - 6, pause_y + bar_height//2),
                         (*TEXT_COLOR, 255), -1)
            cv2.rectangle(overlay, 
                         (pause_x + 6, pause_y - bar_height//2),
                         (pause_x + bar_width + 6, pause_y + bar_height//2),
                         (*TEXT_COLOR, 255), -1)
            
            # Enhanced song title and artist text
            title_color = ACCENT_COLOR if is_hovered else TEXT_COLOR
            # Title shadow
            cv2.putText(overlay, song.title, (content_x + 202, item_y + 2), 
                       font, 1.0, (0, 0, 0), 3, cv2.LINE_AA)
            # Title text
            cv2.putText(overlay, song.title, (content_x + 200, item_y), 
                       font, 1.0, (*title_color, 255), 2, cv2.LINE_AA)
            
            # Artist shadow
            cv2.putText(overlay, song.artist, (content_x + 652, item_y + 2),
                       font, 0.9, (0, 0, 0), 3, cv2.LINE_AA)
            # Artist text
            cv2.putText(overlay, song.artist, (content_x + 650, item_y),
                       font, 0.9, (*TEXT_COLOR_SECONDARY, 255), 2, cv2.LINE_AA)
            
            # Duration with shadow
            duration_x = ui_offset + self.frame_width - 120
            cv2.putText(overlay, song.duration, (duration_x + 2, item_y + 2),
                       font, 0.9, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(overlay, song.duration, (duration_x, item_y),
                       font, 0.9, (*TEXT_COLOR_SECONDARY, 255), 2, cv2.LINE_AA)

        # Draw progress bar below the last song
        if current_song and current_song.is_playing:
            progress_y = last_item_y + 180  # 150'den 180'e çıkardık - progress bar daha aşağıda olacak
            
            # Draw song info above progress bar with larger font
            font = cv2.FONT_HERSHEY_SIMPLEX
            info_y = progress_y - 30  # 25'ten 30'a çıkardık - metin ile bar arası mesafe artacak
            
            # Song title and artist with shadow - daha büyük font
            song_info = f"{current_song.title} - {current_song.artist}"
            # Shadow
            cv2.putText(overlay, song_info,
                       (content_x - 38, info_y + 2),
                       font, 0.9, (0, 0, 0), 3, cv2.LINE_AA)
            # Main text
            cv2.putText(overlay, song_info,
                       (content_x - 40, info_y),
                       font, 0.9, TEXT_COLOR, 2, cv2.LINE_AA)
            
            # Duration with shadow - daha büyük font
            duration_text = current_song.duration
            text_size = cv2.getTextSize(duration_text, font, 0.9, 2)[0]
            # Shadow
            cv2.putText(overlay, duration_text,
                       (ui_offset + self.frame_width - CONTENT_PADDING - text_size[0] + 2, info_y + 2),
                       font, 0.9, (0, 0, 0), 3, cv2.LINE_AA)
            # Main text
            cv2.putText(overlay, duration_text,
                       (ui_offset + self.frame_width - CONTENT_PADDING - text_size[0], info_y),
                       font, 0.9, TEXT_COLOR, 2, cv2.LINE_AA)
            
            # Progress bar background with padding
            progress_height = 5
            cv2.rectangle(overlay,
                         (content_x - 40, progress_y),
                         (ui_offset + self.frame_width - CONTENT_PADDING, progress_y + progress_height),
                         (30, 30, 30), -1)
            
            # Progress bar fill
            progress_width = int((self.frame_width - SIDEBAR_WIDTH - CONTENT_PADDING * 2) * current_song.progress)
            if progress_width > 0:
                cv2.rectangle(overlay,
                            (content_x - 40, progress_y),
                            (content_x - 40 + progress_width, progress_y + progress_height),
                            ACCENT_COLOR, -1) 