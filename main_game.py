import pygame as pg
import random
import sys as sy
import math

# --- 設定・定数 ---
scale_factor = 2
chip_s = int(24 * scale_factor)  # 1マス約48px
map_s = pg.Vector2(16, 9)

# 色定義
COLOR_BG = (10, 10, 30)
COLOR_GRID = (30, 30, 60)
COLOR_REIMU = (255, 50, 50)
COLOR_MARISA = (255, 255, 0)
COLOR_LASER_CORE = (255, 255, 255)
COLOR_LASER_OUT = (255, 255, 100)

# --- サウンド管理クラス ---
class SoundManager:
  def __init__(self):
    self.sounds = {}
    self.enabled = True
    try:
      pg.mixer.init()
      # ファイルがある場合はここでロード
      # self.sounds['shoot'] = pg.mixer.Sound('se_shoot.wav')
      # self.sounds['laser'] = pg.mixer.Sound('se_laser.wav')
      # self.sounds['damage'] = pg.mixer.Sound('se_damage.wav')
    except:
      self.enabled = False

  def play(self, name):
    if self.enabled and name in self.sounds:
      self.sounds[name].play()

  def play_bgm(self):
    if self.enabled and pg.mixer.music.get_busy() == False:
      try: pg.mixer.music.play(-1)
      except: pass

# --- エフェクト・パーティクル ---
class Particle:
  def __init__(self, pos, color, vel, life, size):
    self.pos = pg.Vector2(pos)
    self.vel = pg.Vector2(vel)
    self.color = color
    self.life = life
    self.max_life = life
    self.size = size

  def update(self):
    self.pos += self.vel
    self.life -= 1
    self.size *= 0.9

  def draw(self, screen):
    if self.life > 0:
      alpha = int(255 * (self.life / self.max_life))
      s = pg.Surface(
          (int(self.size * 2) + 1, int(self.size * 2) + 1), pg.SRCALPHA)
      pg.draw.circle(s, (*self.color, alpha),
                     (int(self.size), int(self.size)), int(self.size))
      screen.blit(s, (int(self.pos.x - self.size),
                  int(self.pos.y - self.size)))

class Laser:
  def __init__(self, y_idx, duration):
    self.y = y_idx
    self.timer = duration
    self.width = 0
    self.max_width = chip_s * 1.5
    self.state = "WARNING"  # WARNING -> FIRE -> FADE
    self.warning_timer = 60

  def update(self):
    if self.state == "WARNING":
      self.warning_timer -= 1
      if self.warning_timer <= 0:
        self.state = "FIRE"
    elif self.state == "FIRE":
      self.width += (self.max_width - self.width) * 0.2
      self.timer -= 1
      if self.timer <= 0:
        self.state = "FADE"
    elif self.state == "FADE":
      self.width *= 0.8

  def draw(self, screen):
    cy = self.y * chip_s + chip_s // 2
    if self.state == "WARNING":
      rect = (0, cy - 2, 16 * chip_s, 4)
      pg.draw.rect(screen, (255, 0, 0), rect)
      if (self.warning_timer // 4) % 2 == 0:
        pg.draw.rect(screen, (255, 255, 0), rect, 1)
    elif self.width > 1:
      rect_out = (0, cy - self.width // 2, 16 * chip_s, self.width)
      rect_in = (0, cy - self.width // 4, 16 * chip_s, self.width // 2)
      pg.draw.rect(screen, COLOR_LASER_OUT, rect_out)
      pg.draw.rect(screen, COLOR_LASER_CORE, rect_in)

class Bullet:
  def __init__(self, pos, target_char, is_enemy=False, pattern="homing"):
    self.pos = pg.Vector2(pos)
    self.target = target_char
    self.vel = pg.Vector2(0, 0)
    self.speed = 0.45 if not is_enemy else 0.25
    self.is_active = True
    self.is_enemy = is_enemy
    self.pattern = pattern
    self.timer = 0
    self.angle_rot = 0

    if pattern == "star":
      angle = random.uniform(0, 360)
      self.vel = pg.Vector2(1, 0).rotate(angle) * self.speed * 0.8

  def update(self):
    self.timer += 1
    self.angle_rot += 15  # 回転演出用

    if self.pattern == "homing":
      target_vec = self.target.pos - self.pos
      turn = 0.08 if self.is_enemy else 0.2  # 霊夢の誘導性能アップ
      if target_vec.length() > 0:
        target_vec = target_vec.normalize() * self.speed
        self.vel += (target_vec - self.vel) * turn
        if self.vel.length() > self.speed:
          self.vel = self.vel.normalize() * self.speed

    elif self.pattern == "star":
      if self.timer < 30: self.vel *= 0.95
      elif self.timer == 30:
        if self.target:
          d = (self.target.pos - self.pos)
          if d.length() > 0: self.vel = d.normalize() * self.speed * 1.5

    self.pos += self.vel
    if not (-2 <= self.pos.x < 18 and -2 <= self.pos.y < 11):
      self.is_active = False

  def draw(self, screen):
    bx, by = int(self.pos.x * chip_s + 20), int(self.pos.y * chip_s + 20)

    if not self.is_enemy:
      # 霊夢の弾：回転するお札エフェクト
      size = 12
      # 座標を中心に回転させる計算
      pts = [
          (-size / 2, -size), (size / 2, -size),
          (size / 2, size), (-size / 2, size)
      ]
      rot_pts = []
      rad = math.radians(self.angle_rot)
      c = math.cos(rad)
      s = math.sin(rad)
      for px, py in pts:
        rx = px * c - py * s
        ry = px * s + py * c
        rot_pts.append((bx + rx, by + ry))

      pg.draw.polygon(screen, (255, 255, 255), rot_pts)     # 白
      pg.draw.polygon(screen, (255, 50, 50), rot_pts, 2)    # 赤枠
      # 内側の模様
      inner_rect = (bx - 2, by - 4, 4, 8)
      pg.draw.rect(screen, (255, 0, 0), inner_rect)

    elif self.pattern == "star":
      points = []
      rot = self.timer * 10
      for i in range(5):
        ang = math.radians(rot + i * 72)
        points.append((bx + math.cos(ang) * 10,
                      by + math.sin(ang) * 10))
        ang2 = math.radians(rot + i * 72 + 36)
        points.append((bx + math.cos(ang2) * 4,
                      by + math.sin(ang2) * 4))
      pg.draw.polygon(screen, (255, 255, 100), points)
      pg.draw.polygon(screen, (255, 255, 255), points, 1)
    else:
      w, h = 10, 16
      rect = (bx - w // 2, by - h // 2, w, h)
      pg.draw.rect(screen, (255, 150, 150), rect)
      pg.draw.rect(screen, (255, 255, 255), rect, 2)

class Item:
  def __init__(self, itype="power"):
    self.pos = pg.Vector2(random.randint(1, 14), random.randint(1, 7))
    self.type = itype
    self.timer = 300
    self.bob_offset = random.random() * 6.28

  def draw(self, screen, frame):
    offset_y = math.sin(frame * 0.1 + self.bob_offset) * 5
    p = (int(self.pos.x * chip_s + 24),
         int(self.pos.y * chip_s + 24 + offset_y))
    color = (255, 0, 255) if self.type == "power" else (0, 255, 100)
    if self.type == "super": color = (255, 215, 0)
    pg.draw.circle(screen, color, p, 15)
    pg.draw.circle(screen, (255, 255, 255), p, 15, 2)
    if frame % 10 == 0:
      pg.draw.circle(screen, (255, 255, 255), p, 18, 1)

class PlayerCharacter:
  def __init__(self, name, init_pos, img_path, hp):
    self.pos = pg.Vector2(init_pos)
    self.size = pg.Vector2(24, 32) * scale_factor
    self.dir = 2
    self.hp = hp
    self.max_hp = hp
    self.is_moving = False
    self.__moving_vec = pg.Vector2(0, 0)
    self.__moving_acc = pg.Vector2(0, 0)
    self.invincible_frame = 0
    self.shot_cooldown = 0
    self.super_timer = 0
    self.name = name
    self.prev_positions = []

    try:
      img_raw = pg.image.load(img_path).convert_alpha()
      self.__img_arr = [[pg.transform.scale(img_raw.subsurface(
          24 * j, 32 * i, 24, 32), self.size) for j in range(3)] for i in range(4)]
      for i in range(4): self.__img_arr[i].append(self.__img_arr[i][1])
    except:
      self.__img_arr = None

  def move_to(self, vec):
    if self.is_moving: return
    self.is_moving = True
    self.__moving_vec = vec.copy()
    self.__moving_acc = pg.Vector2(0, 0)

  def update_move_process(self, speed_val):
    if not self.is_moving: return

    if len(self.prev_positions) > 3: self.prev_positions.pop(0)
    self.prev_positions.append(self.get_dp())

    self.__moving_acc += self.__moving_vec * speed_val
    if self.__moving_acc.length() >= chip_s:
      self.pos += self.__moving_vec
      self.pos.x = max(0, min(15, self.pos.x))
      self.pos.y = max(0, min(8, self.pos.y))
      self.is_moving = False
      self.__moving_acc = pg.Vector2(0, 0)
      self.prev_positions = []

  def get_dp(self):
    dp = self.pos * chip_s - pg.Vector2(0, 12) * scale_factor
    if self.is_moving: dp += self.__moving_acc
    return dp

  def get_img(self, frame):
    if self.invincible_frame > 0 and (frame // 2) % 2 == 0: return pg.Surface((0, 0), pg.SRCALPHA)
    if self.__img_arr is None:
      surf = pg.Surface(self.size)
      surf.fill(COLOR_REIMU if self.name == 'reimu' else COLOR_MARISA)
      pg.draw.rect(surf, (255, 255, 255),
                   (0, 0, self.size.x, self.size.y), 2)
      return surf
    idx = (frame // 4 % 4) if self.is_moving else 1
    return self.__img_arr[self.dir][idx]

def main():
  pg.init()
  disp_w, disp_h = int(chip_s * map_s.x), int(chip_s * map_s.y)
  screen = pg.display.set_mode((disp_w, disp_h))
  pg.display.set_caption("東方討伐伝 - Enhanced Edition")
  clock = pg.time.Clock()

  font_title = pg.font.SysFont("msgothic", 60, bold=True)
  font_sub = pg.font.SysFont("msgothic", 25)

  sound_mgr = SoundManager()
  sound_mgr.play_bgm()

  def create_particles(pos, count, color, speed=3.0):
    parts = []
    for _ in range(count):
      angle = random.uniform(0, 6.28)
      v = pg.Vector2(math.cos(angle), math.sin(angle)) * \
          random.uniform(1, speed)
      parts.append(Particle(pos, color, v, 15 + random.randint(0, 10), 3))
    return parts

  # --- タイトル画面 ---
  def show_title():
    sel = 0
    particles = []
    while True:
      screen.fill(COLOR_BG)
      if random.random() < 0.1:
        particles.extend(create_particles(
            (random.randint(0, disp_w), disp_h), 1, (50, 50, 100), 1))

      for p in particles[:]:
        p.vel.y = -1
        p.update()
        p.draw(screen)
        if p.life <= 0: particles.remove(p)

      t1 = font_title.render("東方討伐伝", True, (255, 50, 50))
      screen.blit(t1, (disp_w // 2 - t1.get_width() // 2, 80))

      for i, text in enumerate(["戦闘開始", "終了"]):
        color = (255, 255, 0) if i == sel else (150, 150, 150)
        txt = font_sub.render(text, True, color)
        screen.blit(
            txt, (disp_w // 2 - txt.get_width() // 2, 260 + i * 60))

      pg.display.update()

      for event in pg.event.get():
        if event.type == pg.QUIT: pg.quit(); sy.exit()
        if event.type == pg.KEYDOWN:
          if event.key in [pg.K_UP, pg.K_w]: sel = 0
          if event.key in [pg.K_DOWN, pg.K_s]: sel = 1
          if event.key in [pg.K_SPACE, pg.K_RETURN]:
            if sel == 0: return
            else: pg.quit(); sy.exit()
      clock.tick(60)

  show_title()

  reimu = PlayerCharacter('reimu', (1, 4), './data/img/reimu.png', 10)
  marisa = PlayerCharacter('marisa', (14, 4), './data/img/marisa.png', 60)

  bullets, items, particles, lasers = [], [], [], []
  m_vec = [pg.Vector2(0, -1), pg.Vector2(1, 0),
           pg.Vector2(0, 1), pg.Vector2(-1, 0)]

  frame, finish_frame = 0, 0
  game_state, is_paused = "PLAY", False
  screen_shake = 0

  marisa_action_timer = 0
  marisa_state = "IDLE"

  while True:
    shake_off = pg.Vector2(0, 0)
    if screen_shake > 0:
      shake_off = pg.Vector2(
          random.randint(-screen_shake, screen_shake), random.randint(-screen_shake, screen_shake))
      screen_shake = max(0, screen_shake - 1)

    for event in pg.event.get():
      if event.type == pg.QUIT: pg.quit(); sy.exit()
      if event.type == pg.KEYDOWN:
        if event.key == pg.K_p: is_paused = not is_paused
        if game_state == "PLAY" and not is_paused:
          if not reimu.is_moving:
            if event.key == pg.K_UP: reimu.dir = 0
            elif event.key == pg.K_RIGHT: reimu.dir = 1
            elif event.key == pg.K_DOWN: reimu.dir = 2
            elif event.key == pg.K_LEFT: reimu.dir = 3

          if event.key == pg.K_SPACE and reimu.shot_cooldown <= 0:
            # 霊夢の攻撃強化: 通常で3way、スーパーで5way
            angles = [-10, 0,
                      10] if reimu.super_timer <= 0 else [-25, -12, 0, 12, 25]
            sound_mgr.play('shoot')
            for a in angles:
              b = Bullet(reimu.pos, marisa)
              b.vel = m_vec[reimu.dir].rotate(a) * b.speed
              bullets.append(b)
            reimu.shot_cooldown = 10

        if game_state != "PLAY" and finish_frame > 60 and event.key == pg.K_r:
          main(); return

    if not is_paused and game_state == "PLAY":
      key = pg.key.get_pressed()
      if not reimu.is_moving:
        cmd = -1
        if key[pg.K_UP]: cmd = 0
        elif key[pg.K_RIGHT]: cmd = 1
        elif key[pg.K_DOWN]: cmd = 2
        elif key[pg.K_LEFT]: cmd = 3
        if cmd != -1:
          target = reimu.pos + m_vec[cmd]
          if 0 <= target.x < 16 and 0 <= target.y < 9:
            reimu.dir = cmd; reimu.move_to(m_vec[cmd])
            p_pos = reimu.get_dp() + pg.Vector2(24, 48)
            particles.extend(create_particles(
                p_pos, 2, (255, 200, 200), 1))

      is_awakened = marisa.hp <= 30
      marisa_action_timer += 1

      if marisa_state == "IDLE":
        wait_time = 30 if is_awakened else 50
        if marisa_action_timer > wait_time:
          dice = random.random()
          if is_awakened and dice < 0.3:
            marisa_state = "LASER_PREP"
          elif dice < 0.6:
            marisa_state = "STAR_FIRE"
          else:
            marisa_state = "MOVE"
          marisa_action_timer = 0

      elif marisa_state == "MOVE":
        if not marisa.is_moving:
          m_cmd = random.randint(0, 3)
          marisa.dir = m_cmd
          marisa.move_to(m_vec[m_cmd])
          eb = Bullet(marisa.pos, reimu, is_enemy=True)
          eb.vel = (reimu.pos - marisa.pos).normalize() * 0.25
          bullets.append(eb)
          marisa_state = "IDLE"

      elif marisa_state == "STAR_FIRE":
        if marisa_action_timer % 5 == 0:
          sound_mgr.play('shoot')
          for _ in range(3):
            eb = Bullet(marisa.pos, reimu,
                        is_enemy=True, pattern="star")
            bullets.append(eb)
        if marisa_action_timer > 20:
          marisa_state = "IDLE"
          marisa_action_timer = 0

      elif marisa_state == "LASER_PREP":
        if marisa_action_timer == 1:
          lasers.append(Laser(int(reimu.pos.y), 100))
          p_pos = marisa.pos * chip_s - \
              pg.Vector2(0, 12) * scale_factor + pg.Vector2(24, 32)
          particles.extend(create_particles(
              p_pos, 20, (255, 255, 100), 5))
          sound_mgr.play('laser')
        if marisa_action_timer > 60:
          marisa_state = "IDLE"
          marisa_action_timer = 0

      if reimu.invincible_frame > 0: reimu.invincible_frame -= 1
      if reimu.super_timer > 0: reimu.super_timer -= 1
      if reimu.shot_cooldown > 0: reimu.shot_cooldown -= 1

      for b in bullets[:]:
        b.update()
        hit = False

        # 霊夢弾のパーティクル軌跡
        if not b.is_enemy and frame % 2 == 0:
          p_pos = b.pos * chip_s + pg.Vector2(20, 20)
          particles.extend(create_particles(
              p_pos, 1, (255, 100, 100), 0.5))

        if b.is_enemy:
          if (b.pos - reimu.pos).length() < 0.5 and reimu.invincible_frame == 0:
            reimu.hp -= 1; reimu.invincible_frame = 60; hit = True
            screen_shake = 5
            sound_mgr.play('damage')
        else:
          if (b.pos - marisa.pos).length() < 0.8:
            marisa.hp -= 1; hit = True
            particles.extend(create_particles(
                b.pos * chip_s + pg.Vector2(24, 24), 3, (255, 255, 0)))

        if hit:
          b.is_active = False
        if not b.is_active: bullets.remove(b)

      for l in lasers[:]:
        l.update()
        if l.state == "FIRE" and reimu.invincible_frame == 0:
          if abs(reimu.pos.y - l.y) < 0.8:
            reimu.hp -= 1  # ダメージを1に軽減
            reimu.invincible_frame = 120  # 無敵時間を2秒に延長(即死防止)
            screen_shake = 15
            sound_mgr.play('damage')
        if l.width < 1 and l.state == "FADE": lasers.remove(l)

      if frame % 280 == 0:
        items.append(Item(random.choice(["power", "heal", "super"])))
      for it in items[:]:
        it.timer -= 1
        if (reimu.pos - it.pos).length() < 0.6:
          if it.type == "super": reimu.super_timer = 400
          elif it.type == "heal": reimu.hp = min(reimu.max_hp, reimu.hp + 3)
          items.remove(it)
          particles.extend(create_particles(
              reimu.get_dp() + pg.Vector2(24, 24), 10, (200, 255, 200)))
        elif it.timer <= 0: items.remove(it)

      for p in particles[:]:
        p.update()
        if p.life <= 0: particles.remove(p)

      # 移動速度調整 (速すぎたのを抑制)
      # 60FPS動作なので、1フレームあたりの移動量を 16->8 程度に落とす
      reimu.update_move_process(12 if reimu.super_timer > 0 else 8)
      marisa.update_move_process(6 if is_awakened else 4)

      if reimu.hp <= 0: game_state = "LOSE"
      if marisa.hp <= 0: game_state = "WIN"

    # --- 描画 ---
    screen.fill(COLOR_BG)

    for x in range(16):
      pg.draw.line(screen, COLOR_GRID, (x * chip_s + shake_off.x,
                   shake_off.y), (x * chip_s + shake_off.x, disp_h + shake_off.y))
    for y in range(9):
      pg.draw.line(screen, COLOR_GRID, (shake_off.x, y * chip_s +
                   shake_off.y), (disp_w + shake_off.x, y * chip_s + shake_off.y))

    for l in lasers: l.draw(screen)

    if marisa.hp <= 30 and game_state == "PLAY":
      p = marisa.get_dp() + pg.Vector2(24, 32) + shake_off
      pg.draw.circle(screen, (200, 0, 255), (int(p.x), int(
          p.y)), 50 + int(math.sin(frame * 0.2) * 10), 3)

    for it in items: it.draw(screen, frame)
    for b in bullets: b.draw(screen)
    for p in particles: p.draw(screen)

    for prev_p in reimu.prev_positions:
      ghost = reimu.get_img(frame).copy()
      ghost.set_alpha(80)
      screen.blit(ghost, prev_p + shake_off)

    screen.blit(reimu.get_img(frame), reimu.get_dp() + shake_off)
    if game_state != "WIN" or (frame // 4) % 2 == 0:
      screen.blit(marisa.get_img(frame), marisa.get_dp() + shake_off)

    # UI
    pg.draw.rect(screen, (50, 0, 0), (20, 15, 200, 12))
    pg.draw.rect(screen, (255, 0, 50),
                 (20, 15, (reimu.hp / reimu.max_hp) * 200, 12))

    pg.draw.rect(screen, (50, 50, 0), (disp_w - 220, 15, 200, 12))
    c_m = (255, 0, 255) if marisa.hp <= 30 else (200, 200, 0)
    pg.draw.rect(screen, c_m, (disp_w - 220, 15,
                 (marisa.hp / 60) * 200, 12))

    if reimu.super_timer > 0:
      pg.draw.rect(screen, (255, 255, 0),
                   (20, 30, (reimu.super_timer / 400) * 200, 4))

    if is_paused:
      overlay = pg.Surface((disp_w, disp_h), pg.SRCALPHA)
      overlay.fill((0, 0, 0, 150))
      screen.blit(overlay, (0, 0))
      txt = font_sub.render("- PAUSE -", True, (255, 255, 255))
      screen.blit(txt, (disp_w // 2 - txt.get_width() // 2, disp_h // 2))

    if game_state != "PLAY":
      finish_frame += 1
      overlay = pg.Surface((disp_w, disp_h), pg.SRCALPHA)
      color = (255, 255, 255, max(0, 255 - finish_frame * 4)
               ) if game_state == "WIN" else (0, 0, 0, min(200, finish_frame * 3))
      overlay.fill(color)
      screen.blit(overlay, (0, 0))

      if finish_frame > 60:
        msg = "MISSION CLEAR" if game_state == "WIN" else "GAME OVER"
        col = (255, 200, 0) if game_state == "WIN" else (255, 0, 0)
        img = font_title.render(msg, True, col)
        screen.blit(
            img, (disp_w // 2 - img.get_width() // 2, disp_h // 2 - 40))
        info = font_sub.render(
            "Press 'R' to Retry", True, (200, 200, 200))
        screen.blit(
            info, (disp_w // 2 - info.get_width() // 2, disp_h // 2 + 40))

    if not is_paused: frame += 1
    pg.display.update()
    clock.tick(60)

if __name__ == "__main__": main()
