import cv2
import numpy as np
import mediapipe as mp
import time

# ===== 기본 설정 =====
CAM = 0
WIDTH = 640
HEIGHT = 480

cap = cv2.VideoCapture(CAM)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

mode = 1        # 1: 거리기반 왜곡, 2: 왜곡+스캐너, 3: MediaPipe 손 왜곡
scan_line = 0
prev_gray = None

# MediaPipe Hands 설정 (모드 3용)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    model_complexity=0,          # 가벼운 모델
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

print("===== CRT INTERACTION MODES =====")
print("1 : Distance-based Distortion (가까울수록 화면 더 찌그러짐)")
print("2 : Distortion + Scanner (왜곡 + 스캔라인 합성)")
print("3 : MediaPipe Hand Distortion (손 주변만 찌그러짐)")
print("q : 종료")
print("=================================")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    rows, cols, _ = frame.shape
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 공통용 좌표 그리드
    x = np.arange(cols)
    y = np.arange(rows)
    x_grid, y_grid = np.meshgrid(x, y)

    # ======================================
    # MODE 1: 거리 기반 왜곡 (motion area로 거리 추정)
    # ======================================
    if mode in (1, 2):
        global_distorted = frame.copy()

        if prev_gray is None:
            prev_gray = gray.copy()

        diff = cv2.absdiff(gray, prev_gray)
        _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        # 가장 큰 컨투어 = 사람이 제일 많이 움직인 영역
        contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_area = 0
        if contours:
            max_area = max(cv2.contourArea(c) for c in contours)

        # 화면 전체 대비로 정규화 → 0 ~ 1
        # 가까울수록 화면에 차지하는 비율↑ → distortion 강도↑ 라는 가정
        norm_area = max_area / float(rows * cols)
        distortion_strength = np.clip(norm_area * 4.0, 0.0, 1.0)  # 조금 과하게 스케일

        # base_amplitude: 항상 있는 기본 물결, extra_amplitude: 거리 기반
        base_amp = 1.0
        extra_amp = 5.0 * distortion_strength  # 가까우면 최대 +5px 정도 요동
        amplitude = base_amp + extra_amp

        # 수평 방향으로 물결 발생
        # y축에 따라 sin파 생성, amplitude로 스케일
        sin_wave = (np.sin(y_grid / 12.0) * amplitude).astype(np.float32)

        map_x = (x_grid + sin_wave).astype(np.float32)
        map_y = y_grid.astype(np.float32)

        global_distorted = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)

    # ======================================
    # MODE 1: 결과 만들기 (왜곡만)
    # ======================================
    if mode == 1:
        # motion이 적으면 원본에 가깝게, 많으면 왜곡 반영
        alpha = 0.6 + 0.4 * distortion_strength  # 0.6 ~ 1.0
        output = cv2.addWeighted(frame, 1.0 - alpha, global_distorted, alpha, 0)

    # ======================================
    # MODE 2: 왜곡 + 스캐너 합성
    # ======================================
    elif mode == 2:
        # 먼저 왜곡된 화면 준비 (global_distorted)
        # 그 다음 스캔라인 방식으로 위에서 아래로 채워 넣기
        output = np.zeros_like(frame)
        scan_line = (scan_line + 5) % rows
        output[:scan_line, :] = global_distorted[:scan_line, :]

        # 스캔 라인 강조 (흰색 선)
        cv2.line(output, (0, scan_line), (cols, scan_line), (255, 255, 255), 1)

    # ======================================
    # MODE 3: MediaPipe 손 위치 기반 왜곡
    # ======================================
    elif mode == 3:
        # MediaPipe로 손 landmark 추출
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            # 손의 중심점 (평균)
            cx = 0.0
            cy = 0.0
            for lm in hand.landmark:
                cx += lm.x
                cy += lm.y
            cx /= len(hand.landmark)
            cy /= len(hand.landmark)

            cx_px = int(cx * cols)
            cy_px = int(cy * rows)

            # 손 주변만 radial 왜곡
            dx = x_grid - cx_px
            dy = y_grid - cy_px
            dist = np.sqrt(dx ** 2 + dy ** 2)

            # 손에서 멀어질수록 영향 감소하는 가우시안 마스크
            sigma = 150.0
            hand_mask = np.exp(-(dist ** 2) / (2 * sigma ** 2)).astype(np.float32)

            # 손 주변에서만 radial wave
            wavelength = 30.0
            time_phase = time.time() * 3.0

            radial_wave = np.sin(dist / wavelength - time_phase)

            # 손이 카메라에 가까울수록 z값이 작아짐 (일반적으로)
            # landmark 0의 z값을 사용해서 강도 조절
            z_val = hand.landmark[0].z  # 대략 -0.1 ~ 0.1 근처
            z_strength = np.clip(-z_val * 10.0, 0.0, 1.5)  # 카메라 가까울수록 강하게

            amp = 8.0 * z_strength
            disp = radial_wave * amp * hand_mask

            # x 방향으로만 왜곡
            map_x = (x_grid + disp).astype(np.float32)
            map_y = y_grid.astype(np.float32)

            distorted = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)

            # 손 주변은 왜곡, 그 외는 원본
            hand_mask_3 = cv2.merge([hand_mask, hand_mask, hand_mask])
            output = (distorted * hand_mask_3 + frame * (1 - hand_mask_3)).astype(np.uint8)
        else:
            # 손이 안 보이면 그냥 원본
            output = frame

    else:
        output = frame

    cv2.imshow("CRT Interaction Advanced", output)

    # prev_gray는 모드 1, 2에서만 갱신
    if mode in (1, 2):
        prev_gray = gray.copy()

    key = cv2.waitKey(1) & 0xFF
    if key == ord('1'):
        print("→ MODE 1: Distance-based Distortion")
        mode = 1
        prev_gray = None
    elif key == ord('2'):
        print("→ MODE 2: Distortion + Scanner")
        mode = 2
        scan_line = 0
        prev_gray = None
    elif key == ord('3'):
        print("→ MODE 3: MediaPipe Hand Distortion")
        mode = 3
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
