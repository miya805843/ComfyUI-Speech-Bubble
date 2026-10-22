# ComfyUI-Speech-Bubble

[English](#english) | [日本語](#japanese)

---

<a name="english"></a>
## English

A versatile custom node for **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** that overlays beautifully styled comic/manga speech bubbles and text onto generated images.

Say goodbye to messy AI-generated "alien text"! With **ComfyUI-Speech-Bubble**, you can easily add crisp, readable Japanese (vertical & horizontal) or multi-language dialogue, thought balloons, shout bubbles, and narration boxes directly in post-processing.

### ✨ Key Features
- **Vertical & Horizontal Layout**: Full support for Japanese traditional vertical writing (right-to-left, top-to-bottom) with automatic punctuation offsets and rotation for brackets and long sound marks (`ー`).
- **4 Manga Bubble Styles**:
  - `ellipse`: Standard speech balloon.
  - `rounded_rect`: Narration box or modern chat bubble.
  - `thought`: Fluffy cloud-like thought balloon with trailing bubble dots.
  - `shout`: Dynamic spiky explosion balloon for screams or action lines.
- **Tail Direction Control**: Position the tail towards the speaker's mouth (`bottom_left`, `bottom_right`, `top_left`, `top_right`, or `none`).
- **Cross-Platform System Font Auto-Detection**:
  - Automatically discovers all installed system fonts across **Windows**, **macOS**, and **Linux**.
  - Drop your favorite manga fonts (`.ttf`, `.otf`, `.ttc`) into the local `fonts/` folder to use them instantly.
- **Ultra-Crisp Anti-Aliasing**: High-resolution supersampling rendering ensures smooth, clean borders and text without pixelation.
- **Full Styling Freedom**: Customizable font size, line spacing, bubble color, border width, border color, text color, and overall opacity.

---

### 📦 Installation

#### Method 1: Via Git Clone
Navigate to your ComfyUI `custom_nodes` directory:
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/<your-username>/ComfyUI-Speech-Bubble.git
```
Then restart ComfyUI.

#### Requirements
- `Pillow >= 9.5.0`
- `numpy`
- `torch` (already included in ComfyUI)

---

### ⚙️ Node Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `image` | `IMAGE` | - | Input image tensor from previous node (e.g. KSampler). |
| `text` | `STRING` | Multiline | Dialogue or caption text. |
| `direction` | `ENUM` | `vertical` | Text flow direction: `vertical` (Japanese manga style) or `horizontal`. |
| `bubble_type` | `ENUM` | `ellipse` | Shape: `ellipse`, `rounded_rect`, `thought`, or `shout`. |
| `tail_direction` | `ENUM` | `bottom_left`| Tail direction: `bottom_left`, `bottom_right`, `top_left`, `top_right`, or `none`. |
| `tail_length` | `FLOAT` | `0.7` | Tail length multiplier (`0.0` to `3.0`). Reach far characters easily! |
| `pos_x` / `pos_y` | `FLOAT` | `0.5`, `0.35`| Normalized bubble center position (`0.0` to `1.0`). |
| `font_name` | `ENUM` | System Default | Selected font from system fonts or local `fonts/` folder. |
| `font_size` | `INT` | `36` | Font size in pixels. |
| `text_color` | `STRING` | `#000000` | Hex code or color name for the text. |
| `bubble_color` | `STRING` | `#FFFFFF` | Background color of the speech bubble. |
| `border_color` | `STRING` | `#000000` | Outline border color. |
| `border_width` | `INT` | `3` | Border thickness in pixels. |
| `bubble_opacity`| `FLOAT` | `1.0` | Background opacity (`0.0` to `1.0`) to see background/hair through the bubble! |
| `padding` | `INT` | `24` | Padding between text and bubble border. |
| `max_chars_per_line` | `INT` | `10` | Automatic word/character wrap threshold. |
| `line_spacing` | `INT` | `6` | Spacing between lines/columns. |
| `opacity` | `FLOAT` | `1.0` | Overall bubble and text transparency (`0.0` to `1.0`). |

---

<a name="japanese"></a>
## 日本語

画像生成AIで生成した画像に対して、マンガ風の吹き出しと文字をきれいに合成する **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** 用のカスタムノードです。

プロンプト直接指定で崩れてしまいがちな日本語のセリフを、後処理ノードとして美しく、意図した通りのレイアウトで画像に埋め込むことができます。

### ✨ 主な機能
- **縦書き・横書きの両対応**:
  - 日本語漫画の伝統的な「右上から左下」へ流れる縦書きレイアウトを完全サポート。
  - 句読点（、。）の自然な右上配置や、長音記号（ー）や括弧（「」）の縦書き自動回転に対応（全フォント互換）。
- **4種類の漫画吹き出し形状**:
  - `ellipse`: 通常の楕円吹き出し
  - `rounded_rect`: ナレーションや独白、チャット風の角丸長方形
  - `thought`: 心の声用のモコモコ雲型（大小のコブによる自然なふんわり形状＋思考の泡）
  - `shout`: 叫び・驚き・大声用のトゲトゲ爆発型（手描きフラッシュ感のあるダイナミックなトゲ）
- **しっぽ（尻尾）の向きと長さの調整**:
  - キャラクターの口元に合わせて `bottom_left`（左下）、`bottom_right`（右下）、`top_left`（左上）、`top_right`（右上）、`none`（なし）から選択可能。
  - `tail_length`（尻尾の長さ）スライダーにより、遠くにいるキャラクターの口元まで柔軟に尻尾を伸ばせます。
- **吹き出し背景の透過率設定**:
  - `bubble_opacity` により、文字や枠線のクッキリ感を保ったまま、吹き出しの背景だけを半透明にしてイラストや髪の毛を透かすことが可能。
- **OSシステムフォント自動検出 & 独自フォント追加**:
  - Windows, macOS, Linux のPCにインストールされているフォントを自動検出して選択リストに表示。
  - プロジェクト内の `fonts/` ディレクトリにお好みの漫画用フリーフォント（`.ttf`, `.otf` 等）を置くだけで即座に使用可能。
- **高品位アンチエイリアス処理**:
  - スーパーサンプリングによるレンダリングで、縮小時も滑らかでジャギーのない境界線を実現。

---

### 📦 インストール方法

ComfyUIの `custom_nodes` ディレクトリにクローンしてください：
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/<your-username>/ComfyUI-Speech-Bubble.git
```
その後、ComfyUIを起動（または再起動）してください。

---

### 📄 ライセンス
[MIT License](LICENSE)
