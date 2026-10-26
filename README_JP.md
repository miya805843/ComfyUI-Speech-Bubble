# ComfyUI-Speech-Bubble

[English (README.md)](README.md) | [日本語](README_JP.md)

---

画像生成AI（SDXL, Flux, SD1.5など）で生成した画像に対して、マンガ風の吹き出しとテキストを合成する **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** 用のカスタムノードです。
画像生成後のワークフロー上で吹き出しを追加できます。

---

### 表示例・プレビュー

| 横書き吹き出し例（Horizontal） | 縦書き吹き出し例（Vertical） |
| :---: | :---: |
| ![横書き吹き出し例](horizontal.png) | ![縦書き吹き出し例](vertical.png) |

---

- **縦書き・横書きレイアウト**:
  - 日本語漫画の縦書き（右から左への改行）および横書きに対応。
  - 前揃え（縦書きは上揃え、横書きは左揃え）仕様。行頭の全角スペース（`　`）や空白による字下げに対応。
  - 句読点（、。）の配置補正: 横書き用フォントであっても、直前の文字の右下に自動配置。
  - 括弧類（`（）`、`「」`）、ダッシュ、長音記号（`ー`）の自動縦向き回転。
- **4種類の吹き出し形状（シード別ランダム生成対応）**:
  - `ellipse`: 楕円吹き出し
  - `rounded_rect`: 角丸長方形吹き出し（ナレーション・独白向け）
  - `thought`: 雲型吹き出し（思考の泡付き）
  - `shout`: トゲトゲの爆発型吹き出し
  - `seed` パラメータ（ComfyUI標準の `control_after_generate` 対応）により、雲型やトゲの形状バリエーションを生成可能。
- **しっぽ（尻尾）の向きと長さの調整**:
  - 向きは `bottom_left`（左下）、`bottom_right`（右下）、`top_left`（左上）、`top_right`（右上）、`none`（なし）から選択可能。
  - `tail_length` スライダーで長さを調整可能。
- **吹き出し背景の透過率設定**:
  - `bubble_opacity` により、文字や枠線の不透明度を維持したまま、吹き出しの背景のみを透過可能。
- **フォント名の自動検出 & 独自フォント追加**:
  - フォントファイルのメタデータ（Name Table）を解析し、「源暎アンチック v5」「游ゴシック」等の正式なフォント名で選択リストに表示。
  - OS（Windows, macOS, Linux）にインストールされているシステムフォントを自動検出。
  - プロジェクト内の `fonts/` ディレクトリに配置したフォントファイル（`.ttf`, `.otf` 等）も使用可能。
- **文字の縁取り（袋文字 / テキストストローク）**:
  - `text_border_width` と `text_border_color` により、文字の外側に縁取り線を描画。
  - 縦書き（回転文字や促音・句読点を含む）および横書きに対応。
- **カラープレビュー（スウォッチ表示）**:
  - `text_color`、`text_border_color`、`bubble_color`、`bubble_border_color` の各入力欄の右端に、設定された色の見本（スウォッチ四角）を表示。
- **アンチエイリアス処理**:
  - 2倍のスーパーサンプリングレンダリングとLanczos縮小フィルタによる輪郭描画。

---

### インストール方法

#### Git Clone によるインストール
ComfyUIの `custom_nodes` ディレクトリにクローンしてください：
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/miya805843/ComfyUI-Speech-Bubble.git
```
その後、ComfyUIを起動（または再起動）してください。

#### 動作要件
- `Pillow >= 9.5.0`
- `numpy`
- `torch`（ComfyUI環境に含まれています）

---

### ノードパラメータ一覧

<p align="center">
  <img src="node.png" alt="ComfyUI Speech Bubble Node" width="400">
</p>

| パラメータ名 | 型 | デフォルト値 | 説明 |
| :--- | :--- | :--- | :--- |
| `image` | `IMAGE` | - | 前のノード（KSamplerなど）から受け取る元画像。 |
| `text` | `STRING` | 複数行 | セリフまたはテキスト内容。全角スペース（`　`）での字下げ調整に対応。 |
| `direction` | `ENUM` | `vertical` | 文字の方向：`vertical`（日本語縦書き）または `horizontal`（横書き）。 |
| `bubble_type` | `ENUM` | `ellipse` | 吹き出し形状：`ellipse`（楕円）、`rounded_rect`（角丸）、`thought`（雲型）、`shout`（叫び）。 |
| `tail_direction` | `ENUM` | `bottom_left`| しっぽの向き：`bottom_left`、`bottom_right`、`top_left`、`top_right`、`none`（なし）。 |
| `tail_length` | `FLOAT` | `0.7` | しっぽの長さ倍率（`0.0` 〜 `3.0`）。`0.0` でしっぽなし。 |
| `pos_x` / `pos_y` | `FLOAT` | `0.5`, `0.35`| 画像全体に対する吹き出しの中心位置（`0.0` 〜 `1.0`）。 |
| `font_name` | `ENUM` | システム既定 | 検出されたシステムフォントまたは `fonts/` フォルダ内のフォント名。 |
| `font_size` | `INT` | `36` | フォントサイズ（ピクセル単位）。 |
| `text_color` | `STRING` | `#000000` | 文字色（HEXカラーコードまたはカラー名）。 |
| `text_border_width` | `INT` | `0` | 文字の縁取りの太さ（ピクセル単位）。`0` で縁取りなし。 |
| `text_border_color` | `STRING` | `#FFFFFF` | 文字の縁取り（袋文字）の色。 |
| `bubble_color` | `STRING` | `#FFFFFF` | 吹き出し背景色。 |
| `bubble_border_width` | `INT` | `3` | 吹き出し枠線の太さ（ピクセル単位）。 |
| `bubble_border_color` | `STRING` | `#000000` | 吹き出し枠線の色。 |
| `padding` | `INT` | `24` | 文字と吹き出し境界の間のパディング（余白）。 |
| `max_chars_per_line` | `INT` | `10` | 自動改行・改列を行う文字数制限。 |
| `line_spacing` | `INT` | `6` | 行間または列間の余白。 |
| `thought_bump_size` | `FLOAT` | `1.0` | 雲型（thought）のコブの大きさ、および叫び（shout）のトゲの高さ倍率（`0.2` 〜 `3.0`）。 |
| `seed` | `INT` | `0` | 形状ランダムシード（生成後の制御: `randomize` / `fixed` 等対応）。 |
| `bubble_opacity`| `FLOAT` | `1.0` | （任意）吹き出し背景の不透明度（`0.0` 〜 `1.0`）。背景を透かしたい時に使用。 |
| `opacity` | `FLOAT` | `1.0` | （任意）吹き出し全体の不透明度（文字・枠線含む、`0.0` 〜 `1.0`）。 |

---

### ライセンス

本プロジェクトは [MIT License](LICENSE) の下で公開されています。
