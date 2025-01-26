import cv2
import mediapipe as mp
import math
from config import *

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_hands=1
        )
        # İmleç yumuşatma için önceki pozisyonları sakla
        self.prev_cursor_x = None
        self.prev_cursor_y = None
        self.smoothing_factor = 0.5  # Yumuşatma faktörü (0-1 arası)

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb_frame)

    def draw_landmarks(self, frame, hand_landmarks):
        self.mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_draw.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=4),
            self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2)
        )

    def is_finger_extended(self, hand_landmark, finger_tip_id, finger_pip_id):
        return hand_landmark.landmark[finger_tip_id].y < hand_landmark.landmark[finger_pip_id].y

    def get_hand_orientation(self, hand_landmark):
        wrist = hand_landmark.landmark[self.mp_hands.HandLandmark.WRIST]
        index_mcp = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        pinky_mcp = hand_landmark.landmark[self.mp_hands.HandLandmark.PINKY_MCP]
        
        vertical_orientation = "neutral"
        if wrist.y < index_mcp.y and wrist.y < pinky_mcp.y and pinky_mcp.x < wrist.x:
            vertical_orientation = "up"
        elif wrist.y > index_mcp.y and wrist.y > pinky_mcp.y and pinky_mcp.x < wrist.x:
            vertical_orientation = "down"
        
        return vertical_orientation

    def is_scroll_gesture(self, hand_landmark):
        index_extended = self.is_finger_extended(hand_landmark, self.mp_hands.HandLandmark.INDEX_FINGER_TIP, 
                                               self.mp_hands.HandLandmark.INDEX_FINGER_PIP)
        middle_extended = self.is_finger_extended(hand_landmark, self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                                                self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP)
        ring_extended = self.is_finger_extended(hand_landmark, self.mp_hands.HandLandmark.RING_FINGER_TIP,
                                              self.mp_hands.HandLandmark.RING_FINGER_PIP)
        pinky_extended = self.is_finger_extended(hand_landmark, self.mp_hands.HandLandmark.PINKY_TIP,
                                               self.mp_hands.HandLandmark.PINKY_PIP)

        if index_extended and middle_extended and not ring_extended and not pinky_extended:
            index_tip = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_tip = hand_landmark.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            
            finger_distance = math.hypot(index_tip.x - middle_tip.x, index_tip.y - middle_tip.y)
            return finger_distance < 0.1
        
        return False

    def is_pinch_gesture(self, hand_landmark):
        # İşaret ve başparmak uçlarının konumlarını al
        thumb_tip = hand_landmark.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        # İki parmak arasındaki mesafeyi 2 boyutlu olarak hesapla (x ve y)
        distance = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5
        
        return distance < 0.045  # Daha rahat kullanım için threshold değeri artırıldı

    def get_pinch_position(self, hand_landmark, frame_width, frame_height):
        # İşaret parmağı ve başparmak uçlarının konumlarını al
        thumb_tip = hand_landmark.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        # Pinch pozisyonunu iki parmağın ortası olarak hesapla
        pinch_x = int((thumb_tip.x + index_tip.x) / 2 * frame_width)
        pinch_y = int((thumb_tip.y + index_tip.y) / 2 * frame_height)
        
        # İki parmak arasındaki mesafeyi 2 boyutlu olarak hesapla
        distance = ((thumb_tip.x - index_tip.x) ** 2 + (thumb_tip.y - index_tip.y) ** 2) ** 0.5
        
        if distance < 0.045:  # Daha rahat kullanım için threshold değeri artırıldı
            return pinch_x, pinch_y
        return None, None

    def get_finger_cursor(self, hand_landmark, frame_width, frame_height):
        index_tip = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        
        # Yeni pozisyonu hesapla
        new_x = int(index_tip.x * frame_width)
        new_y = int(index_tip.y * frame_height)
        
        # Eğer önceki pozisyon varsa yumuşatma uygula
        if self.prev_cursor_x is not None and self.prev_cursor_y is not None:
            cursor_x = int(self.prev_cursor_x + (new_x - self.prev_cursor_x) * self.smoothing_factor)
            cursor_y = int(self.prev_cursor_y + (new_y - self.prev_cursor_y) * self.smoothing_factor)
        else:
            cursor_x = new_x
            cursor_y = new_y
        
        # Yeni pozisyonu sakla
        self.prev_cursor_x = cursor_x
        self.prev_cursor_y = cursor_y
        
        return cursor_x, cursor_y 