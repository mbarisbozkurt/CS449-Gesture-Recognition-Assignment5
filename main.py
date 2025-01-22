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

def handle_interactions(cursor_x, cursor_y, menu_items, playlist_songs, vertical_scroll_pos):
    # Check menu items
    menu_start_y = 120
    for i, item in enumerate(menu_items):
        y_pos = menu_start_y + i * MENU_ITEM_SPACING
        if cursor_y is not None and abs(cursor_y - y_pos) < 20 and cursor_x < SIDEBAR_WIDTH:
            print(f"Clicked: {item}")
            return True
    
    # Check playlist items
    content_x = SIDEBAR_WIDTH + CONTENT_PADDING
    content_y = TOP_BAR_HEIGHT + CONTENT_PADDING - int(vertical_scroll_pos)
    
    for i, song in enumerate(playlist_songs):
        item_y = content_y + 100 + i * SONG_ITEM_HEIGHT
        
        if item_y < TOP_BAR_HEIGHT or item_y > CAMERA_HEIGHT:
            continue
            
        if cursor_y is not None and item_y - 25 < cursor_y < item_y + 25:
            if content_x - 20 <= cursor_x <= CAMERA_WIDTH - CONTENT_PADDING:
                print(f"Selected song: {song.title}")
                return True
    
    return False

def main():
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
    gesture_detector = GestureDetector()
    ui_renderer = UIRenderer(actual_width, actual_height)
    current_song = Song.get_current_song()
    playlist_songs = Song.get_playlist()

    # Initialize state
    vertical_scroll_pos = 0
    prev_cursor_x, prev_cursor_y = -1, -1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        result = gesture_detector.process_frame(frame)

        cursor_x, cursor_y = -1, -1
        scroll_gesture_active = False

        if result.multi_hand_landmarks:
            hand_landmark = result.multi_hand_landmarks[0]
            gesture_detector.draw_landmarks(frame, hand_landmark)

            cursor_x, cursor_y = gesture_detector.get_finger_cursor(hand_landmark, actual_width, actual_height)
            scroll_gesture_active = gesture_detector.is_scroll_gesture(hand_landmark)

        overlay = frame.copy()
        is_clicking = False

        if cursor_x != -1 and cursor_y != -1:
            if scroll_gesture_active:
                vertical_scroll_pos = update_scroll_positions(cursor_y, prev_cursor_y, 
                                                           scroll_gesture_active, vertical_scroll_pos)
            else:
                is_clicking = handle_interactions(cursor_x, cursor_y, ui_renderer.menu_items, 
                                               playlist_songs, vertical_scroll_pos)
            
        ui_renderer.draw_modern_ui(overlay, cursor_x, cursor_y, vertical_scroll_pos, 
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

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 