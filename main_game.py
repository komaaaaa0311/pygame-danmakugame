import pygame as pg
import random
import math
from enum import Enum

# =============================================================================
# 1. ゲーム設定・定数の定義
# =============================================================================
SCALE = 2
CHIP = int(24 * SCALE)       # 1マスのサイズ (48px)
MAP_SIZE = pg.Vector2(16, 9)  # マップのマス数 (横16 x 縦9)
SCREEN_W = int(CHIP * MAP_SIZE.x)
SCREEN_H = int(CHIP * MAP_SIZE.y)
VEC = pg.Vector2             # ベクトル計算用ショートカット

# ゲームの状態管理
class State(Enum):
  TITLE = 0
  COUNTDOWN = 1
  PLAY = 2
  OVER = 3

# =============================================================================
# 2. 描画ヘルパー関数
# =============================================================================
def draw_neon_text(screen, font, text_str, base_color, center_pos, alpha=255):
  """ ネオン風テキスト描画 """
  core_text = font.render(text_str, True, (255, 255, 255))
  core_text.set_alpha(alpha)
  core_rect = core_text.get_rect(center=center_pos)

  glow_text = font.render(text_str, True, base_color)
  glow_text.set_alpha(max(0, min(100, alpha - 50)))

  offset_amount = 3
  offsets = [(-offset_amount, 0), (offset_amount, 0),
             (0, -offset_amount), (0, offset_amount)]

  for dx, dy in offsets:
    screen.blit(glow_text, core_rect.move(dx, dy))
  screen.blit(core_text, core_rect)

def draw_star(screen, color, center, size, angle=0):
  """ 星型を描画する関数 """
  pts = []
  for i in range(10):
    r = size if i % 2 == 0 else size * 0.4
    rad = math.radians(i * 36 + angle - 90)
    x = center[0] + r * math.cos(rad)
    y = center[1] + r * math.sin(rad)
    pts.append((x, y))
  pg.draw.polygon(screen, color, pts)

# =============================================================================
# 3. エフェクト（パーティクル）クラス
# =============================================================================
class Particle:
  def __init__(self, pos, color):
    self.pos = VEC(pos)
    self.color = color
    self.vel = VEC(random.uniform(-1, 1), random.uniform(-1, 1)
                   ).normalize() * random.uniform(2, 8)
    self.life = random.randint(10, 25)
    self.size = random.uniform(2, 5)

  def update(self):
    self.pos += self.vel
    self.life -= 1
    self.size *= 0.9

  def draw(self, screen):
    if self.life > 0:
      pg.draw.circle(screen, self.color, (int(self.pos.x),
                                          int(self.pos.y)), int(self.size))

# =============================================================================
# 4. 弾クラス (Bullet)
# =============================================================================
class Bullet:
  def __init__(self, pos, direction, owner, btype="N", target=None, is_awakened=False):
    self.pos = VEC(pos)
    self.direction = direction.normalize() if direction.length_squared() != 0 else VEC(0, 1)
    self.owner = owner
    self.type = btype
    self.target = target
    self.timer = 0
    self.active = True
    self.is_awakened = is_awakened

    # --- 弾の設定 ---
    speed_mult = 1.2 if is_awakened else 1.0

    if self.type == "Amulet":   # 霊夢SP
      self.speed = 0.4
      self.damage = 1
      self.life_time = 150
      self.homing_strength = 0.20
    elif self.type == "Star":   # 魔理沙SP
      self.speed = 0.5 * speed_mult
      self.damage = 1
      self.life_time = 180
      self.homing_strength = 0.08 if not is_awakened else 0.15
    else:                       # 通常弾
      self.speed = (0.7 if owner == "霊夢" else 0.5) * speed_mult
      self.damage = 1
      self.life_time = 100
      self.homing_strength = 0

  def update(self):
    if (self.type in ["Amulet", "Star"]) and self.target and self.target.hp > 0:
      diff = (self.target.pos - self.pos)
      if diff.length_squared() > 0:
        desired = diff.normalize()
        self.direction = self.direction.lerp(
            desired, self.homing_strength).normalize()

    self.pos += self.direction * self.speed
    self.timer += 1

    if self.timer > self.life_time:
      self.active = False

    margin = 2
    if not (-margin <= self.pos.x <= MAP_SIZE.x + margin and -margin <= self.pos.y <= MAP_SIZE.y + margin):
      self.active = False

  def draw(self, screen):
    p = self.pos * CHIP

    if self.type == "Star":
      color = pg.Color(
          'ORANGE') if self.is_awakened else pg.Color('YELLOW')
      draw_star(screen, color, (p.x, p.y), 16, self.timer * 10)
      draw_star(screen, pg.Color('WHITE'), (p.x, p.y), 8, self.timer * 10)

    elif self.type == "Amulet":
      angle = math.degrees(
          math.atan2(-self.direction.y, self.direction.x))
      amulet_surf = pg.Surface((20, 10), pg.SRCALPHA)
      pg.draw.rect(amulet_surf, pg.Color('RED'), (0, 0, 20, 10))
      pg.draw.rect(amulet_surf, pg.Color('WHITE'), (4, 2, 12, 6))
      pg.draw.rect(amulet_surf, pg.Color('PINK'), (5, 3, 10, 8))
      rotated_surf = pg.transform.rotate(amulet_surf, angle)
      rect = rotated_surf.get_rect(center=(p.x, p.y))
      screen.blit(rotated_surf, rect)

    else:
      if self.owner == "霊夢":
        angle = math.degrees(
            math.atan2(-self.direction.y, self.direction.x))
        amulet_surf = pg.Surface((16, 8), pg.SRCALPHA)
        pg.draw.rect(amulet_surf, pg.Color('RED'), (0, 0, 16, 8))
        pg.draw.rect(amulet_surf, pg.Color('WHITE'), (2, 2, 12, 4))
        rotated_surf = pg.transform.rotate(amulet_surf, angle)
        rect = rotated_surf.get_rect(center=(p.x, p.y))
        screen.blit(rotated_surf, rect)
      else:
        color = pg.Color(
            'MAGENTA') if self.is_awakened else pg.Color('CYAN')
        end_pos = p + self.direction * 15
        pg.draw.line(screen, color, p, end_pos, 4)

  def get_rect(self):
    p = self.pos * CHIP
    size = 20 if self.type == "Star" else 12
    return pg.Rect(p.x - size / 2, p.y - size / 2, size, size)

# =============================================================================
# 5. キャラクタークラス
# =============================================================================
class Char:
  def __init__(self, name, pos, img_path, color, hp):
    self.name = name
    self.pos = VEC(pos)
    self.color = color
    self.max_hp = hp
    self.hp = hp
    self.dir = 2
    self.bullets = []
    self.cool_time = 0
    self.move_vec = VEC(0, 0)
    self.move_anim = VEC(0, 0)
    self.img = self.load_img(img_path)
    self.invincible_timer = 0
    self.is_awakened = False

    # --- 死亡演出用変数の追加 ---
    self.is_dying = False   # 撃破演出中かどうか
    self.death_timer = 0    # 演出用のタイマー

  def load_img(self, path):
    try:
      raw = pg.image.load(path)
      chips = []
      for i in range(4):
        row = []
        for j in range(3):
          rect = (24 * j, 32 * i, 24, 32)
          img = raw.subsurface(rect)
          img = pg.transform.scale(
              img, (int(24 * SCALE), int(32 * SCALE)))
          row.append(img)
        chips.append(row)
      return chips
    except:
      return None

  def update(self):
    # 死亡演出中は更新処理（移動など）を行わない
    if self.is_dying:
      return

    if self.cool_time > 0: self.cool_time -= 1

    for b in self.bullets:
      b.update()
    self.bullets = [b for b in self.bullets if b.active]

    if self.move_vec.length() > 0:
      self.move_anim += self.move_vec * 8
      if self.move_anim.length() >= CHIP:
        self.pos += self.move_vec
        self.move_vec = VEC(0, 0)
        self.move_anim = VEC(0, 0)

  def shoot(self, vec, target=None, btype="N"):
    if self.is_dying: return  # 死亡時は撃てない

    ct_mult = 0.7 if self.is_awakened else 1.0
    if self.cool_time > 0: return

    base_ct = 8 if btype == "N" else 45
    self.cool_time = int(base_ct * ct_mult)

    center_pos = self.pos + VEC(0.5, 0.5)

    if btype == "N":
      self.bullets.append(
          Bullet(center_pos, vec, self.name, "N", is_awakened=self.is_awakened))
    else:
      if self.name == "霊夢":
        base_angle = math.degrees(math.atan2(vec.y, vec.x))
        for i in range(-2, 3):
          rad = math.radians(base_angle + i * 20)
          d = VEC(math.cos(rad), math.sin(rad))
          self.bullets.append(
              Bullet(center_pos, d, self.name, "Amulet", target, self.is_awakened))
      else:
        count = 8 if self.is_awakened else 5
        base_angle = math.degrees(math.atan2(vec.y, vec.x))
        for i in range(count):
          spread = random.uniform(-70, 70)
          rad = math.radians(base_angle + spread)
          d = VEC(math.cos(rad), math.sin(rad))
          b = Bullet(center_pos, d, self.name,
                     "Star", target, self.is_awakened)
          b.speed = random.uniform(0.3, 0.8)
          self.bullets.append(b)

  def draw(self, screen, frame):
    # 完全に死亡（リザルト画面での表示など）している場合は描画しない
    if self.is_dying and self.death_timer <= 0:
      return

    # 死亡演出中の点滅処理
    if self.is_dying:
      # 4フレームごとに描画をスキップ＝高速点滅
      if (self.death_timer // 2) % 2 == 0:
        pass  # 描画する
      else:
        return  # 描画しない（透明）

    draw_pos = self.pos * CHIP - VEC(0, 12) * SCALE + self.move_anim

    if self.is_awakened and not self.is_dying:
      aura_radius = 30 + math.sin(frame * 0.2) * 5
      color = (255, 100, 100) if self.name == "魔理沙" else (255, 200, 200)
      s = pg.Surface((100, 100), pg.SRCALPHA)
      pg.draw.circle(s, (*color, 100), (50, 50), int(aura_radius))
      screen.blit(s, (draw_pos.x + 24 - 50, draw_pos.y + 32 - 50))

    if not (self.invincible_timer > 0 and (frame // 2) % 2 == 0):
      if self.img:
        screen.blit(self.img[self.dir][frame // 6 % 3], draw_pos)
      else:
        pg.draw.rect(screen, self.color,
                     (draw_pos.x, draw_pos.y, 48, 64))

    for b in self.bullets:
      b.draw(screen)

  def get_hitbox(self):
    p = self.pos * CHIP + self.move_anim
    return pg.Rect(p.x + 12, p.y + 12, CHIP - 24, CHIP - 24)

# =============================================================================
# 6. AIクラス (覚醒ロジック強化)
# =============================================================================
class AI(Char):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.wait_timer = 0

  def think(self, target_obj):
    # 死亡中は思考停止
    if self.is_dying: return

    if self.hp <= self.max_hp * 0.5:
      self.is_awakened = True
    else:
      self.is_awakened = False

    target_pos = target_obj.pos
    if self.move_vec.length() > 0: return

    self.wait_timer += 1

    think_threshold = 5 if self.is_awakened else 10

    if self.wait_timer < think_threshold: return
    self.wait_timer = 0

    diff = target_pos - self.pos

    # 【修正箇所】ここにあった `if diff.length_squared() == 0: return` を削除しました。
    # これにより、重なっていても攻撃や回避行動が行われるようになります。

    is_aligned = (abs(diff.x) < 0.5 or abs(diff.y) < 0.5)
    move_vecs = [VEC(0, -1), VEC(1, 0), VEC(0, 1), VEC(-1, 0)]

    dist = self.pos.distance_to(target_pos)
    sp_prob = 0.30 if self.is_awakened else 0.15

    if dist < 8 and random.random() < sp_prob:
      if abs(diff.x) > abs(diff.y): self.dir = 1 if diff.x > 0 else 3
      else: self.dir = 2 if diff.y > 0 else 0
      shoot_dir = move_vecs[self.dir]
      self.shoot(shoot_dir, target_obj, "S")
      return

    if is_aligned:
      normal_prob = 0.85 if self.is_awakened else 0.6
      if random.random() < normal_prob:
        self.shoot(diff, target_obj, "N")
        if diff.y > 0: self.dir = 2
        elif diff.y < 0: self.dir = 0
        elif diff.x > 0: self.dir = 1
        else: self.dir = 3
        return

    move_idx = -1
    dodge_prob = 0.7 if self.is_awakened else 0.5

    if is_aligned and random.random() < dodge_prob:
      if abs(diff.x) < 0.5: move_idx = 2 if self.pos.y < target_pos.y else 0
      else: move_idx = 1 if self.pos.x < target_pos.x else 3
    elif random.random() < 0.7:
      if abs(diff.x) > abs(diff.y): move_idx = 1 if diff.x > 0 else 3
      else: move_idx = 2 if diff.y > 0 else 0
    else:
      move_idx = random.randint(0, 3)

    next_pos = self.pos + move_vecs[move_idx]
    if 0 <= next_pos.x < MAP_SIZE.x and 0 <= next_pos.y < MAP_SIZE.y:
      self.dir = move_idx
      self.move_vec = move_vecs[move_idx]

# =============================================================================
# 7. メイン処理
# =============================================================================
def main():
  state = State.TITLE
  menu_cursor = 0
  pg.init()
  screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
  world_screen = pg.Surface((SCREEN_W, SCREEN_H))

  pg.display.set_caption("東方弾幕バトル")
  clock = pg.time.Clock()

  start_title = pg.font.SysFont("msgothic", 50)
  font = pg.font.SysFont("msgothic", 30)
  small_font = pg.font.SysFont("msgothic", 25)
  huge_font = pg.font.SysFont("msgothic", 80)

  particles = []
  move_vecs = [VEC(0, -1), VEC(1, 0), VEC(0, 1), VEC(-1, 0)]

  reimu = Char('霊夢', (2, 4), './data/img/reimu.png', pg.Color('RED'), 25)
  marisa = AI('魔理沙', (13, 4), './data/img/marisa.png', pg.Color('YELLOW'), 30)

  countdown_start_tick = 0
  countdown_val = 3
  shake_timer = 0

  running = True
  while running:
    screen.fill((0, 0, 0))
    world_screen.fill((30, 30, 40))

    for event in pg.event.get():
      if event.type == pg.QUIT:
        running = False

      if state == State.TITLE:
        if event.type == pg.KEYDOWN:
          if event.key == pg.K_UP: menu_cursor = 0
          if event.key == pg.K_DOWN: menu_cursor = 1
          if event.key == pg.K_SPACE:
            if menu_cursor == 0:
              reimu.hp = reimu.max_hp
              reimu.pos = VEC(2, 4)
              reimu.bullets = []
              reimu.invincible_timer = 0
              reimu.is_awakened = False
              reimu.is_dying = False

              marisa.hp = marisa.max_hp
              marisa.pos = VEC(13, 4)
              marisa.bullets = []
              marisa.invincible_timer = 0
              marisa.is_awakened = False
              marisa.is_dying = False

              particles = []
              state = State.COUNTDOWN
              countdown_val = 3
              countdown_start_tick = pg.time.get_ticks()
            else:
              running = False

      if state == State.OVER:
        if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
          state = State.TITLE

    # --- 更新と描画 ---
    shake_offset = (0, 0)
    if shake_timer > 0:
      shake_timer -= 1
      shake_offset = (random.randint(-4, 4), random.randint(-4, 4))

    if state == State.TITLE:
      draw_neon_text(screen, start_title, "東方弾幕バトル",
                     pg.Color('red'), (SCREEN_W // 2, 100))
      opts = ["開始", "終了"]
      for i, opt in enumerate(opts):
        color = ('blue') if i == menu_cursor else ('WHITE')
        txt = font.render(opt, True, color)
        pos = (SCREEN_W // 2 - txt.get_width() // 2, 250 + i * 60)
        screen.blit(txt, pos)
        if i == menu_cursor:
          pg.draw.polygon(screen, ('WHITE'), [
                          (pos[0] - 30, pos[1]), (pos[0] - 10, pos[1] + 15), (pos[0] - 30, pos[1] + 30)])
      info = small_font.render(
          "矢印キーで移動、SPACEで決定/攻撃、vでスペシャル攻撃", True, ('white'))
      screen.blit(
          info, (SCREEN_W // 2 - info.get_width() // 2, SCREEN_H - 50))

    elif state == State.COUNTDOWN:
      frame = pg.time.get_ticks() // 50
      for y in range(0, SCREEN_H, CHIP): pg.draw.line(
          world_screen, (50, 50, 60), (0, y), (SCREEN_W, y))
      for x in range(0, SCREEN_W, CHIP): pg.draw.line(
          world_screen, (50, 50, 60), (x, 0), (x, SCREEN_H))
      reimu.draw(world_screen, frame)
      marisa.draw(world_screen, frame)

      screen.blit(world_screen, (0, 0))

      pg.draw.rect(screen, 'RED', (10, 10, reimu.hp * 10, 15))
      pg.draw.rect(screen, 'WHITE', (10, 10, reimu.hp * 10, 15), 1)
      enemy_bar_w = marisa.hp * 10
      pg.draw.rect(screen, 'YELLOW', (SCREEN_W - 10 -
                                      enemy_bar_w, 10, enemy_bar_w, 15))
      pg.draw.rect(screen, 'WHITE', (SCREEN_W - 10 -
                                     enemy_bar_w, 10, enemy_bar_w, 15), 1)

      elapsed = pg.time.get_ticks() - countdown_start_tick
      if elapsed < 1000: txt, c = "3", "CYAN"
      elif elapsed < 2000: txt, c = "2", "YELLOW"
      elif elapsed < 3000: txt, c = "1", "RED"
      elif elapsed < 4000: txt, c = "GO!", "WHITE"
      else: state = State.PLAY

      draw_neon_text(screen, huge_font, txt, pg.Color(c),
                     (SCREEN_W // 2, SCREEN_H // 2))

    elif state == State.PLAY:
      keys = pg.key.get_pressed()

      # プレイヤー操作（死亡時は操作不可）
      if not reimu.is_dying:
        if reimu.move_vec.length() == 0:
          mv = -1
          if keys[pg.K_UP]: mv = 0
          if keys[pg.K_RIGHT]: mv = 1
          if keys[pg.K_DOWN]: mv = 2
          if keys[pg.K_LEFT]: mv = 3
          if mv != -1:
            reimu.dir = mv
            next_p = reimu.pos + move_vecs[mv]
            if (0 <= next_p.x < MAP_SIZE.x and 0 <= next_p.y < MAP_SIZE.y and next_p != marisa.pos):
              reimu.move_vec = move_vecs[mv]

        current_dir_vec = move_vecs[reimu.dir]
        if keys[pg.K_SPACE]: reimu.shoot(current_dir_vec, marisa, "N")
        if keys[pg.K_v]: reimu.shoot(current_dir_vec, marisa, "S")

      reimu.update()
      if reimu.invincible_timer > 0: reimu.invincible_timer -= 1

      # プレイヤーの死亡演出更新
      if reimu.is_dying:
        reimu.death_timer -= 1
        if reimu.death_timer <= 0:
          state = State.OVER

      # 魔理沙の更新
      if not marisa.is_dying:
        marisa.think(reimu)
        marisa.update()
        if marisa.invincible_timer > 0: marisa.invincible_timer -= 1
      else:
        # 死亡演出中の更新
        marisa.death_timer -= 1
        if marisa.death_timer <= 0:
          state = State.OVER

      # --- ゲーム内世界の描画 ---
      for y in range(0, SCREEN_H, CHIP): pg.draw.line(
          world_screen, (50, 50, 60), (0, y), (SCREEN_W, y))
      for x in range(0, SCREEN_W, CHIP): pg.draw.line(
          world_screen, (50, 50, 60), (x, 0), (x, SCREEN_H))

      frame = pg.time.get_ticks() // 50
      reimu.draw(world_screen, frame)
      marisa.draw(world_screen, frame)

      # 当たり判定 & シェイク発生
      # 死亡演出中はお互いに当たり判定を処理しない（既に死んでいるので）
      if not reimu.is_dying and not marisa.is_dying:
        for attacker, defender in [(reimu, marisa), (marisa, reimu)]:
          for bullet in attacker.bullets:
            if bullet.active and bullet.get_rect().colliderect(defender.get_hitbox()):
              bullet.active = False
              if defender.invincible_timer <= 0:
                defender.hp -= bullet.damage
                defender.invincible_timer = 20
                shake_timer = 15
                hit_color = pg.Color('YELLOW')
                for _ in range(5): particles.append(
                    Particle(bullet.pos * CHIP, hit_color))

                # HPが0になったら死亡演出開始
                if defender.hp <= 0:
                  defender.hp = 0
                  defender.is_dying = True
                  defender.death_timer = 80  # 2秒間 (40FPS * 2)

      for p in particles:
        p.update()
        p.draw(world_screen)
      particles = [p for p in particles if p.life > 0]

      screen.blit(world_screen, shake_offset)

      # UI描画
      pg.draw.rect(screen, 'RED', (10, 10, reimu.hp * 10, 15))
      pg.draw.rect(screen, 'WHITE', (10, 10, reimu.hp * 10, 15), 1)
      screen.blit(small_font.render(
          f"{reimu.name}", True, pg.Color('RED')), (10, 30))

      enemy_bar_w = marisa.hp * 10
      bar_color = 'yellow' if marisa.is_awakened else 'YELLOW'
      pg.draw.rect(screen, bar_color, (SCREEN_W - 10 -
                                       enemy_bar_w, 10, enemy_bar_w, 15))
      pg.draw.rect(screen, 'YELLOW', (SCREEN_W - 10 -
                                      enemy_bar_w, 10, enemy_bar_w, 15), 1)
      m_text = small_font.render(
          f"{marisa.name}", True, pg.Color(bar_color))
      m_text_rect = m_text.get_rect(topright=(SCREEN_W - 10, 30))
      screen.blit(m_text, m_text_rect)

    elif state == State.OVER:
      # プレイ画面を薄暗く残す
      # 死亡しているキャラは消えた状態で描画される
      frame = pg.time.get_ticks() // 50
      for y in range(0, SCREEN_H, CHIP): pg.draw.line(
          world_screen, (50, 50, 60), (0, y), (SCREEN_W, y))
      for x in range(0, SCREEN_W, CHIP): pg.draw.line(
          world_screen, (50, 50, 60), (x, 0), (x, SCREEN_H))
      reimu.draw(world_screen, frame)
      marisa.draw(world_screen, frame)
      screen.blit(world_screen, (0, 0))

      overlay = pg.Surface((SCREEN_W, SCREEN_H))
      overlay.set_alpha(150)  # 少し暗く
      overlay.fill((0, 0, 0))
      screen.blit(overlay, (0, 0))

      winner = "霊夢" if marisa.hp <= 0 else "魔理沙"
      win_color = pg.Color(
          'RED') if winner == "霊夢" else pg.Color('yellow')

      draw_neon_text(
          screen, huge_font, f"{winner} WIN!", win_color, (SCREEN_W // 2, SCREEN_H // 2 - 40))

      blink = (pg.time.get_ticks() // 500) % 2 == 0
      if blink:
        draw_neon_text(screen, small_font, "スペースキーでタイトルへ戻る", pg.Color(
            'WHITE'), (SCREEN_W // 2, SCREEN_H // 2 + 60))

    pg.display.flip()
    clock.tick(50)

  pg.quit()

if __name__ == "__main__":
  main()
