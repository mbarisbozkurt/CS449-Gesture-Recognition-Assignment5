import cv2
from config import *
from gesture.detector import GestureDetector
from ui.renderer import UIRenderer
from models.song import Song
import os
from dotenv import load_dotenv
import time

def update_scroll_positions(cursor_y, prev_cursor_y, scroll_gesture_active, vertical_scroll_pos):
    if scroll_gesture_active and prev_cursor_y != -1 and cursor_y != -1:
        delta_y = cursor_y - prev_cursor_y
        
        if abs(delta_y) > MOVEMENT_THRESHOLD:
            sensitivity = SCROLL_SENSITIVITY
            scroll_amount = (delta_y / abs(delta_y)) * (abs(delta_y) - MOVEMENT_THRESHOLD) * sensitivity
            scroll_amount = round(scroll_amount / 10) * 10
            
            return int(max(0, min(vertical_scroll_pos + scroll_amount, CAMERA_HEIGHT * 2)))
    return vertical_scroll_pos

def handle_interactions(cursor_x, cursor_y, menu_items, playlist_songs, vertical_scroll_pos, current_song):
    try:
        # Adjust cursor_x to be relative to the UI side
        if cursor_x > CAMERA_WIDTH:
            cursor_x = cursor_x - CAMERA_WIDTH

        # Check playlist items
        content_x = SIDEBAR_WIDTH + CONTENT_PADDING
        content_y = TOP_BAR_HEIGHT + CONTENT_PADDING + 100 - int(vertical_scroll_pos)  # Yeni başlangıç pozisyonu
        
        for i, song in enumerate(playlist_songs):
            item_y = content_y + 120 + i * SONG_ITEM_HEIGHT  # Yeni şarkı pozisyonu hesaplaması
            
            if item_y < TOP_BAR_HEIGHT or item_y > CAMERA_HEIGHT:
                continue
            
            # Play button control - genişletilmiş ve düzeltilmiş tıklama alanı
            play_x = content_x + 40
            play_y = item_y
            play_hit_box = 45  # Tıklama alanını biraz daha genişlettik
            
            if (play_x - play_hit_box <= cursor_x <= play_x + play_hit_box and 
                play_y - play_hit_box <= cursor_y <= play_y + play_hit_box):
                try:
                    # If same song is playing, do nothing
                    if current_song and current_song.title == song.title and current_song.is_playing:
                        return True, current_song
                    # If same song is paused, resume
                    elif current_song and current_song.title == song.title and not current_song.is_playing:
                        if current_song.unpause():
                            current_song.is_playing = True
                        return True, current_song
                    # Otherwise play new song
                    else:
                        if current_song:
                            current_song.stop()
                            current_song.is_playing = False
                        if song.play():
                            song.is_playing = True
                            return True, song
                        return True, current_song
                except Exception as e:
                    print(f"Song playback error: {e}")
                    return True, current_song

            # Pause button control - genişletilmiş ve düzeltilmiş tıklama alanı
            pause_x = content_x + 130
            pause_y = item_y
            pause_hit_box = 45  # Tıklama alanını biraz daha genişlettik
            
            if (pause_x - pause_hit_box <= cursor_x <= pause_x + pause_hit_box and 
                pause_y - pause_hit_box <= cursor_y <= pause_y + pause_hit_box):
                try:
                    if current_song and current_song.title == song.title:
                        if current_song.pause():
                            current_song.is_playing = False
                    return True, current_song
                except Exception as e:
                    print(f"Song pause error: {e}")
                    return True, current_song
        
        return False, current_song
    except Exception as e:
        print(f"Interaction error: {e}")
        return False, current_song

def main():
    # Load environment variables
    load_dotenv()
    
    # Spotify API bilgilerini çevresel değişkenlerden al
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Hata: Spotify API bilgileri bulunamadı. Lütfen .env dosyasını kontrol edin.")
        return
    
    # Spotify API'sini başlat
    Song.initialize_spotify(CLIENT_ID, CLIENT_SECRET)
    
    # Playlist'i yükle
    playlist_songs = Song.get_playlist()
    
    # Renderer ve GestureDetector'ı başlat
    renderer = UIRenderer(CAMERA_WIDTH, CAMERA_HEIGHT)
    detector = GestureDetector()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    # Try to set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    
    # Get actual camera resolution
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Create window with double width for split view
    cv2.namedWindow("Modern Music Player", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Modern Music Player", actual_width * 2, actual_height)
    fullscreen = False

    # Initialize components with actual resolution
    current_song = None  # Başlangıçta çalan şarkı yok

    # Initialize state
    vertical_scroll_pos = 0
    prev_cursor_x, prev_cursor_y = -1, -1
    
    # Spotify durumu kontrolü için zamanlayıcı
    last_spotify_check = 0
    SPOTIFY_CHECK_INTERVAL = 1.0  # Her 1 saniyede bir kontrol et

    # Ana döngü
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            result = detector.process_frame(frame)

            # Başlangıç değerlerini tanımla
            cursor_x, cursor_y = -1, -1
            pinch_x, pinch_y = None, None
            scroll_gesture_active = False

            if result.multi_hand_landmarks:
                hand_landmark = result.multi_hand_landmarks[0]
                detector.draw_landmarks(frame, hand_landmark)

                # Get cursor position from camera view (left side)
                cursor_x, cursor_y = detector.get_finger_cursor(hand_landmark, actual_width, actual_height)
                if cursor_x != -1 and cursor_y != -1:
                    # Scale coordinates to match the UI dimensions
                    cursor_x = int(cursor_x * (CAMERA_WIDTH / actual_width))
                    cursor_y = int(cursor_y * (CAMERA_HEIGHT / actual_height))
                    
                    # Map the cursor from left side to right side
                    ui_cursor_x = CAMERA_WIDTH + cursor_x  # Add CAMERA_WIDTH to move to right side
                    
                    # For UI interactions, use the mapped coordinates
                    cursor_x = ui_cursor_x
                
                # Get pinch position from camera view (left side)
                pinch_x, pinch_y = detector.get_pinch_position(hand_landmark, actual_width, actual_height)
                if pinch_x is not None and pinch_y is not None:
                    # Scale coordinates to match the UI dimensions
                    pinch_x = int(pinch_x * (CAMERA_WIDTH / actual_width))
                    pinch_y = int(pinch_y * (CAMERA_HEIGHT / actual_height))
                    
                    # Map the pinch from left side to right side
                    ui_pinch_x = CAMERA_WIDTH + pinch_x  # Add CAMERA_WIDTH to move to right side
                    
                    # For UI interactions, use the mapped coordinates
                    pinch_x = ui_pinch_x
                
                # Scroll gesture detection
                scroll_gesture_active = detector.is_scroll_gesture(hand_landmark)

            # Draw the UI with both camera feed and interface
            canvas = renderer.draw_modern_ui(frame, cursor_x, cursor_y, vertical_scroll_pos, 
                                          current_song, playlist_songs, pinch_x is not None)

            # İmleç görüntüleme ve scroll işlemleri
            if cursor_x != -1 and cursor_y != -1:
                if scroll_gesture_active:
                    vertical_scroll_pos = update_scroll_positions(cursor_y, prev_cursor_y, 
                                                               scroll_gesture_active, vertical_scroll_pos)
            
            # Şarkı durumunu belirli aralıklarla güncelle
            current_time = time.time()
            if current_song and (current_time - last_spotify_check) >= SPOTIFY_CHECK_INTERVAL:
                try:
                    current_playback = Song.spotify.current_playback()
                    if current_playback and current_playback['item']:
                        current_song.is_playing = current_playback['is_playing']
                        current_song.progress = current_playback['progress_ms'] / current_playback['item']['duration_ms']
                    else:
                        current_song.is_playing = False
                except Exception as e:
                    print(f"Spotify playback error: {e}")
                last_spotify_check = current_time
            
            # Pinch (tıklama) kontrolü - imleçten bağımsız
            if pinch_x is not None and pinch_y is not None:
                clicked, current_song = handle_interactions(pinch_x, pinch_y, renderer.menu_items, 
                                                         playlist_songs, vertical_scroll_pos, current_song)

            prev_cursor_x, prev_cursor_y = cursor_x, cursor_y

            cv2.imshow("Modern Music Player", canvas)
            key = cv2.waitKey(1)
            if key == ord("q"):
                break
            elif key == ord("f"):
                fullscreen = not fullscreen
                if fullscreen:
                    cv2.setWindowProperty("Modern Music Player", cv2.WND_PROP_FULLSCREEN, 
                                        cv2.WINDOW_FULLSCREEN)
                else:
                    cv2.setWindowProperty("Modern Music Player", cv2.WND_PROP_FULLSCREEN, 
                                        cv2.WINDOW_NORMAL)
    except KeyboardInterrupt:
        print("\nUygulama kapatılıyor...")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 