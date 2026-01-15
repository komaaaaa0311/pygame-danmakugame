import pygame as pg

def main():

  # 初期化処理
  chip_s = 48  # マップチップの基本サイズ
  map_s = pg.Vector2(16, 9)  # マップの横・縦の配置数

  pg.init()
  pg.display.set_caption('ぼくのかんがえたさいきょうのげーむ II')
  disp_w = int(chip_s * map_s.x)
  disp_h = int(chip_s * map_s.y)
  screen = pg.display.set_mode((disp_w, disp_h))
  clock = pg.time.Clock()
  font = pg.font.Font(None, 15)
  frame = 0
  exit_flag = False
  exit_code = '000'

  # グリッド設定
  grid_c = '#bbbbbb'

  # 自キャラ移動関連【未実装】

  # 自キャラの画像読込み
  reimu_p = pg.Vector2(2, 3)   # 自キャラ位置
  reimu_s = pg.Vector2(48, 64)  # 画面に出力する自キャラサイズ 48x64
  reimu_d = 2  # 自キャラの向き
  reimu_img_raw = pg.image.load('./data/img/reimu.png')
  pose_p = pg.Vector2(24, 64)  # 前向き・2番目のポーズの位置　
  pose_s = pg.Vector2(24, 32)  # ポーズのサイズ
  tmp = reimu_img_raw.subsurface(pg.Rect(pose_p, pose_s))
  reimu_img = pg.transform.scale(tmp, reimu_s)

  # ゲームループ
  while not exit_flag:

    # システムイベントの検出
    cmd_move = -1
    for event in pg.event.get():
      if event.type == pg.QUIT:  # ウィンドウ[X]の押下
        exit_flag = True
        exit_code = '001'
      # 移動用のキー入力の検出【未実装】

    # 背景描画
    screen.fill(pg.Color('WHITE'))

    # グリッド
    for x in range(0, disp_w, chip_s):  # 縦線
      pg.draw.line(screen, grid_c, (x, 0), (x, disp_h))
    for y in range(0, disp_h, chip_s):  # 横線
      pg.draw.line(screen, grid_c, (0, y), (disp_w, y))

    # 移動コマンドの処理【未実装】

    # 自キャラの描画 dp:描画基準点（imgの左上座標）
    dp = pg.Vector2(96, 120)
    screen.blit(reimu_img, dp)

    # フレームカウンタの描画
    frame += 1
    frm_str = f'{frame:05}'
    screen.blit(font.render(frm_str, True, 'BLACK'), (10, 10))

    # 画面の更新と同期
    pg.display.update()
    clock.tick(30)

  # ゲームループ [ここまで]
  pg.quit()
  return exit_code

if __name__ == "__main__":
  code = main()
  print(f'プログラムを「コード{code}」で終了しました。')
