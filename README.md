# ComfyUI-Speech-Bubble

[English](README.md) | [日本語 (README_JP.md)](README_JP.md)

---

A custom node for **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** that overlays comic/manga speech bubbles and text onto generated images.

---

### Preview

| Horizontal Dialogue (横書き) | Vertical Dialogue (縦書き) |
| :---: | :---: |
| ![Horizontal Speech Bubble Example](horizontal.png) | ![Vertical Speech Bubble Example](vertical.png) |

---

- **Vertical & Horizontal Layout**:
  - Supports Japanese vertical text (right-to-left columns) and horizontal text.
  - Top-aligned (vertical) and left-aligned (horizontal) positioning. Indentation can be adjusted with full-width spaces (`　`) or spaces.
  - Punctuation adjustment: Positions commas (`、`) and periods (`。`) to the lower-right of the preceding character for horizontal fonts in vertical mode.
  - Automatic rotation for brackets (`（）`, `「」`), dashes, and prolonged sound marks (`ー`).
- **4 Bubble Styles**:
  - `ellipse`: Elliptical speech balloon.
  - `rounded_rect`: Rounded rectangle (narration box).
  - `thought`: Cloud shape with thought dots.
  - `shout`: Spiked burst bubble.
  - `seed`: Parameter to vary cloud and spike shapes (supports ComfyUI's `control_after_generate`).
- **Tail Direction and Length**:
  - Direction: `bottom_left`, `bottom_right`, `top_left`, `top_right`, or `none`.
  - `tail_length`: Adjusts the tail length multiplier.
- **Bubble Background Opacity**:
  - `bubble_opacity`: Adjusts background transparency while keeping text and border outlines opaque.
- **Font Name Detection & Custom Fonts**:
  - Parses font metadata (Name Table) to display localized font family names.
  - Automatically detects system fonts on Windows, macOS, and Linux.
  - Supports custom fonts placed in the `fonts/` directory (`.ttf`, `.otf`, etc.).
- **Text Stroke / Outline (袋文字)**:
  - `text_border_width` and `text_border_color` add an outline around characters.
  - Supports both vertical and horizontal text layouts.
- **Color Preview Swatches**:
  - Displays color preview swatches next to `text_color`, `text_border_color`, `bubble_color`, and `bubble_border_color` input widgets.
- **Anti-Aliasing**:
  - 2x supersampling with Lanczos downsampling.

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
| `thought_bump_size` | `FLOAT` | `1.0` | Size multiplier for thought (cloud) bumps and shout (spike) heights (`0.2` to `3.0`). |
| `seed` | `INT` | `0` | Random seed for procedural shapes (supports `control_after_generate`). |
| `bubble_opacity`| `FLOAT` | `1.0` | (Optional) Background opacity (`0.0` to `1.0`) to reveal hair or background through the bubble. |
| `opacity` | `FLOAT` | `1.0` | (Optional) Overall opacity of the entire speech bubble and text (`0.0` to `1.0`). |

---

### License

This project is licensed under the [MIT License](LICENSE).
