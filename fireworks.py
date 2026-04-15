import pygame
import random
import math
import sys
import os

pygame.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Happy Birthday Fireworks")
clock = pygame.time.Clock()

def get_chinese_font(size):
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("arial", size)

def random_color():
    h = random.randint(0, 360)
    s = random.uniform(0.7, 1.0)
    v = random.uniform(0.8, 1.0)
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:    r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return (int((r+m)*255), int((g+m)*255), int((b+m)*255))

def golden_color():
    return random.choice([(255,215,0),(255,200,50),(255,180,30),(255,230,100),(255,190,60)])

def pink_color():
    return random.choice([(255,105,180),(255,130,200),(255,80,160),(255,150,210),(255,100,190)])


class Particle:
    def __init__(self, x, y, color, speed, angle, size=3, life=60, gravity=0.06, fade=True, trail=True):
        self.x = x
        self.y = y
        self.color = color
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity
        self.fade = fade
        self.trail = trail
        self.trail_points = []
        self.alive = True

    def update(self):
        if self.trail:
            self.trail_points.append((self.x, self.y))
            if len(self.trail_points) > 10:
                self.trail_points.pop(0)
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.99
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        alpha = self.life / self.max_life if self.fade else 1.0
        r = int(self.color[0] * alpha)
        g = int(self.color[1] * alpha)
        b = int(self.color[2] * alpha)
        color = (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))
        if self.trail and len(self.trail_points) > 1:
            for i, pos in enumerate(self.trail_points):
                t_alpha = (i / len(self.trail_points)) * alpha
                tr = int(self.color[0] * t_alpha * 0.6)
                tg = int(self.color[1] * t_alpha * 0.6)
                tb = int(self.color[2] * t_alpha * 0.6)
                t_color = (max(0,min(255,tr)), max(0,min(255,tg)), max(0,min(255,tb)))
                t_size = max(1, int(self.size * t_alpha * 0.5))
                pygame.draw.circle(surface, t_color, (int(pos[0]), int(pos[1])), t_size)
        current_size = max(1, int(self.size * alpha))
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), current_size)
        if current_size > 1:
            glow = (max(0,min(255,r//3)), max(0,min(255,g//3)), max(0,min(255,b//3)))
            pygame.draw.circle(surface, glow, (int(self.x), int(self.y)), current_size * 3)


class TextBurstFirework:
    """文字烟花 - 从底部发射火箭，到达高空后爆炸成文字形状的粒子"""
    def __init__(self, text, center_x, center_y, color_func, delay, font_size=180):
        self.text = text
        self.center_x = center_x
        self.center_y = center_y
        self.color_func = color_func
        self.delay = delay
        self.font_size = font_size

        # 火箭参数
        self.rocket_x = center_x + random.randint(-20, 20)
        self.rocket_y = HEIGHT + 20
        self.rocket_speed = random.uniform(12, 16)
        self.rocket_trail = []
        self.rocket_sparks = []
        self.rocket_color = random.choice([(255,220,150),(255,200,100),(255,255,200)])

        # 爆炸粒子
        self.text_particles = []
        self.debris_particles = []

        # 预计算文字点
        self.text_points = []
        self._precompute_text_points()

        # wait -> rising -> explode_flash -> forming -> hold -> scatter -> dead
        self.phase = "wait"
        self.phase_timer = 0
        self.flash_alpha = 0
        self.alive = True

    def _precompute_text_points(self):
        font = get_chinese_font(self.font_size)
        surf = font.render(self.text, True, (255,255,255))
        w, h = surf.get_size()
        start_x = self.center_x - w // 2
        start_y = self.center_y - h // 2
        step = 3
        for px in range(0, w, step):
            for py in range(0, h, step):
                if px < surf.get_width() and py < surf.get_height():
                    if surf.get_at((px, py))[3] > 128:
                        self.text_points.append((start_x + px, start_y + py))

    def update(self):
        if self.phase == "wait":
            self.delay -= 1
            if self.delay <= 0:
                self.phase = "rising"

        elif self.phase == "rising":
            self.rocket_y -= self.rocket_speed
            self.rocket_speed *= 0.996

            # 拖尾
            self.rocket_trail.append((self.rocket_x, self.rocket_y))
            if len(self.rocket_trail) > 25:
                self.rocket_trail.pop(0)

            # 尾部火星 - 大量密集
            for _ in range(5):
                sx = self.rocket_x + random.uniform(-4, 4)
                sy = self.rocket_y + random.uniform(5, 20)
                self.rocket_sparks.append({
                    "x": sx, "y": sy,
                    "vx": random.uniform(-1.2, 1.2),
                    "vy": random.uniform(0.5, 3),
                    "color": random.choice([(255,220,150),(255,200,100),(255,180,80),(255,255,200),(255,160,50)]),
                    "life": random.randint(8, 25),
                    "max_life": 25,
                    "size": random.uniform(1, 3),
                })

            for s in self.rocket_sparks:
                s["x"] += s["vx"]
                s["y"] += s["vy"]
                s["vy"] += 0.03
                s["life"] -= 1
            self.rocket_sparks = [s for s in self.rocket_sparks if s["life"] > 0]

            # 到达目标
            if self.rocket_y <= self.center_y:
                self.phase = "explode_flash"
                self.phase_timer = 0
                self.flash_alpha = 255
                self.rocket_trail.clear()
                self.rocket_sparks.clear()

                # 爆炸碎片 - 大量向外扩散
                for _ in range(120):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(4, 12)
                    self.debris_particles.append({
                        "x": self.rocket_x, "y": self.rocket_y,
                        "vx": math.cos(angle) * speed,
                        "vy": math.sin(angle) * speed,
                        "color": self.color_func(),
                        "life": random.randint(15, 40),
                        "max_life": 40,
                        "size": random.uniform(1.5, 3.5),
                    })

                # 文字粒子 - 从爆炸中心飞向文字位置
                for tx, ty in self.text_points:
                    self.text_particles.append({
                        "x": self.rocket_x + random.uniform(-10, 10),
                        "y": self.rocket_y + random.uniform(-10, 10),
                        "tx": tx, "ty": ty,
                        "color": self.color_func(),
                        "size": random.uniform(2.5, 4.5),
                        "sparkle": random.uniform(0, math.pi * 2),
                        "arrived": False,
                        "vx": 0, "vy": 0,
                        "life": 999,
                    })

        elif self.phase == "explode_flash":
            self.phase_timer += 1
            self.flash_alpha = max(0, 255 - self.phase_timer * 15)

            # 更新碎片
            for d in self.debris_particles:
                d["x"] += d["vx"]
                d["y"] += d["vy"]
                d["vy"] += 0.08
                d["vx"] *= 0.98
                d["life"] -= 1
            self.debris_particles = [d for d in self.debris_particles if d["life"] > 0]

            # 文字粒子飞向目标
            all_arrived = True
            for p in self.text_particles:
                if not p["arrived"]:
                    dx = p["tx"] - p["x"]
                    dy = p["ty"] - p["y"]
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 2:
                        # 速度随距离变化，远的飞快，近的减速
                        speed = max(0.08, min(0.15, 0.05 + dist * 0.0005))
                        p["x"] += dx * speed
                        p["y"] += dy * speed
                        all_arrived = False
                    else:
                        p["x"] = p["tx"]
                        p["y"] = p["ty"]
                        p["arrived"] = True

            if all_arrived or self.phase_timer > 160:
                self.phase = "hold"
                self.phase_timer = 0
                for p in self.text_particles:
                    p["arrived"] = True
                    p["x"] = p["tx"]
                    p["y"] = p["ty"]

        elif self.phase == "hold":
            self.phase_timer += 1
            # 碎片继续消散
            for d in self.debris_particles:
                d["x"] += d["vx"]; d["y"] += d["vy"]
                d["vy"] += 0.08; d["life"] -= 1
            self.debris_particles = [d for d in self.debris_particles if d["life"] > 0]

            if self.phase_timer > 300:  # 保持5秒
                self.phase = "scatter"
                self.phase_timer = 0
                for p in self.text_particles:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(0.5, 3)
                    p["vx"] = math.cos(angle) * speed
                    p["vy"] = math.sin(angle) * speed
                    p["life"] = random.randint(50, 100)

        elif self.phase == "scatter":
            self.phase_timer += 1
            for p in self.text_particles:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.03
                p["life"] -= 1
            self.text_particles = [p for p in self.text_particles if p["life"] > 0]
            if not self.text_particles:
                self.phase = "dead"
                self.alive = False

    def draw(self, surface, frame):
        if self.phase == "wait":
            return

        # 火箭上升阶段
        if self.phase == "rising":
            # 拖尾光带
            for i, pos in enumerate(self.rocket_trail):
                alpha = i / max(1, len(self.rocket_trail))
                c = int(220 * alpha * 0.6)
                size = max(1, int(4 * alpha))
                pygame.draw.circle(surface, (c, int(c*0.6), 0), (int(pos[0]), int(pos[1])), size)

            # 火星
            for s in self.rocket_sparks:
                alpha = s["life"] / s["max_life"]
                c = s["color"]
                r = max(0, min(255, int(c[0]*alpha)))
                g = max(0, min(255, int(c[1]*alpha)))
                b = max(0, min(255, int(c[2]*alpha)))
                sz = max(1, int(s["size"] * alpha))
                pygame.draw.circle(surface, (r,g,b), (int(s["x"]), int(s["y"])), sz)

            # 火箭头 - 明亮发光
            pygame.draw.circle(surface, (255,255,240), (int(self.rocket_x), int(self.rocket_y)), 5)
            pygame.draw.circle(surface, self.rocket_color, (int(self.rocket_x), int(self.rocket_y)), 9)
            # 光晕
            glow_surf = pygame.Surface((50,50), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255,200,100,50), (25,25), 22)
            surface.blit(glow_surf, (int(self.rocket_x)-25, int(self.rocket_y)-25))
            return

        # 爆炸闪光
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255,255,220, min(255, self.flash_alpha)),
                (int(self.center_x), int(self.center_y)), int(80 + (255 - self.flash_alpha) * 0.5))
            surface.blit(flash_surf, (0,0))

        # 碎片
        for d in self.debris_particles:
            alpha = d["life"] / d["max_life"]
            c = d["color"]
            r = max(0, min(255, int(c[0]*alpha)))
            g = max(0, min(255, int(c[1]*alpha)))
            b = max(0, min(255, int(c[2]*alpha)))
            sz = max(1, int(d["size"] * alpha))
            pygame.draw.circle(surface, (r,g,b), (int(d["x"]), int(d["y"])), sz)

        # 文字粒子
        for p in self.text_particles:
            if self.phase == "scatter":
                alpha = max(0, p["life"] / 100)
            else:
                alpha = 1.0

            sparkle = 0.7 + 0.3 * math.sin(frame * 0.12 + p["sparkle"])
            c = p["color"]
            r = max(0, min(255, int(c[0]*alpha*sparkle)))
            g = max(0, min(255, int(c[1]*alpha*sparkle)))
            b = max(0, min(255, int(c[2]*alpha*sparkle)))
            sz = max(1, int(p["size"] * alpha))
            pygame.draw.circle(surface, (r,g,b), (int(p["x"]), int(p["y"])), sz)

            # hold阶段加强发光
            if self.phase == "hold" and sz > 1:
                pygame.draw.circle(surface,
                    (max(0,r//2), max(0,g//2), max(0,b//2)),
                    (int(p["x"]), int(p["y"])), sz * 2)


class Firework:
    def __init__(self, x=None):
        self.x = x if x else random.randint(100, WIDTH - 100)
        self.y = HEIGHT
        self.target_y = random.randint(80, HEIGHT // 2)
        self.color = random_color()
        self.speed = random.uniform(9, 14)
        self.particles = []
        self.exploded = False
        self.alive = True
        self.style = random.choice(["circle","ring","star","double","chrysanthemum","willow","spiral","heart"])
        self.rocket_trail = []
        self.rocket_sparks = []

    def update(self):
        if not self.exploded:
            self.y -= self.speed
            self.speed *= 0.997
            self.rocket_trail.append((self.x, self.y))
            if len(self.rocket_trail) > 18:
                self.rocket_trail.pop(0)
            for _ in range(3):
                self.rocket_sparks.append({
                    "x": self.x+random.uniform(-3,3), "y": self.y+random.uniform(3,12),
                    "vx": random.uniform(-0.8,0.8), "vy": random.uniform(0.5,2),
                    "color": random.choice([(255,220,150),(255,200,100),(255,180,80)]),
                    "life": random.randint(6,18), "max_life": 18, "size": random.uniform(1,2.5),
                })
            for s in self.rocket_sparks:
                s["x"]+=s["vx"]; s["y"]+=s["vy"]; s["life"]-=1
            self.rocket_sparks = [s for s in self.rocket_sparks if s["life"]>0]
            if self.y <= self.target_y:
                self.explode()
        else:
            for p in self.particles:
                p.update()
            self.particles = [p for p in self.particles if p.alive]
            if not self.particles:
                self.alive = False

    def explode(self):
        self.exploded = True
        self.rocket_trail.clear()
        self.rocket_sparks.clear()
        color = self.color
        x, y = self.x, self.y
        if self.style == "circle":
            for i in range(random.randint(80,120)):
                angle = (2*math.pi/100)*i
                self.particles.append(Particle(x,y,color,random.uniform(2,6),angle,size=random.randint(2,4),life=random.randint(40,70)))
        elif self.style == "ring":
            for ring in range(2):
                rc = color if ring==0 else random_color()
                for i in range(60):
                    self.particles.append(Particle(x,y,rc,3+ring*2.5+random.uniform(-0.3,0.3),(2*math.pi/60)*i,size=3,life=55))
        elif self.style == "star":
            pts=random.choice([5,6])
            for i in range(200):
                angle=(2*math.pi/200)*i; rf=1.0 if(i*pts)%200<100 else 0.4
                self.particles.append(Particle(x,y,color,random.uniform(2,5)*rf,angle,size=2,life=random.randint(35,60)))
        elif self.style == "double":
            c2=random_color()
            for _ in range(100): self.particles.append(Particle(x,y,color,random.uniform(1.5,3.5),random.uniform(0,2*math.pi),size=3,life=50))
            for _ in range(80): self.particles.append(Particle(x,y,c2,random.uniform(4,6.5),random.uniform(0,2*math.pi),size=2,life=65))
        elif self.style == "chrysanthemum":
            for i in range(150):
                angle=(2*math.pi/150)*i+random.uniform(-0.05,0.05); speed=random.uniform(1,7)
                self.particles.append(Particle(x,y,color,speed,angle,size=2,life=int(40+speed*8),gravity=0.03))
        elif self.style == "willow":
            for _ in range(100): self.particles.append(Particle(x,y,color,random.uniform(2,5),random.uniform(0,2*math.pi),size=2,life=random.randint(70,110),gravity=0.12))
        elif self.style == "spiral":
            for i in range(150):
                self.particles.append(Particle(x,y,color,1+(i/150)*5,(i/150)*math.pi*8,size=2,life=random.randint(40,65)))
        elif self.style == "heart":
            for i in range(120):
                t=(2*math.pi/120)*i; hx=16*math.sin(t)**3; hy=-(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))
                self.particles.append(Particle(x,y,color,math.sqrt(hx**2+hy**2)*0.3,math.atan2(hy,hx),size=3,life=random.randint(45,65),gravity=0.02))

    def draw(self, surface):
        if not self.exploded:
            for i,pos in enumerate(self.rocket_trail):
                alpha=i/max(1,len(self.rocket_trail)); c=int(200*alpha*0.5)
                pygame.draw.circle(surface,(c,c//2,0),(int(pos[0]),int(pos[1])),max(1,int(3*alpha)))
            for s in self.rocket_sparks:
                alpha=s["life"]/s["max_life"]; c=s["color"]
                pygame.draw.circle(surface,(max(0,int(c[0]*alpha)),max(0,int(c[1]*alpha)),max(0,int(c[2]*alpha))),
                    (int(s["x"]),int(s["y"])),max(1,int(s["size"]*alpha)))
            pygame.draw.circle(surface,(255,255,220),(int(self.x),int(self.y)),4)
            pygame.draw.circle(surface,(255,200,100),(int(self.x),int(self.y)),7)
        else:
            for p in self.particles:
                p.draw(surface)


stars = [(random.randint(0,WIDTH),random.randint(0,HEIGHT),random.uniform(0.3,1.5)) for _ in range(250)]
def draw_stars(surface, frame):
    for sx,sy,brightness in stars:
        c = max(0,min(255,int(180*abs(math.sin(frame*0.02+sx*0.1))*brightness)))
        pygame.draw.circle(surface,(c,c,min(255,c+30)),(sx,sy),1)

bg = pygame.Surface((WIDTH, HEIGHT))
for y in range(HEIGHT):
    ratio = y/HEIGHT
    pygame.draw.line(bg,(int(5*(1-ratio)),int(5*(1-ratio)),int(25*(1-ratio)+5)),(0,y),(WIDTH,y))

fireworks = []
text_fireworks = []
frame = 0
auto_timer = 0
birthday_timer = 120

def trigger_birthday():
    global text_fireworks
    text_fireworks = []

    # 第一行 "尹朵小朋友" - 整行作为一个大烟花
    tf1 = TextBurstFirework(
        "\u5C39\u6735\u5C0F\u670B\u53CB",
        WIDTH // 2, HEIGHT // 3 - 30,
        random.choice([golden_color, pink_color]),
        delay=0, font_size=160
    )
    text_fireworks.append(tf1)

    # 第二行 "生日快乐！" - 稍后发射
    tf2 = TextBurstFirework(
        "\u751F\u65E5\u5FEB\u4E50\uFF01",
        WIDTH // 2, HEIGHT // 3 + 180,
        random.choice([golden_color, pink_color]),
        delay=80, font_size=160
    )
    text_fireworks.append(tf2)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                fireworks.append(Firework())
            elif event.key == pygame.K_b:
                trigger_birthday()
                for _ in range(4):
                    fireworks.append(Firework())
        elif event.type == pygame.MOUSEBUTTONDOWN:
            fireworks.append(Firework(event.pos[0]))

    if birthday_timer > 0:
        birthday_timer -= 1
        if birthday_timer == 0:
            trigger_birthday()
            for _ in range(3):
                fireworks.append(Firework())

    auto_timer += 1
    if auto_timer > random.randint(30, 60):
        auto_timer = 0
        fireworks.append(Firework())
        if random.random() > 0.7:
            fireworks.append(Firework())

    for fw in fireworks:
        fw.update()
    fireworks = [fw for fw in fireworks if fw.alive]
    for tf in text_fireworks:
        tf.update()
    text_fireworks = [tf for tf in text_fireworks if tf.alive]

    screen.blit(bg, (0, 0))
    draw_stars(screen, frame)
    for fw in fireworks:
        fw.draw(screen)
    for tf in text_fireworks:
        tf.draw(screen, frame)

    if frame < 250:
        font = pygame.font.Font(None, 24)
        alpha = max(0, 255 - frame)
        text = font.render("Click/SPACE: launch  |  B: birthday  |  ESC: exit", True, (alpha,alpha,alpha))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT-35))

    pygame.display.flip()
    clock.tick(60)
    frame += 1

pygame.quit()
sys.exit()
