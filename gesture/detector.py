import cv2
import mediapipe as mp
import math
from config import *

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
            max_num_hands=MAX_NUM_HANDS
        )

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

    def get_finger_cursor(self, hand_landmark, frame_width, frame_height):
        index_tip = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        index_mcp = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        wrist = hand_landmark.landmark[self.mp_hands.HandLandmark.WRIST]
        
        index_extended = self.is_finger_extended(hand_landmark, self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
                                               self.mp_hands.HandLandmark.INDEX_FINGER_PIP)
        pip_extended = hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_PIP].y < \
                      hand_landmark.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_MCP].y
        
        if index_extended and pip_extended and index_tip.y < wrist.y:
            cursor_x = int((index_tip.x * 0.5 + index_pip.x * 0.3 + index_mcp.x * 0.2) * frame_width)
            cursor_y = int((index_tip.y * 0.5 + index_pip.y * 0.3 + index_mcp.y * 0.2) * frame_height)
            return cursor_x, cursor_y
        return -1, -1 