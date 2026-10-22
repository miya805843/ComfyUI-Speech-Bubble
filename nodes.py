import numpy as np
from PIL import Image
from typing import Tuple, Dict, Any

try:
    import torch
except ImportError:
    torch = None

from .font_manager import FontManager
from .bubble_drawer import BubbleDrawer


class SpeechBubbleNode:
    """ComfyUI用 吹き出し＆セリフ合成カスタムノード"""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        font_names = FontManager.get_font_names()
        default_font = FontManager.get_default_font_name()

        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {
                    "multiline": True,
                    "default": "こんにちは！\nComfyUIへようこそ！"
                }),
                "direction": (["vertical", "horizontal"], {
                    "default": "vertical"
                }),
                "bubble_type": (["ellipse", "rounded_rect", "thought", "shout"], {
                    "default": "ellipse"
                }),
                "tail_direction": (["bottom_left", "bottom_right", "top_left", "top_right", "none"], {
                    "default": "bottom_left"
                }),
                "pos_x": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "pos_y": ("FLOAT", {
                    "default": 0.35,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "font_name": (font_names, {
                    "default": default_font
                }),
                "font_size": ("INT", {
                    "default": 36,
                    "min": 8,
                    "max": 256,
                    "step": 1
                }),
                "text_color": ("STRING", {
                    "default": "#000000"
                }),
                "bubble_color": ("STRING", {
                    "default": "#FFFFFF"
                }),
                "border_color": ("STRING", {
                    "default": "#000000"
                }),
                "border_width": ("INT", {
                    "default": 3,
                    "min": 0,
                    "max": 30,
                    "step": 1
                }),
            },
            "optional": {
                "padding": ("INT", {
                    "default": 24,
                    "min": 0,
                    "max": 200,
                    "step": 1
                }),
                "max_chars_per_line": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
                "line_spacing": ("INT", {
                    "default": 6,
                    "min": 0,
                    "max": 50,
                    "step": 1
                }),
                "opacity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply_speech_bubble"
    CATEGORY = "image/postprocessing"

    def apply_speech_bubble(
        self,
        image,
        text: str,
        direction: str,
        bubble_type: str,
        tail_direction: str,
        pos_x: float,
        pos_y: float,
        font_name: str,
        font_size: int,
        text_color: str,
        bubble_color: str,
        border_color: str,
        border_width: int,
        padding: int = 24,
        max_chars_per_line: int = 10,
        line_spacing: int = 6,
        opacity: float = 1.0,
    ):
        if torch is None:
            raise RuntimeError("PyTorchがインストールされていません。")

        # フォント読み込み
        font = FontManager.load_font(font_name, font_size)

        output_images = []
        batch_size = image.shape[0]

        for i in range(batch_size):
            # torch.Tensor [H, W, C] (0.0 - 1.0) -> PIL.Image RGBA
            img_np = 255.0 * image[i].cpu().numpy()
            img_np = np.clip(img_np, 0, 255).astype(np.uint8)
            base_pil = Image.fromarray(img_np).convert("RGBA")
            img_w, img_h = base_pil.size

            # 吹き出しレイヤー生成
            bubble_layer = BubbleDrawer.render_bubble(
                image_size=(img_w, img_h),
                text=text,
                font=font,
                direction=direction,
                bubble_type=bubble_type,
                tail_direction=tail_direction,
                pos_ratio=(pos_x, pos_y),
                text_color=text_color,
                bubble_color=bubble_color,
                border_color=border_color,
                border_width=border_width,
                padding=padding,
                max_chars_per_line=max_chars_per_line,
                line_spacing=line_spacing,
                opacity=opacity,
            )

            # アルファ合成
            combined = Image.alpha_composite(base_pil, bubble_layer).convert("RGB")

            # PIL.Image -> torch.Tensor [H, W, C] (0.0 - 1.0)
            out_np = np.array(combined).astype(np.float32) / 255.0
            output_images.append(torch.from_numpy(out_np))

        result_tensor = torch.stack(output_images, dim=0)
        return (result_tensor,)
