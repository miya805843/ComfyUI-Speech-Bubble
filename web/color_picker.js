import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ComfyUI-Speech-Bubble.ColorPicker",
    async nodeCreated(node) {
        if (node.comfyClass !== "SpeechBubbleNode") return;

        const colorWidgetNames = [
            "text_color",
            "text_border_color",
            "bubble_color",
            "bubble_border_color"
        ];

        for (const name of colorWidgetNames) {
            const w = node.widgets?.find(widget => widget.name === name);
            if (!w) continue;

            const origDraw = w.draw;
            w.draw = function(ctx, node, width, y, height) {
                if (origDraw) {
                    origDraw.apply(this, arguments);
                }

                // 右端にカラー見本スウォッチ（プレビューボックス）を描画
                const boxW = 22;
                const boxH = Math.max(14, height - 8);
                const margin = 6;
                const bx = width - boxW - margin;
                const by = y + (height - boxH) / 2;

                let fillColor = String(this.value || "#000000").trim();
                if (!fillColor.startsWith("#") && !/^[a-zA-Z]+$/.test(fillColor)) {
                    fillColor = "#000000";
                }

                ctx.save();
                // スウォッチ背景
                ctx.fillStyle = fillColor;
                ctx.beginPath();
                if (ctx.roundRect) {
                    ctx.roundRect(bx, by, boxW, boxH, 4);
                } else {
                    ctx.rect(bx, by, boxW, boxH);
                }
                ctx.fill();

                // スウォッチ枠線
                ctx.strokeStyle = "#FFFFFF";
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.restore();
            };

            const origMouse = w.mouse;
            w.mouse = function(event, pos, node) {
                // 右端のカラーボックスエリア（width - 36px 以降）をクリックしたか判定
                const clickThreshold = node.size[0] - 36;
                const isClickOnSwatch = pos[0] >= clickThreshold;

                if (isClickOnSwatch && (event.type === "pointerdown" || event.type === "mousedown")) {
                    let picker = document.getElementById("speech-bubble-color-picker");
                    if (!picker) {
                        picker = document.createElement("input");
                        picker.type = "color";
                        picker.id = "speech-bubble-color-picker";
                        picker.style.position = "fixed";
                        picker.style.opacity = "0";
                        picker.style.pointerEvents = "none";
                        picker.style.left = "-9999px";
                        picker.style.top = "-9999px";
                        document.body.appendChild(picker);
                    }

                    // 現在の値を正規化（#RRGGBB形式）
                    let currentVal = String(w.value || "#FFFFFF").trim();
                    if (/^#[0-9a-fA-F]{6}$/.test(currentVal)) {
                        picker.value = currentVal;
                    } else if (/^#[0-9a-fA-F]{3}$/.test(currentVal)) {
                        picker.value = `#${currentVal[1]}${currentVal[1]}${currentVal[2]}${currentVal[2]}${currentVal[3]}${currentVal[3]}`;
                    } else {
                        picker.value = "#000000";
                    }

                    const updateColor = (e) => {
                        w.value = e.target.value.toUpperCase();
                        if (w.callback) {
                            w.callback(w.value);
                        }
                        node.setDirtyCanvas(true, true);
                    };

                    picker.oninput = updateColor;
                    picker.onchange = updateColor;

                    picker.click();
                    return true;
                }

                if (origMouse) {
                    return origMouse.apply(this, arguments);
                }
                return false;
            };
        }
    }
});
