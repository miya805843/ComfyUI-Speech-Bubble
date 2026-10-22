import math
import re
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageColor


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

    # 縦書き時に右上にシフトする文字（句読点、小書き）
    OFFSET_CHARS = {
        "、": (0.6, -0.6), "。": (0.6, -0.6), ",": (0.5, -0.5), ".": (0.5, -0.5),
        "っ": (0.2, -0.2), "ゃ": (0.2, -0.2), "ゅ": (0.2, -0.2), "ょ": (0.2, -0.2),
        "ぁ": (0.2, -0.2), "ぃ": (0.2, -0.2), "ぅ": (0.2, -0.2), "ぇ": (0.2, -0.2), "ぉ": (0.2, -0.2),
        "ッ": (0.2, -0.2), "ャ": (0.2, -0.2), "ュ": (0.2, -0.2), "ョ": (0.2, -0.2),
        "ァ": (0.2, -0.2), "ィ": (0.2, -0.2), "ゥ": (0.2, -0.2), "ェ": (0.2, -0.2), "ォ": (0.2, -0.2),
    }

    @staticmethod
    def parse_color(color_str: str, default: Tuple[int, int, int, int] = (0, 0, 0, 255)) -> Tuple[int, int, int, int]:
        """カラー文字列（#RGB, #RRGGBB, #RRGGBBAA, 名前）を RGBA タプルに変換"""
        try:
            color_str = color_str.strip()
            if color_str.startswith("#") and len(color_str) == 9:
                # #RRGGBBAA
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

        # サイズ測定用ダミー画像
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

        max_chars_in_col = max(len(col) for col in columns)
        total_h = max_chars_in_col * char_size
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
                col_total_h = len(col) * char_cell
                cur_y = y0 + (box_h - col_total_h) // 2

                for ch in col:
                    # 置換可能文字の処理
                    draw_ch = cls.ROTATE_CHARS.get(ch, ch)
                    # オフセット文字の処理
                    offset_x, offset_y = 0, 0
                    if ch in cls.OFFSET_CHARS:
                        rx, ry = cls.OFFSET_CHARS[ch]
                        offset_x = int(char_cell * rx * 0.5)
                        offset_y = int(char_cell * ry * 0.5)

                    ch_bbox = draw.textbbox((0, 0), draw_ch, font=font)
                    cw = ch_bbox[2] - ch_bbox[0]
                    ch_h = ch_bbox[3] - ch_bbox[1]

                    px = col_x + (char_cell - cw) // 2 + offset_x
                    py = cur_y + (char_cell - ch_h) // 2 + offset_y

                    draw.text((px, py), draw_ch, fill=text_color, font=font)
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
        pos_ratio: Tuple[float, float] = (0.5, 0.5),
        text_color: str = "#000000",
        bubble_color: str = "#FFFFFF",
        border_color: str = "#000000",
        border_width: int = 3,
        padding: int = 24,
        max_chars_per_line: int = 12,
        line_spacing: int = 6,
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
            # 楕円は四隅が削れるためパディングを広めに確保
            pad_x = int(padding * 1.5)
            pad_y = int(padding * 1.5)
        elif bubble_type == "thought":
            pad_x = int(padding * 1.7)
            pad_y = int(padding * 1.7)
        elif bubble_type == "shout":
            pad_x = int(padding * 1.8)
            pad_y = int(padding * 1.8)

        bubble_w = content_w + pad_x * 2
        bubble_h = content_h + pad_y * 2

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
        b_col = cls.parse_color(bubble_color, (255, 255, 255, 255))
        d_col = cls.parse_color(border_color, (0, 0, 0, 255))
        t_col = cls.parse_color(text_color, (0, 0, 0, 255))

        if opacity < 1.0:
            b_col = (b_col[0], b_col[1], b_col[2], int(b_col[3] * opacity))
            d_col = (d_col[0], d_col[1], d_col[2], int(d_col[3] * opacity))
            t_col = (t_col[0], t_col[1], t_col[2], int(t_col[3] * opacity))

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

        # マスクによる完全一体化描画（内側の重なり線を排除し、完璧な外枠を生成）
        shape_mask = Image.new("L", (canvas_w, canvas_h), 0)
        mask_draw = ImageDraw.Draw(shape_mask)

        # 形状に応じたシルエットを白(255)で塗りつぶし
        if bubble_type == "ellipse":
            cls._draw_ellipse_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction)
        elif bubble_type == "rounded_rect":
            cls._draw_rounded_rect_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction)
        elif bubble_type == "thought":
            cls._draw_thought_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction)
        elif bubble_type == "shout":
            cls._draw_shout_silhouette(mask_draw, sbx0, sby0, sbx1, sby1, tail_direction)

        # 枠線（ボーダー）と塗りつぶし（フィル）の合成
        if sb_width > 0:
            from PIL import ImageFilter
            # 奇数のカーネルサイズを計算
            kernel_size = sb_width * 2 + 1
            dilated_mask = shape_mask.filter(ImageFilter.MaxFilter(kernel_size))
            
            # 枠線部分のマスク = 拡張マスク - 内側マスク
            border_mask = Image.new("L", (canvas_w, canvas_h), 0)
            # numpyを使わずPILのImageChopsまたはevalで高速差分
            from PIL import ImageChops
            border_mask = ImageChops.subtract(dilated_mask, shape_mask)

            # 枠線描画
            border_layer = Image.new("RGBA", (canvas_w, canvas_h), d_col)
            canvas.paste(border_layer, (0, 0), border_mask)

        # 吹き出し内側の塗りつぶし
        fill_layer = Image.new("RGBA", (canvas_w, canvas_h), b_col)
        canvas.paste(fill_layer, (0, 0), shape_mask)

        # 思考バブル（モコモコ）のしっぽの小丸を描画
        if bubble_type == "thought" and tail_direction != "none":
            cls._draw_thought_tail_dots(canvas, draw, cx * scale, cy * scale, bubble_w * scale / 2, bubble_h * scale / 2, tail_direction, b_col, d_col, sb_width)

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

        # Lanczos で元解像度に縮小（最高精度のアンチエイリアス）
        result = canvas.resize((img_w, img_h), Image.Resampling.LANCZOS)
        return result

    @classmethod
    def _draw_ellipse_silhouette(cls, draw, x0, y0, x1, y1, tail_dir):
        """楕円としっぽの白マスクを描画"""
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2
        ry = (y1 - y0) / 2
        draw.ellipse([x0, y0, x1, y1], fill=255)
        if tail_dir != "none":
            tail_points = cls._get_tail_points(cx, cy, rx, ry, tail_dir)
            if tail_points:
                draw.polygon(tail_points, fill=255)

    @classmethod
    def _draw_rounded_rect_silhouette(cls, draw, x0, y0, x1, y1, tail_dir):
        """角丸長方形としっぽの白マスクを描画"""
        radius = min((x1 - x0), (y1 - y0)) * 0.15
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=255)
        if tail_dir != "none":
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            rx = (x1 - x0) / 2
            ry = (y1 - y0) / 2
            tail_points = cls._get_tail_points(cx, cy, rx, ry, tail_dir)
            if tail_points:
                draw.polygon(tail_points, fill=255)

    @classmethod
    def _draw_thought_silhouette(cls, draw, x0, y0, x1, y1, tail_dir):
        """モコモコ思考バブルの白マスクを描画"""
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2
        ry = (y1 - y0) / 2
        num_bumps = 18
        bump_r = min(rx, ry) * 0.32

        draw.ellipse([x0, y0, x1, y1], fill=255)
        for i in range(num_bumps):
            angle = 2 * math.pi * i / num_bumps
            bx = cx + rx * 0.9 * math.cos(angle)
            by = cy + ry * 0.9 * math.sin(angle)
            draw.ellipse([bx - bump_r, by - bump_r, bx + bump_r, by + bump_r], fill=255)

    @classmethod
    def _draw_shout_silhouette(cls, draw, x0, y0, x1, y1, tail_dir):
        """トゲトゲ叫びバブルの白マスクを描画"""
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        rx = (x1 - x0) / 2
        ry = (y1 - y0) / 2
        points = []
        num_spikes = 20
        tail_angle = cls._get_tail_angle(tail_dir)

        for i in range(num_spikes * 2):
            angle = math.pi * i / num_spikes
            is_outer = (i % 2 == 1)
            if is_outer:
                mult = 1.15
                if tail_dir != "none" and abs((angle - tail_angle + math.pi) % (2 * math.pi) - math.pi) < 0.25:
                    mult = 1.45
                px = cx + rx * mult * math.cos(angle)
                py = cy + ry * mult * math.sin(angle)
            else:
                px = cx + rx * 0.9 * math.cos(angle)
                py = cy + ry * 0.9 * math.sin(angle)
            points.append((px, py))

        draw.polygon(points, fill=255)

    @classmethod
    def _draw_thought_tail_dots(cls, canvas, draw, cx, cy, rx, ry, tail_dir, fill, outline, width):
        """思考バブルのしっぽ（独立した小さな円）を描画"""
        dots = cls._get_thought_tail_dots(cx, cy, rx, ry, tail_dir)
        for dx, dy, dr in dots:
            draw.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=fill, outline=outline, width=width)

    @classmethod
    def _get_tail_points(cls, cx, cy, rx, ry, tail_dir) -> Optional[List[Tuple[float, float]]]:
        """三角形のしっぽの頂点リストを返す"""
        angle = cls._get_tail_angle(tail_dir)
        spread = 0.25  # しっぽの根本の幅（ラジアン）
        length = max(rx, ry) * 0.7  # しっぽの長さ

        p0 = (cx + rx * math.cos(angle - spread), cy + ry * math.sin(angle - spread))
        p1 = (cx + (rx + length) * math.cos(angle), cy + (ry + length) * math.sin(angle))
        p2 = (cx + rx * math.cos(angle + spread), cy + ry * math.sin(angle + spread))

        return [p0, p1, p2]

    @classmethod
    def _get_thought_tail_dots(cls, cx, cy, rx, ry, tail_dir) -> List[Tuple[float, float, float]]:
        """思考バブル用の小円（x, y, radius）リストを返す"""
        angle = cls._get_tail_angle(tail_dir)
        dist_base = max(rx, ry) * 1.15
        dots = [
            (cx + dist_base * math.cos(angle), cy + dist_base * math.sin(angle), rx * 0.14),
            (cx + (dist_base + rx * 0.25) * math.cos(angle), cy + (dist_base + ry * 0.25) * math.sin(angle), rx * 0.09),
            (cx + (dist_base + rx * 0.45) * math.cos(angle), cy + (dist_base + ry * 0.45) * math.sin(angle), rx * 0.05),
        ]
        return dots

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
