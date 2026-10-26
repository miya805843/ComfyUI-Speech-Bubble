import { app } from "../../scripts/app.js";

// スタイルをヘッドに注入
function ensureStyles() {
    if (document.getElementById("speech-bubble-palette-styles")) return;
    const style = document.createElement("style");
    style.id = "speech-bubble-palette-styles";
    style.textContent = `
        .sb-palette-popup {
            position: fixed;
            z-index: 1000000;
            background: #202024;
            border: 1px solid #44444c;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.7);
            padding: 12px;
            color: #eee;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 12px;
            width: 250px;
            user-select: none;
        }
        .sb-palette-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-weight: 600;
            color: #aaa;
            border-bottom: 1px solid #333338;
            padding-bottom: 6px;
        }
        .sb-palette-title {
            font-size: 11px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .sb-palette-close {
            cursor: pointer;
            color: #888;
            font-size: 16px;
            line-height: 1;
            padding: 0 4px;
            border-radius: 3px;
        }
        .sb-palette-close:hover {
            color: #fff;
            background: #333;
        }
        .sb-palette-grid {
            display: grid;
            grid-template-columns: repeat(10, 1fr);
            gap: 4px;
            margin-bottom: 12px;
        }
        .sb-palette-cell {
            width: 19px;
            height: 19px;
            border-radius: 3px;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.2);
            box-sizing: border-box;
            transition: transform 0.1s, border-color 0.1s;
        }
        .sb-palette-cell:hover {
            transform: scale(1.25);
            border-color: #fff;
            box-shadow: 0 2px 6px rgba(0,0,0,0.5);
            z-index: 2;
        }
        .sb-palette-custom {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #18181c;
            padding: 6px;
            border-radius: 6px;
            border: 1px solid #303036;
        }
        .sb-palette-preview {
            width: 26px;
            height: 26px;
            border-radius: 4px;
            border: 1px solid #fff;
            flex-shrink: 0;
            box-sizing: border-box;
        }
        .sb-palette-input {
            background: #111;
            border: 1px solid #444;
            color: #fff;
            padding: 4px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 11px;
            width: 70px;
            text-align: center;
            text-transform: uppercase;
            box-sizing: border-box;
        }
        .sb-palette-btn {
            position: relative;
            overflow: hidden;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #2563eb;
            color: #fff;
            border: none;
            border-radius: 4px;
            padding: 5px 8px;
            font-size: 11px;
            cursor: pointer;
            flex-grow: 1;
            font-weight: 500;
        }
        .sb-palette-btn:hover {
            background: #1d4ed8;
        }
        .sb-palette-native-input {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
        }
    `;
    document.head.appendChild(style);
}

// マンガ・イラスト用基本20色パレット
const PRESET_COLORS = [
    // 1行目: モノトーン ＆ 暖色系
    "#000000", "#4B5563", "#9CA3AF", "#E5E7EB", "#FFFFFF",
    "#EF4444", "#B91C1C", "#F43F5E", "#FB7185", "#F97316",
    // 2行目: 明るい色 ＆ 寒色・中間色
    "#EAB308", "#FEF08A", "#84CC16", "#22C55E", "#065F46",
    "#06B6D4", "#38BDF8", "#3B82F6", "#1E3A8A", "#8B5CF6"
];

// シングルトンのパレットUI管理オブジェクト
let palettePopup = null;

function getOrCreatePopup() {
    if (palettePopup) return palettePopup;

    ensureStyles();

    const popup = document.createElement("div");
    popup.className = "sb-palette-popup";
    popup.style.display = "none";

    popup.innerHTML = `
        <div class="sb-palette-header">
            <span class="sb-palette-title" id="sb-title">COLOR PICKER</span>
            <span class="sb-palette-close" id="sb-close">&times;</span>
        </div>
        <div class="sb-palette-grid" id="sb-grid"></div>
        <div class="sb-palette-custom">
            <div class="sb-palette-preview" id="sb-prev"></div>
            <input type="text" class="sb-palette-input" id="sb-hex" maxlength="7" />
            <label class="sb-palette-btn">
                🎨 詳細色...
                <input type="color" class="sb-palette-native-input" id="sb-native" />
            </label>
        </div>
    `;

    document.body.appendChild(popup);

    const titleEl = popup.querySelector("#sb-title");
    const closeEl = popup.querySelector("#sb-close");
    const gridEl = popup.querySelector("#sb-grid");
    const prevEl = popup.querySelector("#sb-prev");
    const hexEl = popup.querySelector("#sb-hex");
    const nativeEl = popup.querySelector("#sb-native");

    // グリッドに20色を配置
    for (const col of PRESET_COLORS) {
        const cell = document.createElement("div");
        cell.className = "sb-palette-cell";
        cell.style.backgroundColor = col;
        cell.title = col;
        cell.addEventListener("click", () => {
            applyColor(col);
        });
        gridEl.appendChild(cell);
    }

    closeEl.addEventListener("click", () => {
        popup.style.display = "none";
    });

    // HEX手入力
    hexEl.addEventListener("change", (e) => {
        let val = e.target.value.trim();
        if (!val.startsWith("#")) val = "#" + val;
        if (/^#[0-9a-fA-F]{6}$/.test(val)) {
            applyColor(val);
        }
    });

    // ネイティブカラーピッカー（HTMLの<input type="color">直結）
    nativeEl.addEventListener("input", (e) => {
        applyColor(e.target.value.toUpperCase());
    });

    function applyColor(hex) {
        hex = hex.toUpperCase();
        prevEl.style.backgroundColor = hex;
        hexEl.value = hex;
        nativeEl.value = hex;

        if (popup._targetWidget && popup._targetNode) {
            popup._targetWidget.value = hex;
            if (popup._targetWidget.callback) {
                popup._targetWidget.callback(hex);
            }
            popup._targetNode.setDirtyCanvas(true, true);
        }
    }

    // 外側クリックで閉じる
    document.addEventListener("pointerdown", (e) => {
        if (popup.style.display !== "none" && !popup.contains(e.target)) {
            popup.style.display = "none";
        }
    });

    popup.openFor = function(widget, node, clientX, clientY) {
        popup._targetWidget = widget;
        popup._targetNode = node;

        titleEl.textContent = widget.name;
        let cur = String(widget.value || "#FFFFFF").trim().toUpperCase();
        if (!cur.startsWith("#") || cur.length !== 7) {
            cur = "#FFFFFF";
        }

        prevEl.style.backgroundColor = cur;
        hexEl.value = cur;
        nativeEl.value = cur;

        // 画面外にはみ出さないよう座標調整
        const popupW = 260;
        const popupH = 140;
        let left = clientX + 10;
        let top = clientY - 40;

        if (left + popupW > window.innerWidth) {
            left = clientX - popupW - 10;
        }
        if (top + popupH > window.innerHeight) {
            top = window.innerHeight - popupH - 10;
        }
        if (top < 10) top = 10;

        popup.style.left = left + "px";
        popup.style.top = top + "px";
        popup.style.display = "block";
    };

    palettePopup = popup;
    return popup;
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

                // スウォッチの白い枠線
                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 1;
                ctx.stroke();

                ctx.restore();
            };

            // クリックイベントのハンドリング
            w.mouse = function(event, pos, node) {
                const margin = 15;
                const swatchAreaStart = node.size[0] - margin - 36;
                const isClickOnSwatch = pos[0] >= swatchAreaStart;

                if (isClickOnSwatch) {
                    // スウォッチをクリックした時: ペイント風カラーパレットポップアップを開く！
                    if (event.type === "pointerdown" || event.type === "mousedown") {
                        const popup = getOrCreatePopup();
                        const clientX = event.clientX || (window.innerWidth / 2);
                        const clientY = event.clientY || (window.innerHeight / 2);
                        popup.openFor(w, node, clientX, clientY);
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
