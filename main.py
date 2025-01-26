import cv2
from config import *
from gesture.detector import GestureDetector
from ui.renderer import UIRenderer
from models.song import Song

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
        # Check menu items
        menu_start_y = 120
        for i, item in enumerate(menu_items):
            y_pos = menu_start_y + i * MENU_ITEM_SPACING
            if cursor_y is not None and abs(cursor_y - y_pos) < 20 and cursor_x < SIDEBAR_WIDTH:
                print(f"Clicked: {item}")
                return True, current_song

        # Check playlist items
        content_x = SIDEBAR_WIDTH + CONTENT_PADDING
        content_y = TOP_BAR_HEIGHT + CONTENT_PADDING - int(vertical_scroll_pos)
        
        for i, song in enumerate(playlist_songs):
            item_y = content_y + 100 + i * SONG_ITEM_HEIGHT
            
            if item_y < TOP_BAR_HEIGHT or item_y > CAMERA_HEIGHT:
                continue
            
            # Oynat butonu kontrolü
            play_x = content_x + 30
            play_y = item_y
            if (play_x - 40 <= cursor_x <= play_x + 40 and 
                play_y - 20 <= cursor_y <= play_y + 20):
                print(f"Play clicked for: {song.title}")
                try:
                    # Eğer aynı şarkı çalıyorsa hiçbir şey yapma
                    if current_song and current_song.title == song.title and current_song.is_playing:
                        return True, current_song
                    # Eğer aynı şarkı duraklatılmışsa devam ettir
                    elif current_song and current_song.title == song.title and not current_song.is_playing:
                        current_song.unpause()
                        return True, current_song
                    # Değilse yeni şarkı çal
                    else:
                        if current_song:
                            current_song.stop()
                        song.play()
                        return True, song
                except Exception as e:
                    print(f"Şarkı çalma hatası: {e}")
                    return True, current_song

            # Durdur butonu kontrolü
            pause_x = content_x + 130
            pause_y = item_y
            if (pause_x - 40 <= cursor_x <= pause_x + 40 and 
                pause_y - 20 <= cursor_y <= pause_y + 20):
                print(f"Pause clicked for: {song.title}")
                try:
                    if current_song and current_song.title == song.title:
                        current_song.pause()
                    return True, current_song
                except Exception as e:
                    print(f"Şarkı durdurma hatası: {e}")
                    return True, current_song
        
        return False, current_song
    except Exception as e:
        print(f"Etkileşim hatası: {e}")
        return False, current_song

def main():
    # Spotify API bilgilerini ayarla
    CLIENT_ID = "e13c91eec5c247bbb35658d7b1ef21d5"
    CLIENT_SECRET = "12e2414d5e0344d4afeb406ca03e285d"
    
    # Spotify API'sini başlat
    Song.initialize_spotify(CLIENT_ID, CLIENT_SECRET)
    
    # Test için birkaç şarkı ara
    songs = Song.search_songs("Metallica", limit=5)  # Metallica şarkıları
    print("\nBulunan şarkılar:")
    for song in songs:
        print(f"Şarkı: {song.title} - Sanatçı: {song.artist}")
    
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
    
    print(f"Actual camera resolution: {actual_width}x{actual_height}")
    
    # Create window
    cv2.namedWindow("Modern Music Player", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Modern Music Player", actual_width, actual_height)
    fullscreen = False

    # Initialize components with actual resolution
    current_song = None  # Başlangıçta çalan şarkı yok
    playlist_songs = songs  # Arama sonuçlarını playlist olarak kullan

    # Initialize state
    vertical_scroll_pos = 0
    prev_cursor_x, prev_cursor_y = -1, -1

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

                # İmleç pozisyonunu al
                cursor_x, cursor_y = detector.get_finger_cursor(hand_landmark, actual_width, actual_height)
                
                # Pinch pozisyonunu al (tıklama için)
                pinch_x, pinch_y = detector.get_pinch_position(hand_landmark, actual_width, actual_height)
                
                # Scroll kontrolü
                scroll_gesture_active = detector.is_scroll_gesture(hand_landmark)

            overlay = frame.copy()
            is_clicking = False

            # İmleç görüntüleme ve scroll işlemleri
            if cursor_x != -1 and cursor_y != -1:
                if scroll_gesture_active:
                    vertical_scroll_pos = update_scroll_positions(cursor_y, prev_cursor_y, 
                                                               scroll_gesture_active, vertical_scroll_pos)
            
            # Pinch (tıklama) kontrolü - imleçten bağımsız
            if pinch_x is not None and pinch_y is not None:
                is_clicking = True
                clicked, current_song = handle_interactions(pinch_x, pinch_y, renderer.menu_items, 
                                                         playlist_songs, vertical_scroll_pos, current_song)
                
            renderer.draw_modern_ui(overlay, cursor_x, cursor_y, vertical_scroll_pos, 
                                     current_song, playlist_songs, is_clicking)

            prev_cursor_x, prev_cursor_y = cursor_x, cursor_y

            cv2.imshow("Modern Music Player", overlay)
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