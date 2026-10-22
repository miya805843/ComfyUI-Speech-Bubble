import os
import sys
import glob
import struct
from pathlib import Path
from typing import Dict, List, Optional
from PIL import ImageFont


class FontManager:
    """OSごとのシステムフォントおよびカスタムフォントを検出・管理するクラス"""

    _cache_fonts: Optional[Dict[str, str]] = None

    @classmethod
    def extract_font_title(cls, font_path: str) -> str:
        """TTF/OTF/TTCのnameテーブルをバイナリ解析し、正式なフォント名（日本語名を最優先）を取得する"""
        try:
            with open(font_path, "rb") as f:
                header = f.read(4)

                # TTC (TrueType Collection) の場合、先頭フォントのオフセットを取得
                if header == b"ttcf":
                    f.seek(8)
                    num_fonts = struct.unpack(">I", f.read(4))[0]
                    if num_fonts > 0:
                        first_offset = struct.unpack(">I", f.read(4))[0]
                        f.seek(first_offset)
                        header = f.read(4)

                num_tables = struct.unpack(">H", f.read(2))[0]
                f.seek(6, os.SEEK_CUR)  # searchRange, entrySelector, rangeShift

                name_table_offset = None
                for _ in range(num_tables):
                    tag = f.read(4)
                    check_sum = f.read(4)
                    offset, length = struct.unpack(">II", f.read(8))
                    if tag == b"name":
                        name_table_offset = offset
                        break

                if not name_table_offset:
                    return Path(font_path).stem

                # name テーブルの解析
                f.seek(name_table_offset)
                format_type, count, string_offset = struct.unpack(">HHH", f.read(6))

                jp_names: Dict[int, str] = {}
                en_names: Dict[int, str] = {}

                for _ in range(count):
                    pid, eid, lid, nid, length, offset = struct.unpack(">HHHHHH", f.read(12))
                    if nid not in (1, 4):  # 1: Family Name, 4: Full Name
                        continue

                    pos = f.tell()
                    f.seek(name_table_offset + string_offset + offset)
                    raw_bytes = f.read(length)
                    f.seek(pos)

                    try:
                        text = ""
                        if pid == 3:  # Windows
                            text = raw_bytes.decode("utf-16-be", errors="ignore")
                            if lid == 0x0411:  # 日本語
                                jp_names[nid] = text.strip().replace("\x00", "")
                            elif lid in (0x0409, 0):  # 英語
                                en_names[nid] = text.strip().replace("\x00", "")
                        elif pid == 1:  # Macintosh
                            if lid == 11:  # 日本語
                                text = raw_bytes.decode("shift_jis", errors="ignore")
                                jp_names[nid] = text.strip().replace("\x00", "")
                            elif lid == 0:  # 英語
                                text = raw_bytes.decode("mac-roman", errors="ignore")
                                en_names[nid] = text.strip().replace("\x00", "")
                        elif pid == 0:  # Unicode
                            text = raw_bytes.decode("utf-16-be", errors="ignore")
                            en_names[nid] = text.strip().replace("\x00", "")
                    except Exception:
                        continue

                # 日本語Full Name (4) -> 日本語Family Name (1) -> 英語Full Name -> 英語Family Name
                title = jp_names.get(4) or jp_names.get(1) or en_names.get(4) or en_names.get(1)
                if title:
                    return title

        except Exception:
            pass

        return Path(font_path).stem

    @classmethod
    def get_font_directories(cls) -> List[Path]:
        """各OSの標準フォントディレクトリおよびプロジェクト内fontsディレクトリを返す"""
        dirs: List[Path] = []

        # 1. プロジェクト内 fonts ディレクトリ（最優先）
        current_dir = Path(__file__).resolve().parent
        local_fonts_dir = current_dir / "fonts"
        if local_fonts_dir.exists():
            dirs.append(local_fonts_dir)

        # 2. OS別システムフォントディレクトリ
        if sys.platform.startswith("win"):
            windir = os.environ.get("WINDIR", r"C:\Windows")
            dirs.append(Path(windir) / "Fonts")
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                dirs.append(Path(local_appdata) / "Microsoft" / "Windows" / "Fonts")

        elif sys.platform.startswith("darwin"):
            dirs.extend([
                Path("/System/Library/Fonts"),
                Path("/Library/Fonts"),
                Path.home() / "Library" / "Fonts",
            ])

        else:
            dirs.extend([
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
                Path.home() / ".fonts",
                Path.home() / ".local" / "share" / "fonts",
            ])

        return [d for d in dirs if d.exists()]

    @classmethod
    def scan_fonts(cls, force_refresh: bool = False) -> Dict[str, str]:
        """利用可能なフォントを走査して {正式表示名: ファイルパス} の辞書を返す"""
        if cls._cache_fonts is not None and not force_refresh:
            return cls._cache_fonts

        fonts: Dict[str, str] = {}
        extensions = ("*.ttf", "*.otf", "*.ttc", "*.TTF", "*.OTF", "*.TTC")

        font_dirs = cls.get_font_directories()
        for font_dir in font_dirs:
            for ext in extensions:
                for file_path in font_dir.rglob(ext):
                    try:
                        abs_path = str(file_path.resolve())
                        # メタデータから正式フォント名を取得
                        display_name = cls.extract_font_title(abs_path)

                        # 重複回避（同じ名前の別フォントファイルの場合）
                        if display_name in fonts and fonts[display_name] != abs_path:
                            display_name = f"{display_name} ({file_path.name})"

                        fonts[display_name] = abs_path
                    except Exception:
                        continue

        if not fonts:
            fonts["Default"] = ""

        # ソートして保持（日本語文字も考慮した昇順ソート）
        sorted_fonts = dict(sorted(fonts.items(), key=lambda x: x[0].lower()))
        cls._cache_fonts = sorted_fonts
        return sorted_fonts

    @classmethod
    def get_font_names(cls) -> List[str]:
        """ノードのUI選択肢用フォント名リストを返す"""
        fonts = cls.scan_fonts()
        return list(fonts.keys())

    @classmethod
    def get_default_font_name(cls) -> str:
        """OSに応じたおすすめデフォルトフォント名を返す"""
        fonts = cls.scan_fonts()
        font_names = list(fonts.keys())

        preferred_patterns = [
            "やさしさ", "アンチック", "源暎", "源ノ角",
            "meiryo", "メイリオ", "游ゴシック", "msgothic", "ms gothic", "ｍｓ ゴシック",
            "biz udp", "biz ud", "biz umincho",
            "hiragino", "ヒラギノ",
            "noto sans cjk", "noto cjk", "takao", "ipagothic", "vl gothic",
            "gothic", "ゴシック", "mincho", "明朝",
            "arial", "segoe ui"
        ]

        for pattern in preferred_patterns:
            for name in font_names:
                if pattern in name.lower().replace(" ", ""):
                    return name

        return font_names[0] if font_names else "Default"

    @classmethod
    def load_font(cls, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """指定されたフォント名とサイズから ImageFont オブジェクトをロードする"""
        fonts = cls.scan_fonts()
        font_path = fonts.get(font_name)

        if font_path and os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size=size)
            except Exception as e:
                print(f"[SpeechBubble] フォント読み込み失敗: {font_path} ({e})")

        # パスが存在しない場合はデフォルトフォントを試行
        try:
            default_name = cls.get_default_font_name()
            alt_path = fonts.get(default_name)
            if alt_path and os.path.exists(alt_path):
                return ImageFont.truetype(alt_path, size=size)
        except Exception:
            pass

        return ImageFont.load_default()
