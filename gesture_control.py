import cv2
import mediapipe as mp
import math
import textwrap

# MediaPipe 
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8)

# Kamera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

cv2.namedWindow("Gesture Control", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Gesture Control", 960, 540)
fullscreen = False

frame_width = 1280
frame_height = 720

# Scrollbar özellikleri
scrollbar_thickness = 60
scrollbar_length = 500

horizontal_scroll_pos = 0
vertical_scroll_pos = 0
horizontal_max_scroll = frame_width - scrollbar_length
vertical_max_scroll = frame_height - scrollbar_length

bar_height = 100
bar_color = (0, 0, 0)
alpha_bar = 0.5

# Stage kontrolü: 1 = Butonlar var, 2 = Suggested songs UI + geri butonu
ui_stage = 1

# Stage 1 butonlar
button_texts = ["Play", "Pause", "Next", "Prev", "Vol +", "Vol -"]
base_colors = [
    (0, 120, 255),
    (0, 255, 0),
    (255, 0, 0),
    (255, 255, 0),
    (128, 0, 255),
    (255, 128, 0)
]

button_radius = 40
spacing = 50
button_count = len(button_texts)
total_buttons_width = button_count * (button_radius*2) + (button_count-1)*spacing
start_x = (frame_width - total_buttons_width) // 2
bar_y = (frame_height - bar_height) // 2

buttons = []
for i, text in enumerate(button_texts):
    cx = start_x + (button_radius + i * (2 * button_radius + spacing))
    cy = bar_y + bar_height // 2
    base_color = base_colors[i % len(base_colors)]
    buttons.append({"cx": cx, "cy": cy, "r": button_radius, "text": text, "base_color": base_color})

clicked_button_text = None

# Stage 2 için içerikler
song_titles = [f"Song {i+1} - Awesome Track {i+1}" for i in range(50)]
line_height = 50

long_text = """\
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed feugiat nulla a enim venenatis, ac placerat magna dignissim. Praesent id quam felis. Curabitur vestibulum elit sed nunc hendrerit semper. Aliquam erat volutpat. Suspendisse potenti. Morbi vitae tincidunt ante. Quisque pharetra volutpat magna, vel laoreet ipsum maximus in. Vestibulum dictum lorem ut elementum rhoncus. Nulla facilisi. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.

Donec congue, urna non eleifend blandit, ante risus condimentum metus, non dignissim eros metus sit amet sapien. Nam vel ultricies eros, a ullamcorper elit. Suspendisse vehicula, odio sed posuere aliquam, magna nisi maximus augue, vitae ultrices metus urna nec justo. Vivamus id volutpat nunc, et finibus libero. Etiam maximus nunc vitae pretium efficitur. Vivamus congue risus vel tellus blandit vehicula. Donec metus neque, sollicitudin sit amet purus ac, efficitur vehicula felis. Nulla vulputate vel elit mollis gravida.

Sed facilisis arcu id mauris tristique, at tincidunt lectus viverra. Nullam interdum urna leo, vitae vestibulum velit tristique eu. Proin mattis felis et sapien vestibulum, eget porttitor metus facilisis. Duis ut lectus et urna bibendum molestie vitae non sem. Etiam dapibus id augue in facilisis. Nullam porta blandit sapien, id ultricies nulla mollis a. Fusce ullamcorper, magna eget scelerisque gravida, nunc tortor suscipit massa, sit amet efficitur mi sapien eu risus. Aenean porttitor accumsan nulla, ac viverra nisl venenatis quis. Aliquam porttitor semper metus, quis suscipit velit.
""".strip()

wrapped_text = textwrap.wrap(long_text, width=80)
content_height = 200 + len(song_titles)*line_height + len(wrapped_text)*40

back_button = {
    "cx": frame_width // 2 + 300,
    "cy": 60,
    "r": 40,
    "text": "Back",
    "base_color": (0, 128, 255)  
}

def draw_circle_button(overlay, button, cursor_x, cursor_y, pinch_detected):
    cx, cy, r = button["cx"], button["cy"], button["r"]
    text = button["text"]
    base_color = button["base_color"]

    dist = math.hypot(cursor_x - cx, cursor_y - cy)
    hovered = dist < r
    clicked = hovered and pinch_detected

    if clicked:
        color = (min(base_color[0]+80, 255), min(base_color[1]+80, 255), min(base_color[2]+80, 255))
        cv2.circle(overlay, (cx, cy), r+15, (0, 255, 255), 4)  
    elif hovered:
        color = (min(base_color[0]+50, 255), min(base_color[1]+50, 255), min(base_color[2]+50, 255))
        cv2.circle(overlay, (cx, cy), r+10, (255, 255, 255), 2)  
    else:
        color = base_color

    cv2.circle(overlay, (cx, cy), r, color, -1)

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    text_size = cv2.getTextSize(text, font, font_scale, 2)[0]
    text_x = cx - text_size[0] // 2
    text_y = cy + text_size[1] // 2
    cv2.putText(overlay, text, (text_x, text_y), font, font_scale, (255, 255, 255), 2, cv2.LINE_AA)

    return clicked, text

def draw_scrollbars(frame, horiz_pos, vert_pos, horizontal_selected, vertical_selected, scroll_gesture_active):
    cv2.rectangle(
        frame,
        (horiz_pos, frame_height - scrollbar_thickness),
        (horiz_pos + scrollbar_length, frame_height),
        (0, 255, 0),
        -1,
    )

    cv2.rectangle(
        frame,
        (frame_width - scrollbar_thickness, vert_pos),
        (frame_width, vert_pos + scrollbar_length),
        (255, 0, 0),
        -1,
    )

    if horizontal_selected:
        thickness = 2 if not scroll_gesture_active else 4
        color = (255, 255, 255) if not scroll_gesture_active else (0, 255, 255)
        cv2.rectangle(
            frame,
            (horiz_pos, frame_height - scrollbar_thickness),
            (horiz_pos + scrollbar_length, frame_height),
            color,
            thickness
        )

    if vertical_selected:
        thickness = 2 if not scroll_gesture_active else 4
        color = (255, 255, 255) if not scroll_gesture_active else (0, 255, 255)
        cv2.rectangle(
            frame,
            (frame_width - scrollbar_thickness, vert_pos),
            (frame_width, vert_pos + scrollbar_length),
            color,
            thickness
        )

def update_scroll_positions(cursor_x, cursor_y, prev_cursor_x, prev_cursor_y, horizontal_selected, vertical_selected):
    global horizontal_scroll_pos, vertical_scroll_pos

    if horizontal_selected:
        delta_x = cursor_x - prev_cursor_x
        horizontal_scroll_pos = max(0, min(horizontal_scroll_pos + delta_x, horizontal_max_scroll))

    if vertical_selected:
        delta_y = cursor_y - prev_cursor_y
        vertical_scroll_pos = max(0, min(vertical_scroll_pos + delta_y, vertical_max_scroll))

def is_scroll_gesture(hand_landmark):
    index_tip = hand_landmark.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    middle_tip = hand_landmark.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    dist = math.hypot(index_tip.x - middle_tip.x, index_tip.y - middle_tip.y)
    return dist < 0.05

prev_cursor_x, prev_cursor_y = -1, -1
scroll_gesture_active = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    cursor_x, cursor_y = -1, -1
    pinch_detected = False
    scroll_gesture_active = False

    if result.multi_hand_landmarks:
        for hand_landmark in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmark,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=4),
                mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
            )

            index_tip = hand_landmark.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmark.landmark[mp_hands.HandLandmark.THUMB_TIP]

            cursor_x = int(index_tip.x * frame.shape[1])
            cursor_y = int(index_tip.y * frame.shape[0])

            distance = math.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)
            if distance < 0.05:
                pinch_detected = True

            if is_scroll_gesture(hand_landmark):
                scroll_gesture_active = True

    overlay = frame.copy()

    horizontal_selected = False
    vertical_selected = False

    if ui_stage == 1:
        bar_overlay = overlay.copy()
        cv2.rectangle(bar_overlay, (0, bar_y), (frame_width, bar_y + bar_height), bar_color, -1)
        cv2.addWeighted(bar_overlay, alpha_bar, overlay, 1 - alpha_bar, 0, overlay)

        clicked_button = None
        for btn in buttons:
            clicked, text = draw_circle_button(overlay, btn, cursor_x, cursor_y, pinch_detected)
            if clicked:
                clicked_button = text

        if clicked_button:
            clicked_button_text = clicked_button
            if clicked_button == "Next":
                ui_stage = 2
                vertical_scroll_pos = 0
                horizontal_scroll_pos = 0

        if cursor_x != -1 and cursor_y != -1:
            if (frame_height - scrollbar_thickness <= cursor_y <= frame_height) and \
               (horizontal_scroll_pos <= cursor_x <= horizontal_scroll_pos + scrollbar_length):
                horizontal_selected = True

            if (frame_width - scrollbar_thickness <= cursor_x <= frame_width) and \
               (vertical_scroll_pos <= cursor_y <= vertical_scroll_pos + scrollbar_length):
                vertical_selected = True

            if scroll_gesture_active and (horizontal_selected or vertical_selected):
                if prev_cursor_x != -1 and prev_cursor_y != -1:
                    update_scroll_positions(cursor_x, cursor_y, prev_cursor_x, prev_cursor_y, horizontal_selected, vertical_selected)

            cv2.circle(overlay, (cursor_x, cursor_y), 10, (255, 255, 0), -1)

        draw_scrollbars(overlay, horizontal_scroll_pos, vertical_scroll_pos, horizontal_selected, vertical_selected, scroll_gesture_active)

        if clicked_button_text:
            font = cv2.FONT_HERSHEY_SIMPLEX
            msg = f"{clicked_button_text} Clicked!"
            text_size = cv2.getTextSize(msg, font, 1, 2)[0]
            msg_x = (frame_width - text_size[0]) // 2
            msg_y = 100
            cv2.putText(overlay, msg, (msg_x, msg_y), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

    else:
        clicked_back, _ = draw_circle_button(overlay, back_button, cursor_x, cursor_y, pinch_detected)
        if clicked_back:
            ui_stage = 1
            vertical_scroll_pos = 0
            horizontal_scroll_pos = 0

        font = cv2.FONT_HERSHEY_SIMPLEX
        title = "Suggested songs:"
        title_size = cv2.getTextSize(title, font, 1.2, 2)[0]
        title_x = (frame_width - title_size[0]) // 2
        title_y = 100
        cv2.putText(overlay, title, (title_x, title_y), font, 1.2, (255, 255, 0), 2, cv2.LINE_AA)

        y_start = 200 - vertical_scroll_pos
        for i, song in enumerate(song_titles):
            song_y = y_start + i * line_height
            if song_y > frame_height or (song_y + line_height < 0):
                continue
            cv2.putText(overlay, song, (100, song_y), font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)

        text_start_y = y_start + len(song_titles)*line_height + 100
        for j, line in enumerate(wrapped_text):
            line_y = text_start_y + j*40
            if line_y > frame_height or (line_y + 40 < 0):
                continue
            cv2.putText(overlay, line, (100, line_y), font, 1.0, (200, 200, 200), 2, cv2.LINE_AA)

        if cursor_x != -1 and cursor_y != -1:
            if (frame_height - scrollbar_thickness <= cursor_y <= frame_height) and \
               (horizontal_scroll_pos <= cursor_x <= horizontal_scroll_pos + scrollbar_length):
                horizontal_selected = True

            if (frame_width - scrollbar_thickness <= cursor_x <= frame_width) and \
               (vertical_scroll_pos <= cursor_y <= vertical_scroll_pos + scrollbar_length):
                vertical_selected = True

            if scroll_gesture_active and (horizontal_selected or vertical_selected):
                if prev_cursor_x != -1 and prev_cursor_y != -1:
                    update_scroll_positions(cursor_x, cursor_y, prev_cursor_x, prev_cursor_y, horizontal_selected, vertical_selected)

            cv2.circle(overlay, (cursor_x, cursor_y), 10, (255, 255, 0), -1)

        draw_scrollbars(overlay, horizontal_scroll_pos, vertical_scroll_pos, horizontal_selected, vertical_selected, scroll_gesture_active)

    prev_cursor_x, prev_cursor_y = cursor_x, cursor_y

    cv2.imshow("Gesture Control", overlay)
    key = cv2.waitKey(1)
    if key == ord("q"):
        break
    elif key == ord("f"):
        fullscreen = not fullscreen
        if fullscreen:
            cv2.setWindowProperty("Gesture Control", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty("Gesture Control", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

cap.release()
cv2.destroyAllWindows()
