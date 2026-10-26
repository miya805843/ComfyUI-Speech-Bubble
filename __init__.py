from .nodes import SpeechBubbleNode

NODE_CLASS_MAPPINGS = {
    "SpeechBubbleNode": SpeechBubbleNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SpeechBubbleNode": "Speech Bubble Overlay (吹き出し合成)"
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
