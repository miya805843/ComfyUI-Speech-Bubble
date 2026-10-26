# ComfyUI-Speech-Bubble

[English](README.md) | [日本語 (README_JP.md)](README_JP.md)

---

A versatile, high-quality custom node for **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** that overlays comic/manga speech bubbles and text onto generated images in post-processing.

You can easily embed readable, beautifully rendered Japanese dialogue (vertical & horizontal) or multi-language text, thought balloons, shout bubbles, and narration boxes directly after image generation.

---

### Preview

| Horizontal Dialogue (横書き) | Vertical Dialogue (縦書き) |
| :---: | :---: |
| ![Horizontal Speech Bubble Example](horizontal.png) | ![Vertical Speech Bubble Example](vertical.png) |

---

- **Vertical & Horizontal Top/Left-Aligned Layout**:
  - Full support for traditional Japanese vertical text (right-to-left columns, top-to-bottom reading).
  - **Top-aligned (vertical)** and **left-aligned (horizontal)** text positioning, allowing you to easily adjust indentation and line drops simply by inserting full-width spaces (`　`) or blank lines.
  - Pixel-perfect punctuation snapping: Automatically anchors Japanese commas (`、`) and periods (`。`) to the lower-right corner of the preceding character, ensuring authentic manga typesetting across all fonts.
  - Automatic 90-degree rotation for brackets (`（）`, `「」`), dashes, and long sound marks (`ー`).
- **4 Manga Bubble Styles with Procedural Randomization**:
  - `ellipse`: Classic smooth speech balloon.
  - `rounded_rect`: Narration box or modern chat bubble.
  - `thought`: Fluffy cloud-like thought balloon with trailing floating dots.
  - `shout`: Dynamic explosion balloon with sharp, hand-drawn manga flash spikes.
  - **Procedural Seed Control**: Use the `seed` parameter with ComfyUI's native randomize feature to generate unique organic cloud shapes and spike bursts on every run!
- **Tail Direction and Length Control**:
  - Point the tail toward the speaker's mouth (`bottom_left`, `bottom_right`, `top_left`, `top_right`, or `none`).
  - Use the `tail_length` slider to reach distant characters smoothly.
- **Independent Bubble Opacity**:
  - Adjust `bubble_opacity` to make the bubble background semi-transparent while keeping text and border outlines 100% crisp and readable.
- **True Font Name Auto-Detection**:
  - Directly inspects TrueType/OpenType binary metadata (Name Table) to display official localized font family names (e.g., `源暎アンチック v5`, `07やさしさアンチック`, `游ゴシック`, `ＭＳ ゴシック`) instead of raw filenames.
  - Automatically discovers installed system fonts on **Windows**, **macOS**, and **Linux**.
  - Drop your favorite manga fonts (`.ttf`, `.otf`, `.ttc`) into the local `fonts/` folder to use them instantly.
- **Text Stroke / Outline (袋文字)**:
  - Add stylized outlines to your text using `text_border_width` and `text_border_color`.
  - Works seamlessly with both horizontal and vertical text layouts (including rotated punctuation, prolonged sound marks, and small kana), dramatically boosting readability and comic appeal.
- **Ultra-Crisp Anti-Aliasing**:
  - Rendered with 2x supersampling and downscaled with the Lanczos filter for smooth outlines without jagged pixels.

---

### Installation

#### Via Git Clone
Navigate to your ComfyUI `custom_nodes` directory:
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/miya805843/ComfyUI-Speech-Bubble.git
```
Then restart ComfyUI.

#### Requirements
- `Pillow >= 9.5.0`
- `numpy`
- `torch` (already included in ComfyUI)

---

### Node Parameters

<p align="center">
  <img src="node.png" alt="ComfyUI Speech Bubble Node" width="400">
</p>

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `image` | `IMAGE` | - | Input image tensor from a generator node (e.g. KSampler). |
| `text` | `STRING` | Multiline | Dialogue or caption text. Full-width spaces (`　`) can be used for indenting. |
| `direction` | `ENUM` | `vertical` | Text direction: `vertical` (Japanese manga style) or `horizontal`. |
| `bubble_type` | `ENUM` | `ellipse` | Bubble shape: `ellipse`, `rounded_rect`, `thought`, or `shout`. |
| `tail_direction` | `ENUM` | `bottom_left`| Direction of the tail: `bottom_left`, `bottom_right`, `top_left`, `top_right`, or `none`. |
| `tail_length` | `FLOAT` | `0.7` | Tail length multiplier (`0.0` to `3.0`). Set to `0.0` for no tail. |
| `pos_x` / `pos_y` | `FLOAT` | `0.5`, `0.35`| Normalized bubble center position on the image (`0.0` to `1.0`). |
| `font_name` | `ENUM` | System Default | Selected font from system fonts or local `fonts/` folder. |
| `font_size` | `INT` | `36` | Font size in pixels. |
| `text_color` | `STRING` | `#000000` | Hex code or color name for dialogue text. |
| `text_border_width` | `INT` | `0` | Outline/stroke thickness in pixels. Set to `0` for no outline. |
| `text_border_color` | `STRING` | `#FFFFFF` | Color of the text outline/stroke. |
| `bubble_color` | `STRING` | `#FFFFFF` | Hex code or color name for the bubble background. |
| `bubble_border_width` | `INT` | `3` | Border thickness for the bubble in pixels. |
| `bubble_border_color` | `STRING` | `#000000` | Outline border color for the bubble. |
| `padding` | `INT` | `24` | Padding between text and bubble boundary. |
| `max_chars_per_line` | `INT` | `10` | Automatic wrapping character limit per column/line. |
| `line_spacing` | `INT` | `6` | Spacing between lines or vertical columns. |
| `thought_bump_size` | `FLOAT` | `1.0` | Size multiplier for thought (cloud) bumps and shout (spike) peak heights (`0.2` to `3.0`). Adjusts cloud fluffiness or shout spike intensity. |
| `seed` | `INT` | `0` | Random seed for procedural shapes (supports `control_after_generate`). |
| `bubble_opacity`| `FLOAT` | `1.0` | (Optional) Background opacity (`0.0` to `1.0`) to reveal hair or background through the bubble. |
| `opacity` | `FLOAT` | `1.0` | (Optional) Overall opacity of the entire speech bubble and text (`0.0` to `1.0`). |

---

### License

This project is licensed under the [MIT License](LICENSE).
