import math
import re
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter, ImageChops


class BubbleDrawer:
    """吹き出しおよびテキストの描画エンジン"""

    # 縦書き時に90度時計回りに回転させる文字
    ROTATE_CHARS = {
        "ー": "丨", "―": "丨", "ｰ": "丨", "～": "≀", "〜": "≀",
        "（": "︵", "）": "︶", "(": "︵", ")": "︶",
        "〔": "︹", "〕": "︺", "【": "︻", "】": "︼",
        "［": "﹇", "］": "﹈", "[": "﹇", "]": "﹈",
        "｛": "︷", "｝": "︸", "{": "︷", "}": "︸",
        "〈": "︿", "〉": "﹀", "《": "︽", "》": "︾",
        "「": "﹁", "」": "﹂", "『": "﹃", "』": "﹄",
        "…": "⋮", "‥": "︰", "=": "॥", "＝": "॥",
    }

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

        # 1文字あたりの標準サイズ
        sample_bbox = draw.textbbox((0, 0), "あ", font=font)
        char_size = max(sample_bbox[2] - sample_bbox[0], sample_bbox[3] - sample_bbox[1])

        # 句読点を考慮した各列の高さを算出
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
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont,
        text_bbox: Tuple[int, int, int, int],
        direction: str,
        text_color: Tuple[int, int, int, int],
        max_chars_per_line: int,
        line_spacing: int
    ):
        """指定領域の中央にテキストを描画"""
        x0, y0, x1, y1 = text_bbox
        box_w = x1 - x0
        box_h = y1 - y0

        if direction == "horizontal":
            lines, content_w, content_h = cls.layout_horizontal(text, font, max_chars_per_line, line_spacing)
            cur_y = y0 + (box_h - content_h) // 2

            for line in lines:
                line_bbox = draw.textbbox((0, 0), line if line else " ", font=font)
                line_w = line_bbox[2] - line_bbox[0]
                line_h = line_bbox[3] - line_bbox[1]
                cur_x = x0 + (box_w - line_w) // 2
                draw.text((cur_x, cur_y), line, fill=text_color, font=font)
                cur_y += line_h + line_spacing

        else:
            # 縦書き（右から左へ）
            columns, content_w, content_h = cls.layout_vertical(text, font, max_chars_per_line, line_spacing)
            sample_bbox = draw.textbbox((0, 0), "あ", font=font)
            char_w = sample_bbox[2] - sample_bbox[0]
            char_h = sample_bbox[3] - sample_bbox[1]
            char_cell = max(char_w, char_h)

            start_x = x0 + box_w - (box_w - content_w) // 2 - char_cell

            for col_idx, col in enumerate(columns):
                col_x = start_x - col_idx * (char_cell + line_spacing)

                # 列全体の高さを計算して垂直中央寄せ
                col_h = 0
                for ch in col:
                    if ch in cls.PUNCTUATION_CHARS:
                        col_h += int(char_cell * 0.55)
                    else:
                        col_h += char_cell

                cur_y = y0 + (box_h - col_h) // 2

                for ch in col:
                    # 句読点（直前の文字の右上に寄せる）
                    if ch in cls.PUNCTUATION_CHARS:
                        actual_bbox = draw.textbbox((0, 0), ch, font=font)
                        # 右上に配置
                        px = col_x + char_cell - actual_bbox[2] - int(char_cell * 0.12)
                        py = cur_y - actual_bbox[1] + int(char_cell * 0.05)
                        draw.text((px, py), ch, fill=text_color, font=font)
                        cur_y += int(char_cell * 0.55)

                    elif ch in cls.SMALL_CHARS:
                        # 促音・拗音などの小書き文字
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
                            # 括弧等: フォントの未収録を避けるためPillowで90度回転
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
                            draw._image.paste(rot_ch, (target_x, target_y), rot_ch)
                        cur_y += char_cell

                    else:
                        # 通常文字
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
    ) -> Image.Image:
        """高品質な吹き出し画像を生成（透明背景RGBA）"""
        img_w, img_h = image_size
        scale = 2  # アンチエイリアス用のオーバーサンプリング倍率

        # テキストサイズ計算
        if direction == "horizontal":
            _, content_w, content_h = cls.layout_horizontal(text, font, max_chars_per_line, line_spacing)
        else:
            _, content_w, content_h = cls.layout_vertical(text, font, max_chars_per_line, line_spacing)

        # 吹き出し内包サイズ
        pad_x = padding
        pad_y = padding
        if bubble_type == "ellipse":
            pad_x = int(padding * 1.5)
            pad_y = int(padding * 1.5)
        elif bubble_type == "thought":
            pad_x = int(padding * 2.2)
            pad_y = int(padding * 1.8)
        elif bubble_type == "shout":
            pad_x = int(padding * 1.8)
            pad_y = int(padding * 1.8)

        bubble_w = content_w + pad_x * 2
        bubble_h = content_h + pad_y * 2

        if bubble_type == "thought":
            # 雲型は縦長すぎるとコブと干渉するため丸みを持たせる
            bubble_w = max(bubble_w, int(bubble_h * 0.75))

        # 最小サイズ制限
        min_dim = int(font.size * 2.2)
        bubble_w = max(bubble_w, min_dim)
        bubble_h = max(bubble_h, min_dim)

        # 配置中心座標
        cx = int(img_w * pos_ratio[0])
        cy = int(img_h * pos_ratio[1])

        # 吹き出し境界
        bx0 = cx - bubble_w // 2
        by0 = cy - bubble_h // 2
        bx1 = bx0 + bubble_w
        by1 = by0 + bubble_h

        # カラー解析
        b_col_raw = cls.parse_color(bubble_color, (255, 255, 255, 255))
        d_col_raw = cls.parse_color(border_color, (0, 0, 0, 255))
        t_col_raw = cls.parse_color(text_color, (0, 0, 0, 255))

        # 透過率の適用:
        # bubble_color には bubble_opacity * opacity を反映（背景透過）
        b_alpha = int(b_col_raw[3] * bubble_opacity * opacity)
        b_col = (b_col_raw[0], b_col_raw[1], b_col_raw[2], max(0, min(255, b_alpha)))

        # 枠線とテキストには全体の opacity を反映
        d_alpha = int(d_col_raw[3] * opacity)
        d_col = (d_col_raw[0], d_col_raw[1], d_col_raw[2], max(0, min(255, d_alpha)))

        t_alpha = int(t_col_raw[3] * opacity)
        t_col = (t_col_raw[0], t_col_raw[1], t_col_raw[2], max(0, min(255, t_alpha)))

        # 高解像度キャンバス準備
        canvas_w = img_w * scale
        canvas_h = img_h * scale
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        sbx0, sby0 = bx0 * scale, by0 * scale
        sbx1, sby1 = bx1 * scale, by1 * scale
        scx, scy = cx * scale, cy * scale
        sbw, sbh = bubble_w * scale, bubble_h * scale
        sb_width = border_width * scale

        # マスクによる完全一体化描画
        shape_mask = Image.new("L", (canvas_w, canvas_h), 0)
        mask_draw = ImageDraw.Draw(shape_mask)

        # 形状に応じたシルエットを白(255)で塗りつぶし
        if bubble_type == "ellipse":
            cls._draw_ellipse_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction, tail_length)
        elif bubble_type == "rounded_rect":
            cls._draw_rounded_rect_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction, tail_length)
        elif bubble_type == "thought":
            cls._draw_thought_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction, tail_length)
        elif bubble_type == "shout":
            cls._draw_shout_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction, tail_length)

        # 枠線（ボーダー）の描画
        if sb_width > 0 and d_col[3] > 0:
            kernel_size = sb_width * 2 + 1
            dilated_mask = shape_mask.filter(ImageFilter.MaxFilter(kernel_size))
            border_mask = ImageChops.subtract(dilated_mask, shape_mask)

            border_layer = Image.new("RGBA", (canvas_w, canvas_h), d_col)
            canvas.paste(border_layer, (0, 0), border_mask)

        # 吹き出し内側の塗りつぶし（背景透過を反映）
        if b_col[3] > 0:
            fill_layer = Image.new("RGBA", (canvas_w, canvas_h), b_col)
            canvas.paste(fill_layer, (0, 0), shape_mask)

        # 思考バブル（モコモコ）のしっぽの小丸を描画
        if bubble_type == "thought" and tail_direction != "none":
            cls._draw_thought_tail_dots(canvas, cx * scale, cy * scale, bubble_w * scale / 2, bubble_h * scale / 2, tail_direction, tail_length, b_col, d_col, sb_width)

        # テキスト描画用拡大フォント
        scaled_font = font
        try:
            if hasattr(font, "path") and font.path:
                scaled_font = ImageFont.truetype(font.path, size=font.size * scale)
        except Exception:
            pass

        # テキスト描画
        text_bbox = (sbx0 + pad_x * scale, sby0 + pad_y * scale, sbx1 - pad_x * scale, sby1 - pad_y * scale)
        cls.draw_text_content(
            draw,
            text,
            scaled_font,
            text_bbox,
            direction,
            t_col,
            max_chars_per_line,
            line_spacing * scale
        )

        # Lanczos で元解像度に縮小
        result = canvas.resize((img_w, img_h), Image.Resampling.LANCZOS)
        return result

    @classmethod
    def _draw_ellipse_silhouette(cls, draw, x0, y0, x1, y1, tail_dir, tail_length):
        """楕円としっぽの白マスクを描画"""
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
        """角丸長方形としっぽの白マスクを描画"""
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
    def _draw_thought_silhouette(cls, draw, x0, y0, x1, y1, tail_dir, tail_length):
        """より自然でふわふわした雲型思考バブルの白マスクを描画"""
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2
        ry = (y1 - y0) / 2

        # 内側楕円で土台を確保
        draw.ellipse([cx - rx * 0.85, cy - ry * 0.85, cx + rx * 0.85, cy + ry * 0.85], fill=255)

        # 14個の大小のリズムを持ったモコモココブ
        num_bumps = 14
        for i in range(num_bumps):
            angle = 2 * math.pi * i / num_bumps
            # 大小の自然なウェーブ（振幅0.18）
            size_mod = 0.92 + 0.20 * math.sin(angle * 3.0 + 0.4)
            bump_r = min(rx, ry) * 0.33 * size_mod

            bx = cx + rx * 0.90 * math.cos(angle)
            by = cy + ry * 0.90 * math.sin(angle)
            draw.ellipse([bx - bump_r, by - bump_r, bx + bump_r, by + bump_r], fill=255)

    @classmethod
    def _draw_shout_silhouette(cls, draw, x0, y0, x1, y1, tail_dir, tail_length):
        """よりダイナミックで手描きフラッシュ感のあるトゲトゲ叫びバブルの白マスクを描画"""
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2
        ry = (y1 - y0) / 2
        points = []
        num_spikes = 24
        tail_angle = cls._get_tail_angle(tail_dir)

        for i in range(num_spikes * 2):
            angle = math.pi * i / num_spikes
            is_outer = (i % 2 == 1)

            if is_outer:
                # 漫画の手描きフラッシュのような大小のリズム感
                rhythm = 1.0 + 0.22 * math.sin(i * 2.7) + 0.12 * math.cos(i * 1.5)
                mult = 1.15 * rhythm

                # しっぽ方向のトゲを tail_length に応じて鋭く突き出す
                ang_diff = abs((angle - tail_angle + math.pi) % (2 * math.pi) - math.pi)
                if ang_diff < 0.25 and tail_dir != "none":
                    mult = 1.2 + 0.8 * tail_length

                px = cx + rx * mult * math.cos(angle)
                py = cy + ry * mult * math.sin(angle)
            else:
                # 谷（内側）
                px = cx + rx * 0.88 * math.cos(angle)
                py = cy + ry * 0.88 * math.sin(angle)

            points.append((px, py))

        draw.polygon(points, fill=255)

    @classmethod
    def _draw_thought_tail_dots(cls, canvas, cx, cy, rx, ry, tail_dir, tail_length, fill, outline, width):
        """思考バブルのしっぽ（独立した小さな円群）を描画"""
        if tail_length <= 0:
            return

        angle = cls._get_tail_angle(tail_dir)
        dist_base = max(rx, ry) * 1.10
        dist_step = max(rx, ry) * 0.28 * tail_length

        dots = [
            (cx + dist_base * math.cos(angle), cy + dist_base * math.sin(angle), rx * 0.13),
            (cx + (dist_base + dist_step) * math.cos(angle), cy + (dist_base + dist_step) * math.sin(angle), rx * 0.085),
            (cx + (dist_base + dist_step * 2.0) * math.cos(angle), cy + (dist_base + dist_step * 2.0) * math.sin(angle), rx * 0.05),
        ]

        draw = ImageDraw.Draw(canvas)
        for dx, dy, dr in dots:
            if fill[3] > 0:
                draw.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=fill)
            if width > 0 and outline[3] > 0:
                draw.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], outline=outline, width=width)

    @classmethod
    def _get_tail_points(cls, cx, cy, rx, ry, tail_dir, tail_length) -> Optional[List[Tuple[float, float]]]:
        """三角形のしっぽの頂点リストを返す"""
        angle = cls._get_tail_angle(tail_dir)
        spread = 0.25  # しっぽの根本の幅（ラジアン）
        length = max(rx, ry) * tail_length  # しっぽの長さ

        p0 = (cx + rx * math.cos(angle - spread), cy + ry * math.sin(angle - spread))
        p1 = (cx + (rx + length) * math.cos(angle), cy + (ry + length) * math.sin(angle))
        p2 = (cx + rx * math.cos(angle + spread), cy + ry * math.sin(angle + spread))

        return [p0, p1, p2]

    @staticmethod
    def _get_tail_angle(tail_dir: str) -> float:
        """しっぽの向きに応じたラジアン角度を返す"""
        angles = {
            "bottom_left": 0.75 * math.pi,   # 135度（左下）
            "bottom_right": 0.25 * math.pi,  # 45度（右下）
            "top_left": 1.25 * math.pi,      # 225度（左上）
            "top_right": 1.75 * math.pi,     # 315度（右上）
        }
        return angles.get(tail_dir, 0.75 * math.pi)
