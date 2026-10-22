import os
import sys
import glob
from pathlib import Path
from typing import Dict, List, Optional
from PIL import ImageFont


class FontManager:
    """OSごとのシステムフォントおよびカスタムフォントを検出・管理するクラス"""

    _cache_fonts: Optional[Dict[str, str]] = None

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
            # Windows
            windir = os.environ.get("WINDIR", r"C:\Windows")
            dirs.append(Path(windir) / "Fonts")
            # ユーザーフォント (Windows 10/11)
            local_appdata = os.environ.get("LOCALAPPDATA")
            if local_appdata:
                dirs.append(Path(local_appdata) / "Microsoft" / "Windows" / "Fonts")

        elif sys.platform.startswith("darwin"):
            # macOS
            dirs.extend([
                Path("/System/Library/Fonts"),
                Path("/Library/Fonts"),
                Path.home() / "Library" / "Fonts",
            ])

        else:
            # Linux / その他 Unix
            dirs.extend([
                Path("/usr/share/fonts"),
                Path("/usr/local/share/fonts"),
                Path.home() / ".fonts",
                Path.home() / ".local" / "share" / "fonts",
            ])

        return [d for d in dirs if d.exists()]

    @classmethod
    def scan_fonts(cls, force_refresh: bool = False) -> Dict[str, str]:
        """利用可能なフォント（.ttf, .otf, .ttc）を走査して {表示名: ファイルパス} の辞書を返す"""
        if cls._cache_fonts is not None and not force_refresh:
            return cls._cache_fonts

        fonts: Dict[str, str] = {}
        extensions = ("*.ttf", "*.otf", "*.ttc", "*.TTF", "*.OTF", "*.TTC")

        # 補助: matplotlib.font_manager が利用可能なら正確なファミリー名を取得
        mpl_fonts = {}
        try:
            from matplotlib import font_manager
            for font_entry in font_manager.fontManager.ttflist:
                try:
                    fpath = os.path.abspath(font_entry.fname)
                    fname = font_entry.name
                    if os.path.exists(fpath):
                        mpl_fonts[fpath] = fname
                except Exception:
                    continue
        except ImportError:
            pass

        font_dirs = cls.get_font_directories()
        for font_dir in font_dirs:
            for ext in extensions:
                for file_path in font_dir.rglob(ext):
                    try:
                        abs_path = str(file_path.resolve())
                        # 表示名の解決
                        if abs_path in mpl_fonts:
                            display_name = mpl_fonts[abs_path]
                        else:
                            display_name = file_path.stem

                        # 重複がある場合はパスの区別をつける
                        if display_name in fonts and fonts[display_name] != abs_path:
                            display_name = f"{display_name} ({file_path.name})"

                        fonts[display_name] = abs_path
                    except Exception:
                        continue

        # フォントが全く見つからなかった場合のフォールバック（Pillowデフォルト）
        if not fonts:
            fonts["Default"] = ""

        # ソートして保持
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

        # 推奨される日本語・汎用フォント候補（優先順）
        preferred_patterns = [
            "meiryo", "msgothic", "ms gothic", "yugoth", "yu gothic", "biz udp", "biz ud", "biz umincho",  # Windows
            "hiragino", "apple gothic",  # macOS
            "noto sans cjk", "noto cjk", "takao", "ipagothic", "vl gothic",  # Linux
            "gothic", "mincho",
            "arial", "dejavu sans", "segoe ui"  # 欧文フォールバック
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

        # パスが存在しないか失敗した場合はデフォルトフォント
        try:
            # デフォルトのフリータイプフォントを試行
            default_name = cls.get_default_font_name()
            alt_path = fonts.get(default_name)
            if alt_path and os.path.exists(alt_path):
                return ImageFont.truetype(alt_path, size=size)
        except Exception:
            pass

        return ImageFont.load_default()
