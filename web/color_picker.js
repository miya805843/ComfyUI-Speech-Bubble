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

            // ウィジェットの完全描画（背景枠、項目名ラベル、HEX値、右端の色見本スウォッチ）
            w.draw = function(ctx, node, width, y, height) {
                const margin = 15;
                const widgetWidth = width - margin * 2;
                const widgetHeight = height;

                ctx.save();

                // 1. ウィジェット背景枠（LiteGraph標準スタイル）
                ctx.fillStyle = "#222222";
                ctx.beginPath();
                if (ctx.roundRect) {
                    ctx.roundRect(margin, y, widgetWidth, widgetHeight, 4);
                } else {
                    ctx.rect(margin, y, widgetWidth, widgetHeight);
                }
                ctx.fill();
                ctx.strokeStyle = "#383838";
                ctx.lineWidth = 1;
                ctx.stroke();

                // 2. 項目名（ラベル）
                ctx.fillStyle = "#aaaaaa";
                ctx.font = "12px sans-serif";
                ctx.textAlign = "left";
                ctx.textBaseline = "middle";
                const labelText = this.label || this.name;
                ctx.fillText(labelText, margin + 10, y + widgetHeight / 2);

                // 3. 値（HEXカラーコード）
                const valStr = String(this.value || "");
                ctx.fillStyle = "#ffffff";
                ctx.textAlign = "right";
                ctx.fillText(valStr, width - margin - 36, y + widgetHeight / 2);

                // 4. 右端のカラー見本スウォッチ（色付き四角形）
                const swatchSize = Math.max(14, widgetHeight - 8);
                const sx = width - margin - swatchSize - 4;
                const sy = y + (widgetHeight - swatchSize) / 2;

                let fillColor = valStr.trim();
                if (!fillColor.startsWith("#") && !/^[a-zA-Z]+$/.test(fillColor)) {
                    fillColor = "#000000";
                }

                ctx.fillStyle = fillColor;
                ctx.beginPath();
                if (ctx.roundRect) {
                    ctx.roundRect(sx, sy, swatchSize, swatchSize, 3);
                } else {
                    ctx.rect(sx, sy, swatchSize, swatchSize);
                }
                ctx.fill();

                // スウォッチの白い枠線（どんな色でも見やすく）
                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.restore();
            };

            // クリックイベントのハンドリング
            w.mouse = function(event, pos, node) {
                const margin = 15;
                const swatchAreaStart = node.size[0] - margin - 34;
                const isClickOnSwatch = pos[0] >= swatchAreaStart;

                if (isClickOnSwatch) {
                    // スウォッチをクリックした時: カラーピッカーダイアログを開く
                    if (event.type === "pointerdown" || event.type === "mousedown") {
                        openNativeColorPicker(event, w, node);
                    }
                    if (event.stopPropagation) event.stopPropagation();
                    if (event.preventDefault) event.preventDefault();
                    return true;
                }

                // スウォッチ以外（左側）をクリックした時: 通常のキーボード手入力プロンプトを開く
                if (event.type === "pointerdown" || event.type === "mousedown") {
                    const canvas = app.canvas;
                    if (canvas && canvas.prompt) {
                        canvas.prompt("Color (" + w.name + ")", w.value, (v) => {
                            if (v !== null && v !== undefined) {
                                w.value = v.toUpperCase();
                                if (w.callback) w.callback(w.value);
                                node.setDirtyCanvas(true, true);
                            }
                        }, event);
                        return true;
                    }
                }
                return true;
            };
        }
    }
});

/**
 * FirefoxおよびChrome/Edge両対応のネイティブカラーピッカー起動処理
 */
function openNativeColorPicker(event, widget, node) {
    let picker = document.getElementById("speech-bubble-color-picker");
    if (!picker) {
        picker = document.createElement("input");
        picker.type = "color";
        picker.id = "speech-bubble-color-picker";
        picker.style.position = "fixed";
        picker.style.opacity = "0.01";
        picker.style.width = "1px";
        picker.style.height = "1px";
        picker.style.pointerEvents = "none";
        picker.style.zIndex = "100000";
        document.body.appendChild(picker);
    }

    // Firefox対策: ユーザーのクリック座標直下に透明inputを移動
    if (event.clientX && event.clientY) {
        picker.style.left = event.clientX + "px";
        picker.style.top = event.clientY + "px";
    }

    // 現在の値を #RRGGBB 形式に正規化
    let currentVal = String(widget.value || "#FFFFFF").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(currentVal)) {
        picker.value = currentVal;
    } else if (/^#[0-9a-fA-F]{3}$/.test(currentVal)) {
        picker.value = `#${currentVal[1]}${currentVal[1]}${currentVal[2]}${currentVal[2]}${currentVal[3]}${currentVal[3]}`;
    } else {
        picker.value = "#000000";
    }

    // 色選択時の即時反映
    const onColorUpdate = (e) => {
        widget.value = e.target.value.toUpperCase();
        if (widget.callback) {
            widget.callback(widget.value);
        }
        node.setDirtyCanvas(true, true);
    };

    picker.oninput = onColorUpdate;
    picker.onchange = onColorUpdate;

    // Firefox (showPicker) および Chrome (showPicker / click) の両立
    try {
        if (typeof picker.showPicker === "function") {
            picker.showPicker();
        } else {
            picker.click();
        }
    } catch (err) {
        picker.click();
    }
}
