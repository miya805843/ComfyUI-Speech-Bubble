import math
import random
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter, ImageChops


class BubbleDrawer:
    """吹き出しおよびテキストの描画エンジン"""

    # 縦書き時に90度時計回りに回転させる文字
    ROTATE_CHARS = set("ー―ｰ～〜()（）[]［］{}｛｝〈〉《》「」『』【】〔〕…‥=＝")

    # 小書き文字（右上寄りに配置）
    SMALL_CHARS = set("っゃゅょぁぃぅぇぉッャュョァィゥェォ")
    PUNCTUATION_CHARS = set("、。，．")

    @staticmethod
    def parse_color(color_str: str, default: Tuple[int, int, int, int] = (0, 0, 0, 255)) -> Tuple[int, int, int, int]:
        """カラー文字列（#RGB, #RRGGBB, #RRGGBBAA, 名前）を RGBA タプルに変換"""
        try:
            color_str = color_str.strip()
            if color_str.startswith("#") and len(color_str) == 9:
                r = int(color_str[1:3], 16)
                g = int(color_str[3:5], 16)
                b = int(color_str[5:7], 16)
                a = int(color_str[7:9], 16)
                return (r, g, b, a)
            rgba = ImageColor.getrgb(color_str)
            if len(rgba) == 3:
                return (rgba[0], rgba[1], rgba[2], 255)
            return rgba
        except Exception:
            return default

    @classmethod
    def layout_horizontal(
        cls,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_chars_per_line: int,
        line_spacing: int
    ) -> Tuple[List[str], int, int]:
        """横書きテキストの改行レイアウトと全体サイズを計算"""
        raw_lines = text.split("\n")
        lines = []

        for raw_line in raw_lines:
            if not raw_line:
                lines.append("")
                continue
            for i in range(0, len(raw_line), max_chars_per_line):
                lines.append(raw_line[i : i + max_chars_per_line])

        if not lines:
            lines = [" "]

        dummy_img = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy_img)

        max_w = 0
        total_h = 0
        line_heights = []

        for line in lines:
            bbox = draw.textbbox((0, 0), line if line else " ", font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w > max_w:
                max_w = w
            line_heights.append(h)

        total_h = sum(line_heights) + line_spacing * (len(lines) - 1)
        return lines, max_w, total_h

    @classmethod
    def layout_vertical(
        cls,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_chars_per_line: int,
        line_spacing: int
    ) -> Tuple[List[str], int, int]:
        """縦書きテキストの列（カラム）分割と全体サイズを計算（右から左へ並ぶ）"""
        raw_lines = text.split("\n")
        columns = []

        for raw_line in raw_lines:
            if not raw_line:
                columns.append("")
                continue
            for i in range(0, len(raw_line), max_chars_per_line):
                columns.append(raw_line[i : i + max_chars_per_line])

        if not columns:
            columns = [" "]

        dummy_img = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(dummy_img)

        sample_bbox = draw.textbbox((0, 0), "あ", font=font)
        char_size = max(sample_bbox[2] - sample_bbox[0], sample_bbox[3] - sample_bbox[1])

        col_heights = []
        for col in columns:
            h = 0
            for ch in col:
                if ch in cls.PUNCTUATION_CHARS:
                    h += int(char_size * 0.55)
                else:
                    h += char_size
            col_heights.append(h)

        total_h = max(col_heights) if col_heights else char_size
        total_w = len(columns) * char_size + line_spacing * (len(columns) - 1)

        return columns, total_w, total_h

    @classmethod
    def draw_text_content(
        cls,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        text_bbox: Tuple[int, int, int, int],
        direction: str,
        text_color: Tuple[int, int, int, int],
        max_chars_per_line: int,
        line_spacing: int
    ):
        """テキストを描画（前揃え／上揃え・左揃えに対応し空白調整を容易に）"""
        x0, y0, x1, y1 = text_bbox
        box_w = x1 - x0
        box_h = y1 - y0

        if direction == "horizontal":
            lines, content_w, content_h = cls.layout_horizontal(text, font, max_chars_per_line, line_spacing)
            # 上下方向は中央揃え、左右方向は左揃え（前揃え）
            cur_y = y0 + (box_h - content_h) // 2

            for line in lines:
                line_bbox = draw.textbbox((0, 0), line if line else " ", font=font)
                line_h = line_bbox[3] - line_bbox[1]
                cur_x = x0
                draw.text((cur_x, cur_y), line, fill=text_color, font=font)
                cur_y += line_h + line_spacing

        else:
            # 縦書き（左右方向は中央揃え、上下方向は上揃え/前揃え）
            columns, content_w, content_h = cls.layout_vertical(text, font, max_chars_per_line, line_spacing)
            sample_bbox = draw.textbbox((0, 0), "あ", font=font)
            char_w = sample_bbox[2] - sample_bbox[0]
            char_h = sample_bbox[3] - sample_bbox[1]
            char_cell = max(char_w, char_h)

            start_x = x0 + box_w - (box_w - content_w) // 2 - char_cell

            for col_idx, col in enumerate(columns):
                col_x = start_x - col_idx * (char_cell + line_spacing)
                cur_y = y0

                for ch in col:
                    if ch in cls.PUNCTUATION_CHARS:
                        # 句読点（、。）: 実インク領域を精密に取得し、文字セルの右上に確実に吸着
                        temp_img = Image.new("RGBA", (char_cell * 2, char_cell * 2), (0, 0, 0, 0))
                        td = ImageDraw.Draw(temp_img)
                        td.text((char_cell // 2, char_cell // 2), ch, fill=text_color, font=font)
                        ink_bbox = temp_img.getbbox()
                        if ink_bbox:
                            glyph_crop = temp_img.crop(ink_bbox)
                            gw, gh = glyph_crop.size
                            # セル内の右上部（直前の文字の右下肩）
                            target_x = col_x + char_cell - gw - int(char_cell * 0.08)
                            target_y = cur_y + int(char_cell * 0.08)
                            canvas.paste(glyph_crop, (target_x, target_y), glyph_crop)
                        else:
                            draw.text((col_x, cur_y), ch, fill=text_color, font=font)
                        cur_y += int(char_cell * 0.55)

                    elif ch in cls.SMALL_CHARS:
                        # 促音・拗音などの小書き文字（右上寄り）
                        actual_bbox = draw.textbbox((0, 0), ch, font=font)
                        cw = actual_bbox[2] - actual_bbox[0]
                        ch_h = actual_bbox[3] - actual_bbox[1]
                        px = col_x + (char_cell - cw) // 2 + int(char_cell * 0.15)
                        py = cur_y + (char_cell - ch_h) // 2 - int(char_cell * 0.08)
                        draw.text((px, py), ch, fill=text_color, font=font)
                        cur_y += char_cell

                    elif ch in cls.ROTATE_CHARS:
                        # 90度回転して描画（長音記号や括弧）
                        if ch in ("ー", "―", "ｰ", "～", "〜"):
                            draw_ch = "丨"
                            actual_bbox = draw.textbbox((0, 0), draw_ch, font=font)
                            cw = actual_bbox[2] - actual_bbox[0]
                            ch_h = actual_bbox[3] - actual_bbox[1]
                            px = col_x + (char_cell - cw) // 2
                            py = cur_y + (char_cell - ch_h) // 2
                            draw.text((px, py), draw_ch, fill=text_color, font=font)
                        else:
                            pad = max(10, char_cell // 2)
                            tw = char_cell + pad * 2
                            ch_img = Image.new("RGBA", (tw, tw), (0, 0, 0, 0))
                            cd = ImageDraw.Draw(ch_img)
                            cb = cd.textbbox((0, 0), ch, font=font)
                            cw = cb[2] - cb[0]
                            ch_h = cb[3] - cb[1]
                            cd.text(((tw - cw) // 2 - cb[0], (tw - ch_h) // 2 - cb[1]), ch, fill=text_color, font=font)
                            rot_ch = ch_img.rotate(-90, resample=Image.Resampling.BILINEAR)
                            target_x = col_x + (char_cell - tw) // 2
                            target_y = cur_y + (char_cell - tw) // 2
                            canvas.paste(rot_ch, (target_x, target_y), rot_ch)
                        cur_y += char_cell

                    else:
                        actual_bbox = draw.textbbox((0, 0), ch, font=font)
                        cw = actual_bbox[2] - actual_bbox[0]
                        ch_h = actual_bbox[3] - actual_bbox[1]
                        px = col_x + (char_cell - cw) // 2
                        py = cur_y + (char_cell - ch_h) // 2
                        draw.text((px, py), ch, fill=text_color, font=font)
                        cur_y += char_cell

    @classmethod
    def render_bubble(
        cls,
        image_size: Tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        direction: str = "vertical",
        bubble_type: str = "ellipse",
        tail_direction: str = "bottom_left",
        tail_length: float = 0.7,
        pos_ratio: Tuple[float, float] = (0.5, 0.5),
        text_color: str = "#000000",
        bubble_color: str = "#FFFFFF",
        border_color: str = "#000000",
        border_width: int = 3,
        padding: int = 24,
        max_chars_per_line: int = 12,
        line_spacing: int = 6,
        bubble_opacity: float = 1.0,
        opacity: float = 1.0,
        seed: int = 0,
    ) -> Image.Image:
        """高品質な吹き出し画像を生成（透明背景RGBA）"""
        img_w, img_h = image_size
        scale = 2  # アンチエイリアス用のオーバーサンプリング倍率
        rng = random.Random(seed)

        # テキストサイズ計算
        if direction == "horizontal":
            _, content_w, content_h = cls.layout_horizontal(text, font, max_chars_per_line, line_spacing)
        else:
            _, content_w, content_h = cls.layout_vertical(text, font, max_chars_per_line, line_spacing)

        # 幾何学的に内接する黄金比サイズ計算（パディングに忠実で、かつ文字が境界線に触れない）
        if bubble_type == "rounded_rect":
            bubble_w = content_w + padding * 2
            bubble_h = content_h + padding * 2
        elif bubble_type == "thought":
            # 通常の楕円吹き出しと完全に同じ目標外枠サイズ
            bubble_w = int(content_w * 1.35 + padding * 2)
            bubble_h = int(content_h * 1.25 + padding * 2)
            bubble_w = max(bubble_w, int(bubble_h * 0.65))
        elif bubble_type == "shout":
            bubble_w = int(content_w * 1.45 + padding * 2)
            bubble_h = int(content_h * 1.35 + padding * 2)
            bubble_w = max(bubble_w, int(bubble_h * 0.65))
            bubble_h = max(bubble_h, int(bubble_w * 0.65))
        else:  # ellipse
            bubble_w = int(content_w * 1.35 + padding * 2)
            bubble_h = int(content_h * 1.25 + padding * 2)
            bubble_w = max(bubble_w, int(bubble_h * 0.65))

        min_dim = int(font.size * 2.2)
        bubble_w = max(bubble_w, min_dim)
        bubble_h = max(bubble_h, min_dim)

        cx = int(img_w * pos_ratio[0])
        cy = int(img_h * pos_ratio[1])

        bx0 = cx - bubble_w // 2
        by0 = cy - bubble_h // 2
        bx1 = bx0 + bubble_w
        by1 = by0 + bubble_h

        b_col_raw = cls.parse_color(bubble_color, (255, 255, 255, 255))
        d_col_raw = cls.parse_color(border_color, (0, 0, 0, 255))
        t_col_raw = cls.parse_color(text_color, (0, 0, 0, 255))

        b_alpha = int(b_col_raw[3] * bubble_opacity * opacity)
        b_col = (b_col_raw[0], b_col_raw[1], b_col_raw[2], max(0, min(255, b_alpha)))

        d_alpha = int(d_col_raw[3] * opacity)
        d_col = (d_col_raw[0], d_col_raw[1], d_col_raw[2], max(0, min(255, d_alpha)))

        t_alpha = int(t_col_raw[3] * opacity)
        t_col = (t_col_raw[0], t_col_raw[1], t_col_raw[2], max(0, min(255, t_alpha)))

        canvas_w = img_w * scale
        canvas_h = img_h * scale
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        sbx0, sby0 = bx0 * scale, by0 * scale
        sbx1, sby1 = bx1 * scale, by1 * scale
        scx, scy = cx * scale, cy * scale
        sbw, sbh = bubble_w * scale, bubble_h * scale
        sb_width = border_width * scale

        shape_mask = Image.new("L", (canvas_w, canvas_h), 0)
        mask_draw = ImageDraw.Draw(shape_mask)

        # 形状に応じたシルエットを白(255)で塗りつぶし
        if bubble_type == "ellipse":
            cls._draw_ellipse_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction, tail_length)
        elif bubble_type == "rounded_rect":
            cls._draw_rounded_rect_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction, tail_length)
        elif bubble_type == "thought":
            cls._draw_thought_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction, tail_length, rng)
        elif bubble_type == "shout":
            cls._draw_shout_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction, tail_length, rng)

        # 枠線（外側拡張下敷き方式で境界線の隙間を完全に排除）
        if sb_width > 0 and d_col[3] > 0:
            kernel_size = sb_width * 2 + 1
            dilated_mask = shape_mask.filter(ImageFilter.MaxFilter(kernel_size))
            border_layer = Image.new("RGBA", (canvas_w, canvas_h), d_col)
            canvas.paste(border_layer, (0, 0), dilated_mask)

        # 吹き出し内側の塗りつぶし
        if b_col[3] > 0:
            fill_layer = Image.new("RGBA", (canvas_w, canvas_h), b_col)
            canvas.paste(fill_layer, (0, 0), shape_mask)

        # 思考バブル（モコモコ）のしっぽの小丸を描画
        if bubble_type == "thought" and tail_direction != "none":
            cls._draw_thought_tail_dots(canvas, cx * scale, cy * scale, bubble_w * scale / 2, bubble_h * scale / 2, tail_direction, tail_length, b_col, d_col, sb_width, rng)

        scaled_font = font
        try:
            if hasattr(font, "path") and font.path:
                scaled_font = ImageFont.truetype(font.path, size=font.size * scale)
        except Exception:
            pass

        # 吹き出し中央にテキスト配置ボックスを設定（均等マージン）
        tx0 = sbx0 + (sbw - content_w * scale) // 2
        ty0 = sby0 + (sbh - content_h * scale) // 2
        tx1 = tx0 + content_w * scale
        ty1 = ty0 + content_h * scale
        text_bbox = (tx0, ty0, tx1, ty1)

        cls.draw_text_content(
            canvas,
            draw,
            text,
            scaled_font,
            text_bbox,
            direction,
            t_col,
            max_chars_per_line,
            line_spacing * scale
        )

        result = canvas.resize((img_w, img_h), Image.Resampling.LANCZOS)
        return result

    @classmethod
    def _draw_ellipse_silhouette(cls, draw, x0, y0, x1, y1, tail_dir, tail_length):
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2
        ry = (y1 - y0) / 2
        draw.ellipse([x0, y0, x1, y1], fill=255)
        if tail_dir != "none" and tail_length > 0:
            tail_points = cls._get_tail_points(cx, cy, rx, ry, tail_dir, tail_length)
            if tail_points:
                draw.polygon(tail_points, fill=255)

    @classmethod
    def _draw_rounded_rect_silhouette(cls, draw, x0, y0, x1, y1, tail_dir, tail_length):
        radius = min((x1 - x0), (y1 - y0)) * 0.15
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=255)
        if tail_dir != "none" and tail_length > 0:
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            rx = (x1 - x0) / 2
            ry = (y1 - y0) / 2
            tail_points = cls._get_tail_points(cx, cy, rx, ry, tail_dir, tail_length)
            if tail_points:
                draw.polygon(tail_points, fill=255)

    @classmethod
    def _draw_thought_silhouette(cls, draw, x0, y0, x1, y1, tail_dir, tail_length, rng: random.Random):
        """コブの外縁が外枠サイズ（x0, y0, x1, y1）に一致する、モコモコ雲型を描画"""
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        target_rx = (x1 - x0) / 2
        target_ry = (y1 - y0) / 2

        # コブの数を程よく抑える（周長に応じて9〜12個程度。ふっくら大きなモコモコ感）
        num_bumps = 10
        perimeter = 2 * math.pi * math.sqrt((target_rx**2 + target_ry**2) / 2)
        bump_r = (perimeter / num_bumps) * 0.60

        # コブの外縁が target_rx, target_ry にピタリと収まるように基準楕円とオフセットを算出
        outer_protrusion = bump_r * 0.30
        base_rx = max(10, target_rx - outer_protrusion)
        base_ry = max(10, target_ry - outer_protrusion)
        bump_inset = bump_r * 0.70  # コブの中心を基準円周より深く内側に配置

        # 1. 基準楕円をベタ塗り（内部の隙間・穴あきを100%防止）
        draw.ellipse([cx - base_rx, cy - base_ry, cx + base_rx, cy + base_ry], fill=255)

        # 2. 基準楕円周上の弧長等間隔サンプリングでコブを配置
        samples = 1000
        angles_table = [0.0]
        total_arc = 0.0
        prev_x = base_rx
        prev_y = 0.0
        for s in range(1, samples + 1):
            t = 2 * math.pi * s / samples
            px = base_rx * math.cos(t)
            py = base_ry * math.sin(t)
            total_arc += math.hypot(px - prev_x, py - prev_y)
            angles_table.append(total_arc)
            prev_x = px
            prev_y = py

        arc_step = total_arc / num_bumps
        for i in range(num_bumps):
            target_arc = i * arc_step
            low = 0
            high = samples
            while low < high:
                mid = (low + high) // 2
                if angles_table[mid] < target_arc:
                    low = mid + 1
                else:
                    high = mid
            angle = 2 * math.pi * low / samples

            # コブの中心を基準楕円の内側に配置
            bx = cx + (base_rx - bump_inset) * math.cos(angle)
            by = cy + (base_ry - bump_inset) * math.sin(angle)
            r = bump_r * rng.uniform(0.95, 1.10)
            draw.ellipse([bx - r, by - r, bx + r, by + r], fill=255)

    @classmethod
    def _draw_shout_silhouette(cls, draw, x0, y0, x1, y1, tail_dir, tail_length, rng: random.Random):
        """外枠サイズ内に収まる、ダイナミックな手描き叫びバブルを描画"""
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2 * 0.78
        ry = (y1 - y0) / 2 * 0.78

        points = []
        num_spikes = rng.randint(22, 28)
        tail_angle = cls._get_tail_angle(tail_dir)

        for i in range(num_spikes * 2):
            base_angle = math.pi * i / num_spikes
            angle = base_angle + rng.uniform(-0.04, 0.04)
            is_outer = (i % 2 == 1)

            if is_outer:
                rhythm = rng.uniform(0.95, 1.25)
                mult = 1.15 * rhythm

                ang_diff = abs((angle - tail_angle + math.pi) % (2 * math.pi) - math.pi)
                if ang_diff < 0.28 and tail_dir != "none":
                    mult = 1.20 + 0.85 * tail_length

                px = cx + rx * mult * math.cos(angle)
                py = cy + ry * mult * math.sin(angle)
            else:
                inner_mult = rng.uniform(0.82, 0.92)
                px = cx + rx * inner_mult * math.cos(angle)
                py = cy + ry * inner_mult * math.sin(angle)

            points.append((px, py))

        draw.polygon(points, fill=255)

    @classmethod
    def _draw_thought_tail_dots(cls, canvas, cx, cy, rx, ry, tail_dir, tail_length, fill, outline, width, rng: random.Random):
        """思考バブルのしっぽ（雲のフチから直接連なる独立した小丸群）を描画"""
        if tail_length <= 0:
            return

        angle = cls._get_tail_angle(tail_dir)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        num_bumps = 10
        perimeter = 2 * math.pi * math.sqrt((rx**2 + ry**2) / 2)
        bump_r = (perimeter / num_bumps) * 0.60

        # 外縁座標（rx, ry）から出発
        edge_x = cx + rx * cos_a
        edge_y = cy + ry * sin_a

        # 通常楕円のしっぽ先端と同じ到達距離にする
        tail_reach = max(rx, ry) * tail_length
        dots = [
            (edge_x + tail_reach * 0.20 * cos_a, edge_y + tail_reach * 0.20 * sin_a, bump_r * 0.40),
            (edge_x + tail_reach * 0.55 * cos_a, edge_y + tail_reach * 0.55 * sin_a, bump_r * 0.26),
            (edge_x + tail_reach * 0.90 * cos_a, edge_y + tail_reach * 0.90 * sin_a, bump_r * 0.16),
        ]

        draw = ImageDraw.Draw(canvas)
        for dx, dy, dr in dots:
            if width > 0 and outline[3] > 0:
                draw.ellipse([dx - dr - width, dy - dr - width, dx + dr + width, dy + dr + width], fill=outline)
            if fill[3] > 0:
                draw.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=fill)

    @classmethod
    def _get_tail_points(cls, cx, cy, rx, ry, tail_dir, tail_length) -> Optional[List[Tuple[float, float]]]:
        angle = cls._get_tail_angle(tail_dir)
        spread = 0.25
        length = max(rx, ry) * tail_length

        p0 = (cx + rx * math.cos(angle - spread), cy + ry * math.sin(angle - spread))
        p1 = (cx + (rx + length) * math.cos(angle), cy + (ry + length) * math.sin(angle))
        p2 = (cx + rx * math.cos(angle + spread), cy + ry * math.sin(angle + spread))

        return [p0, p1, p2]

    @staticmethod
    def _get_tail_angle(tail_dir: str) -> float:
        angles = {
            "bottom_left": 0.75 * math.pi,   # 135度（左下）
            "bottom_right": 0.25 * math.pi,  # 45度（右下）
            "top_left": 1.25 * math.pi,      # 225度（左上）
            "top_right": 1.75 * math.pi,     # 315度（右上）
        }
        return angles.get(tail_dir, 0.75 * math.pi)
