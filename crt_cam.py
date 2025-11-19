import pygame
import cv2
import sys
import numpy as np

# --- 사용자 설정 ---
# 웹캠 영상이 표시될 사각형의 위치와 크기를 여기서 조절하세요.
# (배경 이미지에 맞게 이 값들을 변경해야 합니다)
WEBCAM_POS_X = 150
WEBCAM_POS_Y = 100
WEBCAM_WIDTH = 500
WEBCAM_HEIGHT = 375
# -----------------

def main():
    """
    Main function to run the 2.5D room webcam display.
    """
    pygame.init()

    try:
        display_info = pygame.display.Info()
        screen_width, screen_height = display_info.current_w, display_info.current_h
    except pygame.error:
        screen_width, screen_height = 800, 600

    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("2.5D Room Webcam")
    pygame.mouse.set_visible(False)
    
    # --- Load Room Background Image ---
    try:
        background_image = pygame.image.load("room_background.png").convert()
        background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
        has_background = True
    except pygame.error:
        print("Warning: 'room_background.png' not found. Displaying on black background.", file=sys.stderr)
        has_background = False

    # --- OpenCV Webcam Initialization ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.", file=sys.stderr)
        pygame.quit()
        return

    # --- Main Loop ---
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.", file=sys.stderr)
            running = False
            continue

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # OpenCV 프레임을 Pygame Surface로 변환
        webcam_surface = pygame.surfarray.make_surface(np.rot90(frame_rgb))
        
        # 설정된 크기로 웹캠 영상 스케일링
        scaled_webcam = pygame.transform.scale(webcam_surface, (WEBCAM_WIDTH, WEBCAM_HEIGHT))
        
        # --- Drawing to the Screen ---
        # 1. 배경 그리기
        if has_background:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((0, 0, 0)) # 배경이 없으면 검은색으로 채움

        # 2. 배경 위에 웹캠 영상 그리기
        screen.blit(scaled_webcam, (WEBCAM_POS_X, WEBCAM_POS_Y))

        # 3. 화면 업데이트
        pygame.display.flip()
        clock.tick(30) # Limit frame rate for performance on Raspberry Pi

    # --- Cleanup ---
    cap.release()
    pygame.quit()
    print("Application closed.")

if __name__ == '__main__':
    main()
