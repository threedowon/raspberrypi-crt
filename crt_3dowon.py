import pygame
import random
import math
import sys
import socket
import threading

# ----------------------------
# 설정
# ----------------------------
WIDTH, HEIGHT = 640, 480
FULLSCREEN = True
TEXT = "3DOWON"
BG_COLOR = (5, 10, 15)

# UDP 설정
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

# ----------------------------
# UDP 수신 스레드
# ----------------------------
latest_color = (120, 255, 120)  # 기본 3DOWON 초록색


def udp_listener():
    global latest_color
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"[UDP] Listening on {UDP_IP}:{UDP_PORT}")

    while True:
        data, _ = sock.recvfrom(1024)
        msg = data.decode().strip()

        if msg.startswith("#") and len(msg) == 7:
            try:
                r = int(msg[1:3], 16)
                g = int(msg[3:5], 16)
                b = int(msg[5:7], 16)
                latest_color = (r, g, b)
                print(f"[UDP] Color updated → {latest_color}")
            except:
                print("[UDP] Invalid HEX")
                continue


# 스레드 시작
udp_thread = threading.Thread(target=udp_listener, daemon=True)
udp_thread.start()

# ----------------------------
# pygame 초기화
# ----------------------------
pygame.init()
flags = pygame.FULLSCREEN if FULLSCREEN else 0
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
clock = pygame.time.Clock()
pygame.display.set_caption("3DOWON CRT Vintage")

font = pygame.font.SysFont("Courier", 72, bold=True)


# ----------------------------
# 텍스트 생성 함수 (3D 효과)
# ----------------------------
def create_extruded_text(text, base_color, depth=7):
    base = font.render(text, True, base_color)
    w, h = base.get_size()
    surf = pygame.Surface((w + depth, h + depth), pygame.SRCALPHA)

    # 그림자
    shadow_color = (
        int(base_color[0] * 0.2),
        int(base_color[1] * 0.2),
        int(base_color[2] * 0.2),
    )
    shadow = font.render(text, True, shadow_color)

    for i in range(depth):
        surf.blit(shadow, (i + 1, i + 1))

    surf.blit(base, (0, 0))
    return surf


# ----------------------------
# CRT 스캔라인 / 비네트
# ----------------------------
scan = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for y in range(0, HEIGHT, 2):
    pygame.draw.line(scan, (0, 0, 0, 60), (0, y), (WIDTH, y))

vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
cx, cy = WIDTH / 2, HEIGHT / 2
max_dist = math.sqrt(cx * cx + cy * cy)

for y in range(HEIGHT):
    for x in range(WIDTH):
        dist = math.dist((x, y), (cx, cy))
        alpha = int(140 * (dist / max_dist) ** 1.8)
        if alpha > 0:
            vignette.set_at((x, y), (0, 0, 0, min(180, alpha)))


# ----------------------------
# 텍스트 움직임
# ----------------------------
x, y = WIDTH / 2, HEIGHT / 2
vx = random.choice([-1, 1]) * 80
vy = random.choice([-1, 1]) * 60


def jitter():
    return random.randint(-1, 1)


# ----------------------------
# 메인 루프
# ----------------------------
def main():
    global x, y, vx, vy, latest_color

    # 최초 텍스트 생성
    text_surf = create_extruded_text(TEXT, latest_color)
    TEXT_W, TEXT_H = text_surf.get_size()

    last_color = latest_color
    last_time = pygame.time.get_ticks() / 1000

    running = True

    while running:
        now = pygame.time.get_ticks() / 1000
        dt = now - last_time
        last_time = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # 🔥 색이 바뀌면 텍스트 다시 생성
        if latest_color != last_color:
            text_surf = create_extruded_text(TEXT, latest_color)
            TEXT_W, TEXT_H = text_surf.get_size()
            last_color = latest_color

        # ---------------- 이동 ----------------
        x += vx * dt
        y += vy * dt

        if x - TEXT_W / 2 < 20:
            x = 20 + TEXT_W / 2
            vx *= -1
        if x + TEXT_W / 2 > WIDTH - 20:
            x = WIDTH - 20 - TEXT_W / 2
            vx *= -1

        if y - TEXT_H / 2 < 20:
            y = 20 + TEXT_H / 2
            vy *= -1
        if y + TEXT_H / 2 > HEIGHT - 20:
            y = HEIGHT - 20 - TEXT_H / 2
            vy *= -1

        # ---------------- 렌더링 ----------------
        flicker = random.randint(-3, 3)
        bg = (
            max(0, min(255, BG_COLOR[0] + flicker)),
            max(0, min(255, BG_COLOR[1] + flicker)),
            max(0, min(255, BG_COLOR[2] + flicker)),
        )
        screen.fill(bg)

        # 텍스트 위치 + 흔들림
        cx, cy = int(x) + jitter(), int(y) + jitter()
        rect_t = text_surf.get_rect(center=(cx, cy))
        screen.blit(text_surf, rect_t)

        # CRT 효과
        screen.blit(scan, (0, 0))
        screen.blit(vignette, (0, 0))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
