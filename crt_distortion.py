import cv2
import numpy as np

# 카메라 설정
CAM = 0
WIDTH = 640
HEIGHT = 480

cap = cv2.VideoCapture(CAM)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

mode = 1  # 기본 모드
scan_line = 0

print("===== CRT INTERACTION MODES =====")
print("1 : CRT Distortion (손 움직임 기반 찌그러짐)")
print("2 : Horizontal Scanner (위→아래)")
print("3 : Vertical Scanner (좌→우)")
print("q : 종료")
print("=================================")

# 밝기 변화 추적용
prev_gray = None

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # -------------------------
    # MODE 1 : Distortion
    # -------------------------
    if mode == 1:
        if prev_gray is None:
            prev_gray = gray.copy()

        # 밝기 변화 = 움직임(손/얼굴)
        diff = cv2.absdiff(gray, prev_gray)
        _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        # 모션 많은 영역을 흐릿하게 흔들기 위한 blur mask
        motion_mask_blur = cv2.GaussianBlur(motion_mask, (25, 25), 0)

        # 화면 전체 살짝 지글지글한 wave effect
        rows, cols = gray.shape
        x = np.arange(cols)
        y = np.arange(rows)
        x_grid, y_grid = np.meshgrid(x, y)

        # 파동 생성
        sin_wave = (np.sin(y_grid / 12.0) * 2).astype(np.float32)

        map_x = (x_grid + sin_wave).astype(np.float32)
        map_y = y_grid.astype(np.float32)

        distorted = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)

        # motion 영역만 더 움직이게 distortion 강화
        motion_mask_color = cv2.cvtColor(motion_mask_blur, cv2.COLOR_GRAY2BGR)
        output = cv2.addWeighted(frame, 0.6, distorted, 0.4, 0)
        output = np.where(motion_mask_color > 10, distorted, output)

        prev_gray = gray.copy()

    # -------------------------
    # MODE 2 : Horizontal Scanner
    # -------------------------
    elif mode == 2:
        output = np.zeros_like(frame)
        scan_line = (scan_line + 5) % HEIGHT
        output[:scan_line, :] = frame[:scan_line, :]

        # 스캔 라인 강조 (CRT 느낌)
        cv2.line(output, (0, scan_line), (cols, scan_line), (255, 255, 255), 1)

    # -------------------------
    # MODE 3 : Vertical Scanner
    # -------------------------
    elif mode == 3:
        output = np.zeros_like(frame)
        scan_line = (scan_line + 5) % WIDTH
        output[:, :scan_line] = frame[:, :scan_line]

        # 스캔 라인 강조
        cv2.line(output, (scan_line, 0), (scan_line, rows), (255, 255, 255), 1)

    # -------------------------
    # default fallback
    # -------------------------
    else:
        output = frame

    cv2.imshow("CRT Interaction", output)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('1'):
        print("→ CRT Distortion mode")
        mode = 1
    elif key == ord('2'):
        print("→ Horizontal Scanner mode")
        mode = 2
        scan_line = 0
    elif key == ord('3'):
        print("→ Vertical Scanner mode")
        mode = 3
        scan_line = 0
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
