import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ComfyUI-Speech-Bubble.ColorPreview",
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

            // ウィジェットの描画（背景枠、項目名ラベル、HEX値、右端のカラープレビュー見本）
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

                // 4. 右端のカラープレビュースウォッチ（色付き四角形）
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

            // クリック時はComfyUI標準のテキスト入力プロンプトを起動
            w.mouse = function(event, pos, node) {
                if (event.type === "pointerdown" || event.type === "mousedown") {
                    const canvas = app.canvas;
                    if (canvas && canvas.prompt) {
                        canvas.prompt("Color (" + w.name + ")", w.value, (v) => {
                            if (v !== null && v !== undefined) {
                                let newVal = v.trim();
                                if (!newVal.startsWith("#") && /^[0-9a-fA-F]{3,8}$/.test(newVal)) {
                                    newVal = "#" + newVal;
                                }
                                w.value = newVal.toUpperCase();
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
