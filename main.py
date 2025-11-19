import pygame
import cv2
import sys
import numpy as np

def main():
    """
    Main function to run the webcam display application.
    """
    # --- Pygame Initialization ---
    pygame.init()

    # Get display info to set up a fullscreen window
    try:
        display_info = pygame.display.Info()
        screen_width, screen_height = display_info.current_w, display_info.current_h
    except pygame.error:
        # Fallback for environments without a full display server
        screen_width, screen_height = 800, 600

    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Live Webcam Feed")
    pygame.mouse.set_visible(False) # Hide the cursor

    # --- OpenCV Webcam Initialization ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.", file=sys.stderr)
        pygame.quit()
        return

    webcam_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    webcam_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # --- Scaling Logic to maintain aspect ratio ---
    webcam_aspect_ratio = webcam_width / webcam_height
    screen_aspect_ratio = screen_width / screen_height

    if webcam_aspect_ratio > screen_aspect_ratio:
        # Webcam is wider, fit to screen width (letterbox top/bottom)
        scaled_width = screen_width
        scaled_height = int(screen_width / webcam_aspect_ratio)
    else:
        # Webcam is taller, fit to screen height (pillarbox left/right)
        scaled_height = screen_height
        scaled_width = int(screen_height * webcam_aspect_ratio)

    # Calculate position to center the feed
    pos_x = (screen_width - scaled_width) // 2
    pos_y = (screen_height - scaled_height) // 2

    # --- Main Loop ---
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- Frame Capture and Processing ---
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.", file=sys.stderr)
            running = False
            continue

        # 1. Flip horizontally for a mirror effect
        frame = cv2.flip(frame, 1)

        # 2. Convert from BGR (OpenCV) to RGB (Pygame)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 3. Create Pygame surface from the numpy array.
        #    Using frombuffer is more efficient.
        webcam_surface = pygame.image.frombuffer(
            frame_rgb.tobytes(), (webcam_width, webcam_height), "RGB"
        )

        # --- Drawing to the Screen ---
        # 1. Scale the webcam surface to fit the screen
        scaled_surface = pygame.transform.scale(webcam_surface, (scaled_width, scaled_height))
        
        # 2. Fill the background with black
        screen.fill((0, 0, 0))
        
        # 3. Blit the scaled surface onto the screen at the centered position
        screen.blit(scaled_surface, (pos_x, pos_y))

        # 4. Update the display
        pygame.display.flip()

    # --- Cleanup ---
    cap.release()
    pygame.quit()
    print("Application closed.")

if __name__ == '__main__':
    main()
