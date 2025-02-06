import cv2
import mediapipe as mp
import math
import numpy as np
from config import *

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_face = mp.solutions.face_detection
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_hands=1
        )
        self.face_detection = self.mp_face.FaceDetection(
            min_detection_confidence=0.5
        )
        # İmleç yumuşatma için önceki pozisyonları sakla
        self.prev_cursor_x = None
        self.prev_cursor_y = None
        self.smoothing_factor = 0.5  # Yumuşatma faktörü (0-1 arası)

    def process_frame(self, frame):
        # Create a copy of the frame for blurring
        blurred = cv2.GaussianBlur(frame, (55, 55), 0)
        
        # Process the frame for face and hand detection
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hand_results = self.hands.process(rgb_frame)
        face_results = self.face_detection.process(rgb_frame)
        
        # Create a mask for the face and hands
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        # Add face to mask if detected
        if face_results.detections:
            for detection in face_results.detections:
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, _ = frame.shape
                x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                            int(bboxC.width * iw), int(bboxC.height * ih)
                # Make the face region slightly larger
                padding = 20
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(iw - x, w + 2*padding)
                h = min(ih - y, h + 2*padding)
                cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        
        # Add hands to mask if detected
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                # Get hand bounding box
                x_coords = [landmark.x for landmark in hand_landmarks.landmark]
                y_coords = [landmark.y for landmark in hand_landmarks.landmark]
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                ih, iw, _ = frame.shape
                x1 = max(0, int((x_min - 0.1) * iw))
                y1 = max(0, int((y_min - 0.1) * ih))
                x2 = min(iw, int((x_max + 0.1) * iw))
                y2 = min(ih, int((y_max + 0.1) * ih))
                
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
        
        # Blur mask edges
        mask = cv2.GaussianBlur(mask, (21, 21), 11)
        
        # Normalize mask to [0, 1]
        mask = mask.astype(float) / 255
        
        # Stack mask for 3 channels
        mask = np.stack([mask] * 3, axis=-1)
        
        # Combine original and blurred frames using the mask
        result_frame = frame * mask + blurred * (1 - mask)
        result_frame = result_frame.astype(np.uint8)
        
        return hand_results, result_frame

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