import { app } from "../../scripts/app.js";

// シングルトンのカラーピッカー用透明オーバーレイ要素
let activeOverlay = null;

function getOrCreateOverlay() {
    if (activeOverlay) return activeOverlay;

    const input = document.createElement("input");
    input.type = "color";
    input.id = "speech-bubble-color-overlay";
    input.style.position = "fixed";
    input.style.opacity = "0.001";
    input.style.width = "26px";
    input.style.height = "24px";
    input.style.cursor = "pointer";
    input.style.zIndex = "999999";
    input.style.display = "none";
    input.style.border = "none";
    input.style.padding = "0";
    input.style.margin = "0";

    const updateColor = (e) => {
        if (input._targetWidget && input._targetNode) {
            input._targetWidget.value = e.target.value.toUpperCase();
            if (input._targetWidget.callback) {
                input._targetWidget.callback(input._targetWidget.value);
            }
            input._targetNode.setDirtyCanvas(true, true);
        }
    };

    input.addEventListener("input", updateColor);
    input.addEventListener("change", (e) => {
        updateColor(e);
        input.style.display = "none";
    });

    // マウスが外れたら非表示にして誤操作を防止
    input.addEventListener("mouseleave", () => {
        input.style.display = "none";
    });

    document.body.appendChild(input);
    activeOverlay = input;
    return input;
}

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

            // クリック＆ホバーイベントのハンドリング
            w.mouse = function(event, pos, node) {
                const margin = 15;
                const swatchAreaStart = node.size[0] - margin - 36;
                const isOverSwatch = pos[0] >= swatchAreaStart;

                if (isOverSwatch) {
                    const overlay = getOrCreateOverlay();
                    overlay._targetWidget = w;
                    overlay._targetNode = node;

                    // 現在のHEX値を正規化してセット
                    let currentVal = String(w.value || "#FFFFFF").trim();
                    if (/^#[0-9a-fA-F]{6}$/.test(currentVal)) {
                        overlay.value = currentVal;
                    } else if (/^#[0-9a-fA-F]{3}$/.test(currentVal)) {
                        overlay.value = `#${currentVal[1]}${currentVal[1]}${currentVal[2]}${currentVal[2]}${currentVal[3]}${currentVal[3]}`;
                    } else {
                        overlay.value = "#000000";
                    }

                    // Firefox対策: マウス直下に透明な本物のinput[type=color]を重ねてスタンバイ
                    if (event.clientX && event.clientY) {
                        overlay.style.left = (event.clientX - 13) + "px";
                        overlay.style.top = (event.clientY - 12) + "px";
                        overlay.style.display = "block";
                    }

                    // クリック時: showPickerを試行し、直下のinputへの本物クリックも連動
                    if (event.type === "pointerdown" || event.type === "mousedown") {
                        try {
                            if (typeof overlay.showPicker === "function") {
                                overlay.showPicker();
                            } else {
                                overlay.click();
                            }
                        } catch (err) {
                            // 万が一の例外時もoverlayがカーソル直下にあるため本物のクリックが通る
                        }
                    }

                    if (event.stopPropagation) event.stopPropagation();
                    return true;
                } else {
                    if (activeOverlay) {
                        activeOverlay.style.display = "none";
                    }
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
