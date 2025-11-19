import pygame
import random
import math
import sys

# ----------------------------
# 설정
# ----------------------------
WIDTH, HEIGHT = 640, 480  # CRT 느낌 해상도
FULLSCREEN = True  # 개발할 땐 False, 설치할 땐 True 추천
TEXT = "3DOWON"

BG_COLOR = (5, 10, 15)  # 어두운 남색 계열 배경 (빈티지 모니터 느낌)

# ----------------------------
# 초기화
# ----------------------------
pygame.init()
flags = pygame.FULLSCREEN if FULLSCREEN else 0
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.display.set_caption("3DOWON CRT Vintage")

clock = pygame.time.Clock()

# 폰트 (없는 경우를 대비해서 기본 폰트 사용)
font_size = 72
font = pygame.font.SysFont("Courier", font_size, bold=True)


# ----------------------------
# 3D처럼 보이는 텍스트 만들기
# ----------------------------
def create_extruded_text(text, color, depth=8):
    """
    단일 색 텍스트에 두꺼운 그림자를 겹쳐서 가짜 3D 효과.
    """
    base = font.render(text, True, color)
    w, h = base.get_size()
    surf = pygame.Surface((w + depth, h + depth), pygame.SRCALPHA)

    # 어두운 그림자 색
    shadow_color = (int(color[0] * 0.2), int(color[1] * 0.2), int(color[2] * 0.2))
    shadow = font.render(text, True, shadow_color)

    # 깊이만큼 뒤로 밀린 그림자 여러 번 그리기
    for i in range(depth):
        surf.blit(shadow, (i + 1, i + 1))

    # 맨 위에 실제 텍스트
    surf.blit(base, (0, 0))
    return surf


# 메인 텍스트를 RGB로 약간씩 어긋나게 그려서 빈티지 색 번짐 느낌
text_red = create_extruded_text(TEXT, (255, 80, 80))
text_green = create_extruded_text(TEXT, (120, 255, 120))
text_blue = create_extruded_text(TEXT, (120, 160, 255))

TEXT_W, TEXT_H = text_red.get_size()

# ----------------------------
# CRT 스캔라인 / 비네트 오버레이 만들기
# ----------------------------
scanline_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for y in range(0, HEIGHT, 2):
    # 반투명 검은 줄
    pygame.draw.line(scanline_surface, (0, 0, 0, 60), (0, y), (WIDTH, y))

vignette_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
center_x, center_y = WIDTH / 2, HEIGHT / 2
max_dist = math.sqrt(center_x**2 + center_y**2)
for y in range(HEIGHT):
    for x in range(WIDTH):
        dx = x - center_x
        dy = y - center_y
        dist = math.sqrt(dx * dx + dy * dy)
        # 바깥으로 갈수록 어두워지는 비네트
        alpha = int(120 * (dist / max_dist) ** 1.5)  # 곡선감 조정
        if alpha > 0:
            vignette_surface.set_at((x, y), (0, 0, 0, min(alpha, 180)))


# ----------------------------
# 텍스트 움직임 설정
# ----------------------------
x, y = WIDTH / 2, HEIGHT / 2
vx = random.choice([-1, 1]) * 80  # px/sec
vy = random.choice([-1, 1]) * 60


# 약간의 랜덤 흔들림 (브라운관 느낌)
def jitter():
    return random.randint(-1, 1)


# ----------------------------
# 메인 루프
# ----------------------------
def main():
    global x, y, vx, vy

    running = True
    last_time = pygame.time.get_ticks() / 1000.0

    while running:
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        last_time = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # ESC로 종료
                if event.key == pygame.K_ESCAPE:
                    running = False

        # ------------------------
        # 텍스트 위치 업데이트 (벽 튕기기)
        # ------------------------
        x += vx * dt
        y += vy * dt

        # 텍스트가 화면 바깥으로 나가지 않게 튕김
        if x - TEXT_W / 2 < 20:
            x = 20 + TEXT_W / 2
            vx *= -1
        elif x + TEXT_W / 2 > WIDTH - 20:
            x = WIDTH - 20 - TEXT_W / 2
            vx *= -1

        if y - TEXT_H / 2 < 20:
            y = 20 + TEXT_H / 2
            vy *= -1
        elif y + TEXT_H / 2 > HEIGHT - 20:
            y = HEIGHT - 20 - TEXT_H / 2
            vy *= -1

        # 배경 + 약간의 밝기 깜빡임
        flicker = random.randint(-3, 3)
        bg = (
            max(0, min(255, BG_COLOR[0] + flicker)),
            max(0, min(255, BG_COLOR[1] + flicker)),
            max(0, min(255, BG_COLOR[2] + flicker)),
        )
        screen.fill(bg)

        # ------------------------
        # 텍스트 그리기 (RGB 약간 어긋나게)
        # ------------------------
        base_pos = (int(x), int(y))

        # 가벼운 흔들림
        jx, jy = jitter(), jitter()
        cx, cy = base_pos[0] + jx, base_pos[1] + jy

        # Blue (왼쪽 살짝)
        rect_b = text_blue.get_rect(center=(cx - 2, cy))
        screen.blit(text_blue, rect_b)

        # Red (오른쪽 살짝)
        rect_r = text_red.get_rect(center=(cx + 2, cy))
        screen.blit(text_red, rect_r)

        # Green (중앙)
        rect_g = text_green.get_rect(center=(cx, cy))
        screen.blit(text_green, rect_g)

        # ------------------------
        # CRT 효과 오버레이
        # ------------------------
        screen.blit(scanline_surface, (0, 0))
        screen.blit(vignette_surface, (0, 0))

        pygame.display.flip()
        clock.tick(60)  # 최대 60fps

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
