"""Build the 20-minute Traditional-Chinese Assignment 2 presentation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "presentation"
PPTX_PATH = OUT_DIR / "assignment2_20min_zh_tw.pptx"
NOTES_PATH = OUT_DIR / "assignment2_speaker_notes_zh_tw.md"

FONT = "Droid Sans Fallback"
FONT_LATIN = "Aptos"
NAVY = RGBColor(16, 32, 56)
BLUE = RGBColor(42, 117, 184)
CYAN = RGBColor(54, 190, 196)
ORANGE = RGBColor(238, 133, 68)
GREEN = RGBColor(77, 157, 104)
RED = RGBColor(207, 74, 69)
PURPLE = RGBColor(117, 93, 170)
INK = RGBColor(36, 44, 56)
MUTED = RGBColor(95, 108, 124)
LIGHT = RGBColor(243, 246, 250)
WHITE = RGBColor(255, 255, 255)
GRID = RGBColor(214, 222, 232)


SLIDES: list[dict[str, str]] = []


def add_notes(slide, title: str, timing: str, notes: str) -> None:
    slide.notes_slide.notes_text_frame.text = f"{timing}\n\n{notes}"
    SLIDES.append({"title": title, "timing": timing, "notes": notes})


def set_background(slide, color: RGBColor = WHITE) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    size: float = 22,
    color: RGBColor = INK,
    bold: bool = False,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
    font: str = FONT,
) -> object:
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.margin_left = frame.margin_right = Inches(0.05)
    frame.margin_top = frame.margin_bottom = Inches(0.03)
    frame.vertical_anchor = valign
    p = frame.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def add_bullets(
    slide,
    bullets: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    size: float = 20,
    color: RGBColor = INK,
    spacing: float = 8,
) -> object:
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.08)
    frame.margin_right = Inches(0.03)
    for index, bullet in enumerate(bullets):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = bullet
        p.level = 0
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(spacing)
        p.line_spacing = 1.08
    return shape


def add_rect(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: RGBColor = LIGHT,
    line: RGBColor | None = None,
    radius: bool = True,
) -> object:
    kind = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    return shape


def add_header(slide, title: str, section: str, number: int) -> None:
    add_text(slide, section.upper(), 0.55, 0.24, 3.7, 0.3, size=10, color=BLUE, bold=True)
    add_text(slide, title, 0.55, 0.58, 12.0, 0.52, size=26, color=NAVY, bold=True)
    add_rect(slide, 0.55, 1.16, 12.2, 0.03, fill=GRID, radius=False)
    add_text(slide, str(number), 12.35, 0.22, 0.4, 0.25, size=10, color=MUTED, align=PP_ALIGN.RIGHT)


def add_footer(slide, text: str = "ECE 258 · Assignment 2 · Twitch 新頻道推薦") -> None:
    add_text(slide, text, 0.55, 7.20, 12.2, 0.2, size=8.5, color=MUTED)


def add_card(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    *,
    accent: RGBColor = BLUE,
    title_size: float = 18,
    body_size: float = 13,
) -> None:
    add_rect(slide, x, y, w, h, fill=LIGHT, line=GRID)
    add_rect(slide, x, y, 0.08, h, fill=accent, radius=False)
    add_text(slide, title, x + 0.25, y + 0.16, w - 0.38, 0.4, size=title_size, color=NAVY, bold=True)
    add_text(slide, body, x + 0.25, y + 0.62, w - 0.4, h - 0.76, size=body_size, color=INK)


def add_metric(slide, x: float, y: float, w: float, value: str, label: str, color: RGBColor = BLUE) -> None:
    add_rect(slide, x, y, w, 1.05, fill=LIGHT, line=GRID)
    add_text(slide, value, x + 0.12, y + 0.12, w - 0.24, 0.46, size=25, color=color, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, label, x + 0.10, y + 0.64, w - 0.2, 0.25, size=10.5, color=MUTED, align=PP_ALIGN.CENTER)


def add_picture_fit(slide, path: Path, x: float, y: float, w: float, h: float) -> None:
    with Image.open(path) as image:
        iw, ih = image.size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    px, py = x + (w - pw) / 2, y + (h - ph) / 2
    slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))


def add_table(slide, rows: list[list[str]], x: float, y: float, w: float, h: float,
              widths: list[float] | None = None, font_size: float = 11.5) -> None:
    table = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(h)).table
    if widths:
        for i, width in enumerate(widths):
            table.columns[i].width = Inches(width)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = value
            cell.margin_left = cell.margin_right = Inches(0.07)
            cell.margin_top = cell.margin_bottom = Inches(0.04)
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if r == 0 else (WHITE if r % 2 else LIGHT)
            cell.border_left = None
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
                p.font.name = FONT
                p.font.size = Pt(font_size if r else font_size - 0.5)
                p.font.bold = r == 0
                p.font.color.rgb = WHITE if r == 0 else INK


def arrow(slide, x: float, y: float, w: float = 0.45) -> None:
    shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(0.42))
    shape.fill.solid(); shape.fill.fore_color.rgb = CYAN
    shape.line.color.rgb = CYAN


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # 1 — title
    slide = prs.slides.add_slide(blank); set_background(slide, NAVY)
    add_rect(slide, 0.0, 0.0, 0.18, 7.5, fill=CYAN, radius=False)
    add_text(slide, "TWITCH NEW-CHANNEL RECOMMENDATION", 0.75, 0.65, 8.4, 0.35, size=13, color=CYAN, bold=True, font=FONT_LATIN)
    add_text(slide, "Twitch 新頻道推薦系統", 0.75, 1.35, 11.8, 0.85, size=38, color=WHITE, bold=True)
    add_text(slide, "從高度稀疏的 implicit feedback，找出使用者下一個可能觀看的新頻道", 0.78, 2.35, 10.9, 0.8, size=22, color=RGBColor(218, 228, 240))
    add_rect(slide, 0.78, 3.48, 5.85, 1.28, fill=RGBColor(25, 50, 82), line=RGBColor(48, 78, 111))
    add_text(slide, "核心結果", 1.05, 3.68, 1.4, 0.3, size=13, color=CYAN, bold=True)
    add_text(slide, "Hybrid NDCG@10 = 0.1315", 1.05, 4.08, 5.2, 0.38, size=23, color=WHITE, bold=True, font=FONT_LATIN)
    add_text(slide, "ECE 258 · Assignment 2 · 20-minute presentation", 0.78, 6.65, 8.2, 0.3, size=12, color=RGBColor(176, 193, 214), font=FONT_LATIN)
    add_notes(slide, "Twitch 新頻道推薦系統", "0:00–0:35（35 秒）",
              "大家好，這個專案研究的是 Twitch 新頻道推薦。我們不是要預測使用者會不會回去看熟悉的實況主，而是根據過去觀看紀錄，推薦十個他從未看過、但未來可能會第一次觀看的頻道。接下來我會依 Assignment 2 的五個部分，說明任務、EDA、模型、評估與相關研究。")

    # 2 — rubric roadmap
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "20 分鐘簡報路線圖", "Rubric mapping", 2)
    cards = [
        ("1", "預測任務", "Top-10 新頻道排序\n基準與有效性", BLUE),
        ("2", "資料與 EDA", "規模、長尾、重複觀看\n前處理與資料品質", CYAN),
        ("3", "模型設計", "Popularity、ItemKNN\nBPR、Hybrid", ORANGE),
        ("4", "評估與結果", "NDCG／Recall／Coverage\n顯著性與 robustness", GREEN),
        ("5", "相關文獻", "LiveRec 與 BPR\n差異、限制、下一步", PURPLE),
    ]
    for i, (num, title, body, color) in enumerate(cards):
        x = 0.6 + i * 2.52
        add_rect(slide, x, 1.65, 2.24, 3.55, fill=LIGHT, line=GRID)
        add_rect(slide, x + 0.72, 1.92, 0.8, 0.8, fill=color)
        add_text(slide, num, x + 0.72, 2.02, 0.8, 0.5, size=24, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, title, x + 0.15, 2.95, 1.94, 0.45, size=18, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, body, x + 0.16, 3.65, 1.92, 1.1, size=13, color=MUTED, align=PP_ALIGN.CENTER)
    add_text(slide, "主線：EDA 發現 → 模型選擇 → 時間切分 → 結果與失敗原因", 1.35, 5.75, 10.6, 0.55, size=21, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "20 分鐘簡報路線圖", "0:35–1:15（40 秒）",
              "這份簡報直接對應五個各五分的評分部分。我會特別把 EDA 和模型選擇連起來，也會討論負面結果，因為 rubric 明確要求結果要合理、失敗也要被解釋。最後的相關工作會說明我們和原始 LiveRec 任務為何不同，因此不能直接比較數字。")

    # 3 — predictive task
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "預測任務：推薦下一個『從未看過』的頻道", "1 · Predictive task", 3)
    add_card(slide, 0.6, 1.55, 2.65, 2.05, "輸入", "使用者在 fit period 的\nbinary 觀看歷史", accent=BLUE, body_size=17)
    arrow(slide, 3.38, 2.33)
    add_card(slide, 3.95, 1.55, 2.65, 2.05, "排序", "對完整 fit catalog 評分\n排除已看過頻道", accent=ORANGE, body_size=17)
    arrow(slide, 6.72, 2.33)
    add_card(slide, 7.29, 1.55, 2.35, 2.05, "輸出", "每位使用者\nTop-10 清單", accent=GREEN, body_size=17)
    arrow(slide, 9.78, 2.33)
    add_card(slide, 10.35, 1.55, 2.35, 2.05, "答案", "未來第一次觀看的\n新 user-channel pair", accent=PURPLE, body_size=15)
    add_rect(slide, 0.6, 4.15, 12.1, 1.75, fill=RGBColor(235, 244, 252), line=RGBColor(188, 215, 238))
    add_text(slide, "這是 ranking，不是 rating prediction", 0.9, 4.4, 4.8, 0.4, size=21, color=BLUE, bold=True)
    add_bullets(slide, [
        "未觀看 ≠ 負評：可能是不知道，或當時沒有開播",
        "必要 baselines：整體熱門度與最近 7 天熱門度",
        "離線有效性：chronological holdout、完整候選排序、paired bootstrap",
    ], 5.45, 4.3, 6.9, 1.25, size=15, spacing=4)
    add_footer(slide)
    add_notes(slide, "預測任務", "1:15–2:25（70 秒）",
              "輸入是使用者過去看過哪些頻道。模型對訓練期已知的完整頻道庫排序，先排除使用者已看過的項目，再輸出十個頻道。未來第一次觀看的 user-channel pair 才是 positive。這是一個 ranking task，不是星等預測，也不是把所有沒看過的頻道當成真正負評。為了確認個人化是否有價值，我們一定要和全域及近期熱門度比較。")

    # 4 — dataset
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "資料：100K 使用者、3.05M 觀看互動、43 天", "2 · Dataset & EDA", 4)
    add_metric(slide, 0.65, 1.45, 2.3, "100,000", "使用者", BLUE)
    add_metric(slide, 3.12, 1.45, 2.3, "162,625", "頻道（items）", ORANGE)
    add_metric(slide, 5.59, 1.45, 2.3, "3,051,733", "觀看互動", GREEN)
    add_metric(slide, 8.06, 1.45, 2.3, "739,991", "直播 sessions", PURPLE)
    add_metric(slide, 10.53, 1.45, 2.15, "43", "相對日數", CYAN)
    add_card(slide, 0.65, 2.95, 5.7, 2.75, "資料來源與欄位", "UCSD McAuley Lab Twitch dataset\n匿名 user ID、stream ID、streamer 名稱、開始／停止 time slot\n每個 time slot = 10 分鐘；沒有 rating 或內容 metadata", accent=BLUE, body_size=15)
    add_card(slide, 6.6, 2.95, 6.08, 2.75, "資料品質與核心困難", "缺失值、完全重複、負時長、零時長：全部為 0\n平均每人約 30.5 筆互動，但理論矩陣超過 162 億格\n真正問題是高度稀疏、長尾與 catalog cold-start", accent=RED, body_size=15)
    add_text(slide, "implicit feedback：看過是正訊號；沒看過的原因未知", 1.6, 6.1, 10.1, 0.45, size=21, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide, "Source: UCSD Twitch dataset; Rappaz, McAuley & Aberer (RecSys 2021)")
    add_notes(slide, "資料集", "2:25–3:30（65 秒）",
              "資料來自 UCSD 公開的 Twitch dataset，記錄聊天室連線，每十分鐘是一個 time slot。官方 subset 有十萬使用者、十六萬多個頻道與三百零五萬筆互動。品質檢查沒有發現缺失或明顯壞資料；困難不是 cleaning，而是十萬乘十六萬的矩陣幾乎都是空的，而且沒有遊戲類別、語言或文字內容可用。")

    # 5 — long tail
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "EDA 發現一：頻道熱門度極度長尾", "2 · Dataset & EDA", 5)
    add_picture_fit(slide, ROOT / "outputs/figures/channel_long_tail.png", 0.55, 1.35, 7.45, 5.35)
    add_card(slide, 8.25, 1.55, 4.35, 1.32, "現象", "少數頭部頻道累積大量互動；多數頻道只有少量觀眾。", accent=ORANGE, body_size=14)
    add_card(slide, 8.25, 3.05, 4.35, 1.32, "對模型的影響", "Popularity 是合理 baseline；BPR 的長尾 item embeddings 容易資料不足。", accent=RED, body_size=14)
    add_card(slide, 8.25, 4.55, 4.35, 1.62, "對評估的影響", "只看 NDCG 會忽略集中化，因此同時回報 catalog coverage、novelty 與 long-tail exposure。", accent=GREEN, body_size=14)
    add_footer(slide)
    add_notes(slide, "EDA：長尾", "3:30–4:40（70 秒）",
              "橫軸是頻道熱門度排名，縱軸是互動數，兩邊都是對數尺度。曲線仍下降很多個數量級，說明資料非常長尾。這個觀察直接導出三件事：熱門度是不能省略的 baseline；BPR 必須為大量低資料頻道學 embedding，可能不穩；評估不能只看準確度，還要檢查推薦是否只集中在少數頭部頻道。")

    # 6 — repeats
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "EDA 發現二：回訪增加，但我們研究的是 discovery", "2 · Dataset & EDA", 6)
    add_picture_fit(slide, ROOT / "outputs/figures/new_vs_return.png", 0.55, 1.38, 7.6, 5.3)
    add_card(slide, 8.35, 1.55, 4.25, 1.45, "重複觀看是強訊號", "隨時間累積，return interactions 上升；這是直播平台的重要行為。", accent=BLUE, body_size=14)
    add_card(slide, 8.35, 3.25, 4.25, 1.45, "但 target 排除 repeats", "主要表示採 binary feedback，避免重度回訪完全主導新頻道推薦。", accent=ORANGE, body_size=14)
    add_card(slide, 8.35, 4.95, 4.25, 1.35, "冷啟動上限", "約 12% 測試期新頻道 positives 不在 fit catalog，協同過濾無法命中。", accent=RED, body_size=14)
    add_footer(slide)
    add_notes(slide, "EDA：重複觀看與冷啟動", "4:40–5:40（60 秒）",
              "第二個現象是回訪互動逐漸增加。這和原始 LiveRec 的動機一致，但我們刻意研究 discovery，所以重複觀看不算測試 positive。主要 user-item matrix 用 binary，而 count-weighted 只是 ablation。另外約百分之十二的新頻道答案在訓練期完全沒出現，這形成協同過濾無法跨越的候選覆蓋上限。")

    # 7 — split and validity
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "Chronological split：模型不能偷看未來", "1 & 4 · Validity", 7)
    add_rect(slide, 0.75, 1.55, 7.9, 0.86, fill=BLUE); add_text(slide, "TRAIN · Day 0–29 · 建模與候選模型", 0.95, 1.76, 7.45, 0.32, size=18, color=WHITE, bold=True)
    add_rect(slide, 8.65, 1.55, 1.65, 0.86, fill=ORANGE); add_text(slide, "VAL\n30–35", 8.65, 1.65, 1.65, 0.55, size=15, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_rect(slide, 10.30, 1.55, 2.25, 0.86, fill=GREEN); add_text(slide, "TEST · 36–42", 10.30, 1.76, 2.25, 0.32, size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_card(slide, 0.75, 2.92, 3.75, 2.75, "防止 leakage", "mapping、熱門度、相似度與 embeddings 都只用 fit period\n\nValidation 選參數；Test 只做一次最終評估", accent=BLUE, body_size=15)
    add_card(slide, 4.78, 2.92, 3.75, 2.75, "完整 ranking", "不是只和少量 sampled negatives 比\n\n每位使用者對完整 fit catalog 排序並排除 seen items", accent=ORANGE, body_size=15)
    add_card(slide, 8.81, 2.92, 3.75, 2.75, "統計有效性", "53,212 users／104,818 user-day cases\n\n10,000 次 user-clustered paired bootstrap + Holm correction", accent=GREEN, body_size=15)
    add_footer(slide)
    add_notes(slide, "時間切分與有效性", "5:40–6:55（75 秒）",
              "資料依時間切成前百分之七十訓練、接著驗證、最後測試。所有 mapping、熱門度、ItemKNN 相似度和 BPR 參數都只從 fit period 建立。驗證集選參數後，用 train 加 validation 重訓，測試只看一次。評估時對完整 catalog 排序，而不是用少量容易的 sampled negatives。因為同一使用者有多個 day cases，信賴區間以 user 為 cluster 做一萬次 paired bootstrap。")

    # 8 — models
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "四種方法：由共同觀看到 latent factors", "3 · Modeling", 8)
    add_card(slide, 0.65, 1.42, 2.88, 2.25, "Popularity", "所有人收到相近清單\n✓ 快速、可解釋\n✕ 幾乎無個人化", accent=MUTED, body_size=14)
    add_card(slide, 3.70, 1.42, 2.88, 2.25, "ItemKNN", "以共同觀眾計算 item cosine\n✓ 保留局部 co-view 訊號\n✕ 記憶體與近鄰計算", accent=BLUE, body_size=14)
    add_card(slide, 6.75, 1.42, 2.88, 2.25, "BPR", "學 user/item embeddings\nscore(u,i) > score(u,j)\n✕ 依賴 negative sampling", accent=ORANGE, body_size=14)
    add_card(slide, 9.80, 1.42, 2.88, 2.25, "Hybrid", "標準化後融合兩種分數\n✓ 利用互補命中\n✕ coverage 低於 ItemKNN", accent=GREEN, body_size=14)
    add_rect(slide, 1.05, 4.25, 11.2, 1.3, fill=RGBColor(235, 244, 252), line=RGBColor(188, 215, 238))
    add_text(slide, "Hybrid score = α · z(BPR) + (1 − α) · z(ItemKNN) − λ · log(1 + popularity)", 1.25, 4.56, 10.8, 0.48, size=21, color=NAVY, bold=True, align=PP_ALIGN.CENTER, font=FONT_LATIN)
    add_text(slide, "為何不是一般分類器？候選組合極多，未觀察組合不是真正負例；我們需要 Top-K ranking。", 1.1, 5.95, 11.1, 0.48, size=18, color=MUTED, align=PP_ALIGN.CENTER)
    add_footer(slide, "BPR: Rendle et al. (UAI 2009)")
    add_notes(slide, "模型", "6:55–8:25（90 秒）",
              "我們比較由簡到繁的四類方法。Popularity 是必要的非個人化基準。ItemKNN 用共同觀眾計算頻道相似度，直接保留局部 co-view 關係。BPR 使用 pairwise objective，讓看過的頻道分數高於抽到的未觀看頻道。Hybrid 先對每位使用者的 eligible candidates 標準化兩種分數再混合。這裡不直接用一般分類器，是因為負例數量巨大，而且未互動不是可靠的負標籤；我們真正要最佳化的是前十名排序。")

    # 9 — code implementation
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "實作架構：稀疏計算、disk-backed pipeline、可重現設定", "3 · Code walkthrough", 9)
    stages = [
        ("config", "YAML\nseed 258", BLUE), ("prepare", "DuckDB\n時間切分", CYAN),
        ("fit", "Sparse ItemKNN\nBPR SGD", ORANGE), ("select", "Validation\n33 configs", PURPLE),
        ("evaluate", "Full catalog\nTop-10", GREEN),
    ]
    for i, (_, body, color) in enumerate(stages):
        x = 0.72 + i * 2.48
        add_rect(slide, x, 1.6, 1.95, 1.25, fill=color)
        add_text(slide, body, x + 0.08, 1.83, 1.79, 0.75, size=16, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        if i < len(stages) - 1: arrow(slide, x + 2.02, 2.03, 0.35)
    add_card(slide, 0.72, 3.38, 3.78, 2.2, "ItemKNN scaling", "Sparse block multiplication\n不建立 162k × 162k dense matrix\n每個 item 只留 top-200 neighbors", accent=BLUE, body_size=14)
    add_card(slide, 4.77, 3.38, 3.78, 2.2, "Model selection", "Validation 比較 3 個 k、8 組 BPR、20 組 Hybrid\nTest 不參與調參", accent=ORANGE, body_size=14)
    add_card(slide, 8.82, 3.38, 3.78, 2.2, "Repo 對照", "models/item_knn.py · models/bpr.py\npipeline.py · evaluation.py\nassignment_analysis.py", accent=GREEN, body_size=14)
    add_text(slide, "同一流程已完成 100K → 200K → 500K → 1M matched-protocol runs", 1.25, 6.05, 10.8, 0.4, size=19, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "程式與架構", "8:25–9:20（55 秒）",
              "程式由 YAML 固定 seed 和搜尋空間，DuckDB 負責大型資料處理，再訓練稀疏 ItemKNN 與 BPR。ItemKNN 用 block multiplication，避免建立十六萬乘十六萬的 dense matrix，只保存每個 item 最相似的兩百個鄰居。模型選擇和測試完全分開。相同 pipeline 也已經在十萬到一百萬使用者的四個規模跑完。錄影時可在 workbook 或 repository 快速指出這幾個檔案。")

    # 10 — tuning
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "超參數只在 Validation 選：α = 0.75、λ = 0", "3 · Hyperparameter selection", 10)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/hybrid_ablation.png", 0.55, 1.38, 7.65, 5.25)
    add_card(slide, 8.40, 1.55, 4.15, 1.28, "ItemKNN", "k ∈ {50, 100, 200}\n選 k = 200", accent=BLUE, body_size=14)
    add_card(slide, 8.40, 3.03, 4.15, 1.45, "BPR", "64 factors · lr 0.03\nreg 0.0025 · 20 epochs\n1 negative／positive", accent=ORANGE, body_size=14)
    add_card(slide, 8.40, 4.70, 4.15, 1.52, "Hybrid", "α ∈ {0, .25, .5, .75, 1}\nλ ∈ {0, .05, .1, .2}\n最佳：α=.75、λ=0", accent=GREEN, body_size=14)
    add_footer(slide)
    add_notes(slide, "超參數", "9:20–10:25（65 秒）",
              "這張圖是 validation ablation。橫軸 alpha 是 BPR 權重；alpha 等於一就是只有 BPR，所以右端分數大幅下降。混合在 0.75 最高，而 popularity penalty lambda 沒有改善 NDCG，因此最後選零。ItemKNN 選兩百個鄰居；BPR 在 32/64 factors、兩種 regularization、10/20 epochs 中選出 64 factors、20 epochs。所有決定都沒有使用 test。")

    # 11 — metrics
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "主要指標回答不同問題：準確，不等於多樣", "4 · Evaluation", 11)
    add_card(slide, 0.65, 1.45, 3.7, 2.15, "Recall@10", "真正會看的新頻道中，前 10 名找回多少？\n\n重視找回率，不在意命中排第 1 或第 10。", accent=BLUE, body_size=15)
    add_card(slide, 4.56, 1.45, 3.7, 2.15, "NDCG@10 · 主指標", "命中之外，也獎勵把正確答案排得更前面。\n\n用它選 validation hyperparameters。", accent=ORANGE, body_size=15)
    add_card(slide, 8.47, 1.45, 3.86, 2.15, "Catalog Coverage", "多少不同頻道至少被推薦一次？\n\n衡量廣度，不保證推薦正確。", accent=GREEN, body_size=15)
    add_table(slide, [
        ["補充指標", "回答的問題"],
        ["Hit Rate@10", "至少命中一個嗎？"],
        ["Novelty", "推薦是否避開最熱門項目？"],
        ["Long-tail exposure", "小型頻道獲得多少曝光？"],
        ["Candidate coverage", "正確答案是否存在於 fit catalog？"],
    ], 1.15, 4.12, 11.0, 1.82, widths=[3.0, 8.0], font_size=13)
    add_text(slide, "產品判斷必須同時看 accuracy × diversity × cold-start feasibility", 1.25, 6.25, 10.8, 0.4, size=19, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "評估指標", "10:25–11:35（70 秒）",
              "Recall 看十個位置找回多少答案；NDCG 還會讓排得前面的命中得到更高權重，因此是主要選參數指標。Coverage 則完全不同，它問模型推薦過多少不同頻道，所以高 coverage 不代表高 accuracy。Hit rate、novelty、long-tail exposure 和 candidate coverage 用來補足產品觀點。這裡的核心是，不能只用一個分數宣稱模型全面最好。")

    # 12 — main results
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "主要結果：Hybrid 最準；ItemKNN 是最強單一模型", "4 · Main results", 12)
    add_picture_fit(slide, ROOT / "outputs/figures/test_accuracy.png", 0.45, 1.30, 7.85, 5.25)
    add_metric(slide, 8.55, 1.48, 3.75, "0.13148", "Hybrid NDCG@10", GREEN)
    add_metric(slide, 8.55, 2.75, 3.75, "+247.9%", "vs. Recent Popularity NDCG", BLUE)
    add_card(slide, 8.55, 4.05, 3.75, 1.82, "準確度／多樣性取捨", "Hybrid 比 ItemKNN NDCG 高 4.48%\n但 catalog coverage：26.36% vs. 36.71%", accent=ORANGE, body_size=14)
    add_text(slide, "個人化模型全部超越 popularity baselines", 8.50, 6.10, 3.85, 0.45, size=17, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "主要結果", "11:35–13:10（95 秒）",
              "Hybrid 的 Recall 是 0.2234，NDCG 是 0.1315，兩者都是最高。ItemKNN NDCG 0.1258，是最強單一模型。BPR 只有 0.0542，但仍比 popularity 高。Hybrid 相對近期熱門度提升約百分之二百四十八，證明個人化歷史有預測力。不過 Hybrid 的 catalog coverage 只有百分之二十六，ItemKNN 是百分之三十七，所以 Hybrid 是準確度最佳，不是所有產品目標都最佳。Count-weighted ItemKNN 的準確度更低，但多樣性最高，也說明不同目標會選不同模型。")

    # 13 — explain models
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "為什麼 BPR 弱？Hybrid 又為什麼仍然有幫助？", "4 · Interpretation", 13)
    add_card(slide, 0.65, 1.42, 5.85, 3.65, "BPR 的 mismatch", "1. 長尾頻道缺乏足夠資料學穩定 embeddings\n2. 未觀看可能是『沒開播』，不是 dislike\n3. 每個 positive 只抽 1 個 uniform negative，通常太容易\n4. 64 維空間壓縮大量局部關係\n5. 目標是新頻道 Top-10，和隨機 pairwise loss 不完全一致", accent=RED, body_size=15)
    add_card(slide, 6.80, 1.42, 5.85, 2.08, "互補命中", "ItemKNN only：22,559\nBPR only：5,540\nBoth：7,648", accent=GREEN, body_size=18)
    add_card(slide, 6.80, 3.75, 5.85, 1.83, "小幅提升，但具有統計證據", "Hybrid − ItemKNN NDCG = +0.005638\n95% user-clustered CI [0.005201, 0.006088]\nHolm-adjusted p = 0.0024", accent=BLUE, body_size=14)
    add_rect(slide, 0.95, 5.78, 11.45, 0.68, fill=RGBColor(235, 244, 252), line=RGBColor(188, 215, 238))
    add_text(slide, "結論：BPR 整體較弱，但提供少量 ItemKNN 看不到的排序訊號", 1.15, 5.95, 11.05, 0.3, size=19, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "BPR 與 Hybrid 解釋", "13:10–14:50（100 秒）",
              "BPR 較弱不是單一 bug。第一，長尾 item 的 embedding 資料不足。第二，直播未觀看可能只代表當時沒開播。第三，每個 positive 只抽一個 uniform negative，通常是非常容易的負例，無法教模型區分相似候選。第四，低維 latent space 不一定能保留 ItemKNN 的局部關係。五個不同 seeds 的 BPR 仍然遠低於 ItemKNN，所以不是 seed 258 特別倒楣。可是 BPR 單獨命中五千多個 ItemKNN 沒命中的 positive，因此融合後仍有小幅、但 bootstrap 顯著的提升。")

    # 14 — subgroup
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "誰最難推薦？長尾頻道與長歷史使用者", "4 · Subgroup analysis", 14)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/channel_popularity_subgroups.png", 0.45, 1.35, 6.25, 4.55)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/user_history_subgroups.png", 6.70, 1.35, 6.15, 4.55)
    add_rect(slide, 0.75, 5.98, 5.6, 0.64, fill=RGBColor(252, 239, 236), line=RGBColor(241, 196, 185))
    add_text(slide, "最冷門 quartile Recall@10 = 0.0328", 0.95, 6.14, 5.2, 0.3, size=17, color=RED, bold=True, align=PP_ALIGN.CENTER)
    add_rect(slide, 6.98, 5.98, 5.55, 0.64, fill=RGBColor(235, 244, 252), line=RGBColor(188, 215, 238))
    add_text(slide, "歷史 1–6 頻道：NDCG 0.1679；25+：0.0901", 7.12, 6.14, 5.27, 0.3, size=16, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "群體差異", "14:50–16:05（75 秒）",
              "模型對不同人和 item 的表現差很多。最冷門四分位的 target recall 只有 0.033，最熱門四分位超過 0.40，表示目前結果主要由較熱門的新頻道驅動。使用者歷史越長，NDCG 反而越低；可能是容易的相似頻道已經被看過，剩下的 unseen candidates 更難。真正零歷史使用者無法個人化，只能退回 popularity，NDCG 約 0.053。這些群體結果比單一平均數更能說明產品風險。")

    # 15 — robustness/scaling
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "Robustness：時間窗排序一致，規模擴大也不翻轉", "4 · Robustness & scalability", 15)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/rolling_backtest.png", 0.45, 1.30, 6.25, 4.65)
    add_picture_fit(slide, ROOT / "outputs/assignment2/figures/scalability_ndcg.png", 6.75, 1.30, 6.15, 4.65)
    add_text(slide, "Early → late 絕對準確度下降，模型順序不變", 0.65, 6.05, 5.9, 0.42, size=15.5, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "100K／200K／500K／1M：Hybrid > ItemKNN > BPR", 6.92, 6.05, 5.75, 0.42, size=15.5, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "穩健性與擴展", "16:05–17:20（75 秒）",
              "Rolling-origin 的 early、middle、late 三個時間窗都保持 Hybrid、ItemKNN、BPR、Popularity 的排序，雖然越晚的絕對準確度下降。Scaling 實驗也用同一 seed、相同 hyperparameter grid、validation 兩千與 test 五千上限，完成十萬、二十萬、五十萬與一百萬使用者。Hybrid 和 ItemKNN 大致穩定，BPR 在 item catalog 擴張後下降。但 cohorts 和 catalogs 不固定，因此這只能支持 scalability 和 robustness，不是純粹 training-size 的因果 learning curve。")

    # 16 — related work and limitations
    slide = prs.slides.add_slide(blank); set_background(slide); add_header(slide, "與 LiveRec 的差異：我們研究 discovery，不是即時回訪", "5 · Related work & limitations", 16)
    add_table(slide, [
        ["面向", "LiveRec（Rappaz et al., 2021）", "本專案"],
        ["目標", "排序當下可看的直播", "推薦從未看過的新頻道"],
        ["Repeat views", "核心訊號", "從主要 target 排除"],
        ["Availability", "明確建模 live status", "最近 7 天活躍 proxy"],
        ["模型", "self-attention + availability", "Popularity／ItemKNN／BPR／Hybrid"],
    ], 0.65, 1.45, 12.0, 2.55, widths=[2.0, 5.0, 5.0], font_size=12.5)
    add_card(slide, 0.65, 4.35, 3.78, 1.55, "限制 1 · 冷啟動", "約 12% novel positives 不在 fit catalog；純協同過濾無法推薦。", accent=RED, body_size=13)
    add_card(slide, 4.78, 4.35, 3.78, 1.55, "限制 2 · Availability", "沒有推薦時刻的真實 live status，未互動負例帶有噪音。", accent=ORANGE, body_size=13)
    add_card(slide, 8.91, 4.35, 3.78, 1.55, "下一步", "hard negatives、即時 availability、內容 metadata、兩階段 reranking、線上 A/B test。", accent=GREEN, body_size=13)
    add_text(slide, "相關方法：BPR（Rendle et al., 2009）；LightGCN（He et al., 2020）", 1.35, 6.30, 10.65, 0.3, size=13, color=MUTED, align=PP_ALIGN.CENTER)
    add_footer(slide)
    add_notes(slide, "相關文獻與限制", "17:20–18:45（85 秒）",
              "原始 LiveRec 使用同一資料來源，但目標不同。它強調當下可觀看的 live content 和 repeat behavior；我們研究新頻道 discovery，並沒有精確 live status。因此兩邊數值不能直接比較，但 LiveRec 指出 availability 是下一步最重要的特徵。BPR 提供 pairwise ranking 基礎，LightGCN 則是可嘗試的圖協同過濾。未來除了更強模型，更重要的是改善 negative sampling、加入即時可用性與內容 metadata，並用線上 A/B test 驗證觀看時間和創作者曝光。")

    # 17 — conclusion
    slide = prs.slides.add_slide(blank); set_background(slide, NAVY)
    add_text(slide, "結論", 0.75, 0.65, 3.0, 0.55, size=30, color=WHITE, bold=True)
    conclusions = [
        ("01", "個人化有效", "Hybrid NDCG@10 0.1315，遠高於 popularity 0.0370。", CYAN),
        ("02", "簡單模型符合資料結構", "ItemKNN 直接利用強 co-view 訊號；BPR 受稀疏、長尾與負樣本影響。", ORANGE),
        ("03", "『最佳』取決於產品目標", "Hybrid 最準；ItemKNN coverage 更高；冷啟動與 availability 仍未解決。", GREEN),
    ]
    for i, (num, title, body, color) in enumerate(conclusions):
        y = 1.55 + i * 1.48
        add_rect(slide, 0.78, y, 0.72, 0.72, fill=color)
        add_text(slide, num, 0.78, y + 0.14, 0.72, 0.35, size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, title, 1.78, y - 0.02, 3.25, 0.4, size=21, color=WHITE, bold=True)
        add_text(slide, body, 5.0, y - 0.01, 7.1, 0.75, size=16, color=RGBColor(214, 225, 238))
    add_rect(slide, 0.78, 6.28, 11.65, 0.04, fill=RGBColor(66, 89, 117), radius=False)
    add_text(slide, "Takeaway：更多資料或更複雜模型不會自動更好；inductive bias 必須符合任務。", 0.85, 6.55, 11.5, 0.45, size=20, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
    add_notes(slide, "結論", "18:45–20:00（75 秒）",
              "最後有三個結論。第一，個人化明顯有效，Hybrid 遠高於熱門度。第二，在這個高度稀疏、只有互動資料的新頻道任務中，ItemKNN 的局部 co-view inductive bias 比目前 BPR 更合適。第三，最佳模型取決於目標：Hybrid 最準，但 ItemKNN 推薦更廣，冷啟動和即時 availability 仍然是上限。最重要的 takeaway 是，更多資料或更複雜模型不會自動更好；模型假設必須和資料及 target definition 一致。謝謝。")

    prs.save(PPTX_PATH)
    notes_lines = [
        "# Assignment 2 20 分鐘投影片講稿（繁體中文）",
        "",
        "投影片檔：`assignment2_20min_zh_tw.pptx`",
        "",
        "建議錄影時同時開啟 `workbook.html`；第 9 頁可短暫切到 notebook／repository 做 code walkthrough。",
        "",
    ]
    for index, item in enumerate(SLIDES, 1):
        notes_lines.extend([
            f"## {index}. {item['title']}", "", f"時間：{item['timing']}", "", item["notes"], ""
        ])
    NOTES_PATH.write_text("\n".join(notes_lines), encoding="utf-8")
    print(f"Wrote {PPTX_PATH}")
    print(f"Wrote {NOTES_PATH}")


if __name__ == "__main__":
    build()
