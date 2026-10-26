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
                "tail_length": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 3.0,
                    "step": 0.05,
                    "display": "slider"
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
                "text_border_width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 30,
                    "step": 1
                }),
                "text_border_color": ("STRING", {
                    "default": "#FFFFFF"
                }),
                "bubble_color": ("STRING", {
                    "default": "#FFFFFF"
                }),
                "bubble_border_color": ("STRING", {
                    "default": "#000000"
                }),
                "bubble_border_width": ("INT", {
                    "default": 3,
                    "min": 0,
                    "max": 30,
                    "step": 1
                }),
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
                "thought_bump_size": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.2,
                    "max": 3.0,
                    "step": 0.05,
                    "display": "slider"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": "randomize"
                }),
            },
            "optional": {
                "bubble_opacity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider"
                }),
                "opacity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "display": "slider"
                }),
                # 旧パラメータ名との後方互換性用
                "border_color": ("STRING", {
                    "default": ""
                }),
                "border_width": ("INT", {
                    "default": -1
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
        tail_length: float,
        pos_x: float,
        pos_y: float,
        font_name: str,
        font_size: int,
        text_color: str,
        text_border_width: int,
        text_border_color: str,
        bubble_color: str,
        bubble_border_color: str,
        bubble_border_width: int,
        padding: int,
        max_chars_per_line: int,
        line_spacing: int,
        thought_bump_size: float,
        seed: int,
        bubble_opacity: float = 1.0,
        opacity: float = 1.0,
        border_color: str = "",
        border_width: int = -1,
        **kwargs
    ):
        if torch is None:
            raise RuntimeError("PyTorchがインストールされていません。")

        # 旧パラメータ名のフォールバック
        actual_border_color = border_color if border_color else bubble_border_color
        actual_border_width = border_width if border_width >= 0 else bubble_border_width

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

            # 吹き出しレイヤー生成（バッチごとにシードを少しずらす）
            current_seed = (seed + i) & 0xffffffffffffffff
            bubble_layer = BubbleDrawer.render_bubble(
                image_size=(img_w, img_h),
                text=text,
                font=font,
                direction=direction,
                bubble_type=bubble_type,
                tail_direction=tail_direction,
                tail_length=tail_length,
                pos_ratio=(pos_x, pos_y),
                text_color=text_color,
                text_border_color=text_border_color,
                text_border_width=text_border_width,
                bubble_color=bubble_color,
                bubble_border_color=actual_border_color,
                bubble_border_width=actual_border_width,
                padding=padding,
                max_chars_per_line=max_chars_per_line,
                line_spacing=line_spacing,
                thought_bump_size=thought_bump_size,
                bubble_opacity=bubble_opacity,
                opacity=opacity,
                seed=current_seed,
            )

            # アルファ合成
            combined = Image.alpha_composite(base_pil, bubble_layer).convert("RGB")

            # PIL.Image -> torch.Tensor [H, W, C] (0.0 - 1.0)
            out_np = np.array(combined).astype(np.float32) / 255.0
            output_images.append(torch.from_numpy(out_np))

        result_tensor = torch.stack(output_images, dim=0)
        return (result_tensor,)
