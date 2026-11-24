"""Rebuild the Twitch research talk using Group_9_Presentation.pptx as its template."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "Group_9_Presentation.pptx"
OUT = ROOT / "presentation" / "Group_9_Presentation_Twitch.pptx"
NOTES_OUT = ROOT / "presentation" / "Group_9_Presentation_Twitch_notes.md"
MOTIVATION_FIGURE = ROOT / "outputs" / "figures" / "channel_ecdf_motivation.png"

FONT = "Calibri"
HEADER_FONT_SIZE = 24
NAVY = RGBColor(0x12, 0x30, 0x47)
TEAL = RGBColor(0x08, 0x7D, 0x8B)
BLUE = RGBColor(0x35, 0x5D, 0x9B)
RED = RGBColor(0xB3, 0x26, 0x1E)
GREEN = RGBColor(0x2E, 0x7D, 0x54)
ORANGE = RGBColor(0xD9, 0x72, 0x32)
GRAY = RGBColor(0x56, 0x65, 0x75)
MID = RGBColor(0x71, 0x82, 0x93)
LIGHT = RGBColor(0xEE, 0xF3, 0xF6)
GRID = RGBColor(0xD6, 0xE0, 0xE6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

SLIDE_NOTES: list[dict[str, str]] = []


def build_motivation_figure() -> None:
    """Render an interpretable ECDF line chart from the channel-count summary."""
    thresholds = [1, 2, 5, 10, 20, 50, 100]
    cumulative_share = [44.6, 60.1, 76.9, 86.1, 91.9, 96.0, 97.7]
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    figure.patch.set_facecolor("white")
    axis.set_facecolor("white")
    axis.plot(
        thresholds, cumulative_share, color="#355D9B", linewidth=3,
        marker="o", markersize=6, markerfacecolor="white", markeredgewidth=2,
    )
    axis.scatter([5], [76.9], s=95, color="#087D8B", zorder=4)
    axis.axvline(5, color="#087D8B", linewidth=1.2, alpha=0.35)
    for x, y, label in [(1, 44.6, "45%"), (2, 60.1, "60%"),
                        (5, 76.9, "77%"), (10, 86.1, "86%")]:
        axis.annotate(
            label, (x, y), xytext=(0, 11), textcoords="offset points",
            ha="center", color="#087D8B" if x == 5 else "#123047",
            fontsize=11, fontweight="bold",
        )
    axis.set_xscale("log")
    axis.set_xlim(0.85, 125)
    axis.set_ylim(0, 105)
    axis.set_xticks(thresholds, labels=[str(value) for value in thresholds])
    axis.set_yticks([0, 20, 40, 60, 80, 100],
                    labels=["0%", "20%", "40%", "60%", "80%", "100%"])
    axis.set_xlabel("Maximum interactions per channel (log scale)", fontsize=11)
    axis.set_ylabel("Share of channels", fontsize=11)
    axis.set_title("Empirical cumulative distribution", loc="left",
                   fontsize=13, fontweight="bold", color="#123047")
    axis.grid(axis="y", color="#D6E0E6", linewidth=0.8)
    axis.grid(axis="x", visible=False)
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_color("#718293")
    axis.tick_params(colors="#566575", labelsize=10)
    figure.tight_layout(pad=0.8)
    MOTIVATION_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(MOTIVATION_FIGURE, dpi=180, bbox_inches="tight")
    plt.close(figure)


def clear_template_slides(prs: Presentation) -> None:
    slide_ids = prs.slides._sldIdLst  # noqa: SLF001 - python-pptx has no public delete API
    for slide_id in list(slide_ids):
        prs.part.drop_rel(slide_id.rId)
        slide_ids.remove(slide_id)


def template_seal(prs: Presentation) -> bytes:
    for shape in prs.slide_layouts[1].shapes:
        if shape.shape_type == 13:
            return shape.image.blob
    raise RuntimeError("UCSD seal was not found in the template")


def no_line(shape) -> None:
    shape.line.fill.background()


def rect(slide, x: float, y: float, w: float, h: float, color: RGBColor,
         line: RGBColor | None = None) -> object:
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line is None:
        no_line(shape)
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(0.75)
    return shape


def text(slide, value: str, x: float, y: float, w: float, h: float, *,
         size: float = 16, color: RGBColor = NAVY, bold: bool = False,
         align: PP_ALIGN = PP_ALIGN.LEFT,
         valign: MSO_ANCHOR = MSO_ANCHOR.TOP) -> object:
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = Inches(0.02)
    frame.margin_top = frame.margin_bottom = Inches(0.01)
    frame.vertical_anchor = valign
    p = frame.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = value
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def bullets(slide, values: list[str], x: float, y: float, w: float, h: float, *,
            size: float = 14.5, color: RGBColor = NAVY,
            space_after: float = 5) -> object:
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.08)
    frame.margin_right = Inches(0.02)
    for index, item in enumerate(values):
        p = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        p.text = item
        p.font.name = FONT
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(space_after)
        p.line_spacing = 1.0
    return shape


def picture_fit(slide, path: Path, x: float, y: float, w: float, h: float) -> None:
    with Image.open(path) as image:
        iw, ih = image.size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    slide.shapes.add_picture(
        str(path), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2),
        Inches(pw), Inches(ph)
    )


def add_footer(slide, number: int) -> None:
    rect(slide, 0, 5.30, 10, 0.325, BLUE)
    text(slide, "CSE 258 · Fall 2026", 0.12, 5.365, 3.0, 0.18,
         size=9.5, color=WHITE)
    text(slide, "Twitch New-Channel Recommendation", 5.65, 5.365, 3.85, 0.18,
         size=9.5, color=WHITE, align=PP_ALIGN.RIGHT)
    text(slide, str(number), 9.60, 5.365, 0.23, 0.18,
         size=9.5, color=WHITE, align=PP_ALIGN.RIGHT)


def add_seal(slide, seal: bytes) -> None:
    slide.shapes.add_picture(BytesIO(seal), Inches(9.10), Inches(0.16),
                             Inches(0.58), Inches(0.58))


def add_header(slide, title_value: str, takeaway: str, number: int,
               seal: bytes) -> None:
    # Every content slide uses one consistent title size and baseline.
    text(slide, title_value, 0.68, 0.24, 8.16, 0.46,
         size=HEADER_FONT_SIZE, color=NAVY, bold=True,
         valign=MSO_ANCHOR.MIDDLE)
    rect(slide, 0.69, 0.88, 8.90, 0.045, TEAL)
    add_seal(slide, seal)
    add_footer(slide, number)


def add_notes(slide, title_value: str, timing: str, note: str) -> None:
    slide.notes_slide.notes_text_frame.text = f"{timing}\n\n{note}"
    SLIDE_NOTES.append({"title": title_value, "timing": timing, "note": note})


def add_flat_table(slide, rows: list[list[str]], x: float, y: float,
                   widths: list[float], row_h: float = 0.40,
                   font_size: float = 11.5) -> None:
    total_w = sum(widths)
    table = slide.shapes.add_table(
        len(rows), len(rows[0]), Inches(x), Inches(y), Inches(total_w),
        Inches(row_h * len(rows))
    ).table
    for c, width in enumerate(widths):
        table.columns[c].width = Inches(width)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = value
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if r == 0 else (WHITE if r % 2 else LIGHT)
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER
                p.font.name = FONT
                p.font.size = Pt(font_size if r else font_size - 0.5)
                p.font.bold = r == 0
                p.font.color.rgb = WHITE if r == 0 else NAVY
            # Explicitly disable any border/shadow-like decoration.
            cell._tc.get_or_add_tcPr()


def add_metric_line(slide, x: float, y: float, value: str, label: str,
                    color: RGBColor = TEAL) -> None:
    text(slide, value, x, y, 1.45, 0.40, size=24, color=color, bold=True,
         align=PP_ALIGN.CENTER)
    text(slide, label, x - 0.05, y + 0.42, 1.55, 0.34, size=10.5,
         color=GRAY, align=PP_ALIGN.CENTER)
    rect(slide, x + 0.14, y + 0.83, 1.17, 0.025, color)


def add_experiment_question(slide, question: str) -> None:
    rect(slide, 0.72, 1.06, 8.62, 0.38, LIGHT, line=GRID)
    text(slide, "QUESTION", 0.88, 1.17, 0.78, 0.16,
         size=9.5, color=TEAL, bold=True)
    text(slide, question, 1.70, 1.13, 7.42, 0.22,
         size=11.5, color=NAVY, bold=True)


def add_experiment_finding(slide, finding: str) -> None:
    rect(slide, 0.72, 4.72, 8.62, 0.40, LIGHT, line=GRID)
    text(slide, "FINDING", 0.88, 4.84, 0.72, 0.16,
         size=9.5, color=TEAL, bold=True)
    text(slide, finding, 1.66, 4.80, 7.45, 0.22,
         size=11, color=NAVY, bold=True)


def add_process_arrow(slide, x: float, y: float) -> None:
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(0.40), Inches(0.28)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = TEAL
    no_line(shape)


def oval(slide, x: float, y: float, w: float, h: float, color: RGBColor,
         line: RGBColor | None = None) -> object:
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.OVAL, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    if line is None:
        no_line(shape)
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    return shape


def flatten_shape_effects(shape) -> None:
    """Remove template theme effect references and explicitly apply an empty effect list."""
    element = shape._element
    style = element.find(qn("p:style"))
    if style is not None:
        element.remove(style)
    sp_pr = element.find(qn("p:spPr"))
    if sp_pr is None:
        return
    for tag in ("a:effectLst", "a:effectDag", "a:scene3d", "a:sp3d"):
        node = sp_pr.find(qn(tag))
        if node is not None:
            sp_pr.remove(node)
    sp_pr.append(OxmlElement("a:effectLst"))


def flatten_presentation_effects(prs: Presentation) -> None:
    for slide in prs.slides:
        for shape in slide.shapes:
            flatten_shape_effects(shape)


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    build_motivation_figure()
    prs = Presentation(TEMPLATE)
    seal = template_seal(prs)
    clear_template_slides(prs)
    blank = prs.slide_layouts[10]
    SLIDE_NOTES.clear()

    # 1 — Title
    slide = prs.slides.add_slide(blank)
    text(slide, "Twitch New-Channel Recommendation", 0.72, 1.28, 8.56, 0.58,
         size=28, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    rect(slide, 1.55, 2.08, 6.90, 0.055, TEAL)
    text(slide,
         "Personalized discovery from highly sparse implicit feedback",
         1.15, 2.36, 7.70, 0.36, size=17, color=GRAY,
         align=PP_ALIGN.CENTER)
    text(slide, "Wen-Chieh Lo · Bing-You Yu", 2.20, 3.32, 5.60, 0.30,
         size=15, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    text(slide, "CSE 258 · Fall 2026", 2.20, 3.72, 5.60, 0.26,
         size=12.5, color=MID, align=PP_ALIGN.CENTER)
    slide.shapes.add_picture(BytesIO(seal), Inches(8.72), Inches(0.25),
                             Inches(0.78), Inches(0.78))
    add_footer(slide, 1)
    add_notes(slide, "Twitch New-Channel Recommendation", "0:00–0:30 (30 sec)",
              "Let me start with what we mean by new-channel recommendation. We are not trying to bring a viewer back "
              "to a channel they already know; we are trying to predict the next channel they will discover. Here, new "
              "means absent from that viewer's history, not newly created, which makes this a natural recommendation "
              "problem in a catalog far too large to explore manually.")

    # 2 — Motivation
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Motivation", "", 2, seal)
    picture_fit(slide, MOTIVATION_FIGURE, 0.48, 1.18, 5.70, 3.78)

    conclusion_cards = [
        ("Extreme item sparsity", "77% of channels have five or fewer interactions", TEAL),
        ("Concentrated attention", "The top 1% receives 60% of all interactions", BLUE),
        ("Ambiguous negatives", "A missing view may mean offline—not disliked", ORANGE),
        ("Baseline design", "Use popularity as the baseline; can personalization beat it?", GREEN),
    ]
    for index, (heading, body, color) in enumerate(conclusion_cards):
        y = 1.22 + index * 0.92
        rect(slide, 6.42, y, 2.94, 0.76, WHITE, line=GRID)
        rect(slide, 6.42, y, 0.065, 0.76, color)
        text(slide, heading, 6.64, y + 0.10, 2.50, 0.22,
             size=11.5, color=NAVY, bold=True)
        text(slide, body, 6.64, y + 0.38, 2.50, 0.28,
             size=10.2, color=GRAY)
    text(slide, "Source: UCSD Twitch dataset; channel-level interaction counts.",
         0.72, 5.05, 5.40, 0.18, size=8.5, color=MID)
    add_notes(slide, "Motivation", "0:30–1:25 (55 sec)",
              "The challenge becomes clear when we look at the data. We have more than 162,000 channels, but an average "
              "viewer gives us only about thirty interactions. The curve shows how severe that imbalance is: 45 percent "
              "of channels appear once, and 77 percent appear no more than five times. At the same time, the top one "
              "percent receives 60 percent of all attention. That makes popularity a strong baseline, because a model "
              "should prove it can do more than recommend the obvious head channels. And on a live platform, no view does "
              "not necessarily mean dislike—the channel may simply have been offline.")

    # 3 — Objective
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Research Objective", "", 3, seal)
    rect(slide, 0.74, 1.18, 8.52, 0.72, LIGHT, line=GRID)
    text(slide, "CORE QUESTION", 0.98, 1.30, 1.22, 0.18,
         size=10, color=TEAL, bold=True)
    text(slide,
         "Can past viewing history predict which unseen Twitch channels a viewer will discover next?",
         2.12, 1.27, 6.82, 0.36, size=16.5, color=NAVY, bold=True,
         align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)

    objectives = [
        (0.70, "01", "Ranking quality",
         "Compare popularity, ItemKNN, BPR, and Hybrid on Top-10 unseen-channel recommendation."),
        (3.52, "02", "Explanation",
         "Identify why methods differ through BPR diagnostics, feature ablations, and subgroup analysis."),
        (6.34, "03", "Robustness",
         "Test whether conclusions persist across target windows and cohorts from 100K to 1M users."),
    ]
    for x, number, heading, body in objectives:
        rect(slide, x, 2.24, 2.64, 1.78, WHITE, line=GRID)
        rect(slide, x, 2.24, 2.64, 0.055, TEAL)
        text(slide, number, x + 0.18, 2.48, 0.38, 0.24,
             size=15, color=TEAL, bold=True)
        text(slide, heading, x + 0.62, 2.46, 1.76, 0.28,
             size=14, color=NAVY, bold=True)
        text(slide, body, x + 0.20, 2.94, 2.24, 0.78,
             size=11.5, color=GRAY, align=PP_ALIGN.CENTER)

    rect(slide, 1.16, 4.40, 7.68, 0.45, LIGHT, line=GRID)
    text(slide, "PREDICTION TARGET", 1.38, 4.54, 1.52, 0.18,
         size=9.5, color=TEAL, bold=True)
    text(slide, "Future first-time channel views in a chronological holdout",
         2.92, 4.50, 5.55, 0.22, size=12, color=NAVY, bold=True,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Research Objective", "1:25–2:10 (45 sec)",
              "So the research question is straightforward: can past viewing history tell us which unseen channel a "
              "viewer will discover next? We answer that in three layers. We compare the ranking quality of several "
              "models, we investigate why their performance differs instead of stopping at a leaderboard, and we test "
              "whether the same conclusions survive changes in time and dataset scale. Throughout the study, success "
              "means predicting a future first-time channel view in a chronological holdout.")

    # 4 — Dataset overview
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Dataset Overview", "", 4, seal)
    add_flat_table(slide, [
        ["Property", "Full Twitch source", "Primary 100K benchmark"],
        ["Users", "15,524,309", "100,000"],
        ["Interactions", "474,676,930", "3,051,733"],
        ["Channels", "790,100", "162,625"],
        ["Observation window", "43 relative days", "43 relative days"],
        ["Feedback", "Viewing sessions (implicit)", "Viewing sessions (implicit)"],
        ["Available fields", "User, stream, channel, start, stop", "Same five fields"],
        ["Channel metadata", "Identifier only; no class or category", "Same limitation"],
    ], 0.82, 1.28, [2.05, 3.15, 3.15], row_h=0.46, font_size=11.3)
    text(slide, "Source: UCSD Twitch dataset; Rappaz, McAuley, and Aberer, RecSys 2021.",
         0.86, 5.02, 5.80, 0.18, size=8.8, color=MID)
    add_notes(slide, "Dataset Overview", "2:10–3:25 (75 sec)",
              "The full Twitch source is very large—15.5 million users and almost 475 million viewing interactions over "
              "forty-three relative days. For the main experiment, we use the official 100,000-user benchmark, which still "
              "contains more than three million interactions and 162,625 channels. What matters here is not only the size, "
              "but also what the data does not contain. These are viewing sessions, not ratings, so an unrecorded view is "
              "not an explicit negative. We also have only identifiers and time fields, with no game, language, or channel "
              "category. That means we cannot group channels by class or build a content-based recommender; the models have "
              "to learn almost entirely from the interaction structure.")

    # 5 — Task and protocol
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Experimental Protocol",
               "Model selection is chronological; the test set is used exactly once.", 5, seal)
    text(slide, "Chronological split", 0.72, 1.08, 2.10, 0.24,
         size=13, color=NAVY, bold=True)
    text(slide, "Past data must remain earlier than the simulated future.",
         2.56, 1.10, 4.90, 0.20, size=10.5, color=GRAY)
    split_stages = [
        (0.72, "TRAIN", "Days 0–29", "Learn user–channel patterns", NAVY),
        (3.67, "VALIDATE", "Days 30–35", "Choose settings without test data", BLUE),
        (6.62, "TEST", "Days 36–42", "Evaluate future discoveries once", TEAL),
    ]
    for index, (x, heading, days, purpose, color) in enumerate(split_stages):
        rect(slide, x, 1.42, 2.64, 1.08, WHITE, line=GRID)
        rect(slide, x, 1.42, 2.64, 0.34, color)
        text(slide, heading, x, 1.50, 2.64, 0.18,
             size=11, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
        text(slide, days, x + 0.18, 1.89, 2.28, 0.24,
             size=15, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
        text(slide, purpose, x + 0.18, 2.19, 2.28, 0.22,
             size=10.2, color=GRAY, align=PP_ALIGN.CENTER)
        if index < len(split_stages) - 1:
            add_process_arrow(slide, x + 2.70, 1.80)

    rect(slide, 2.02, 2.66, 5.96, 0.43, LIGHT, line=GRID)
    text(slide, "AFTER TUNING", 2.20, 2.80, 1.10, 0.16,
         size=9, color=TEAL, bold=True)
    text(slide, "Refit the selected model on days 0–35, then test once.",
         3.30, 2.70, 4.42, 0.34, size=10.2, color=NAVY, bold=True,
         align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)

    text(slide, "How one test recommendation is scored", 0.72, 3.22, 5.10, 0.24,
         size=13, color=NAVY, bold=True)
    test_steps = [
        (0.72, "1  HISTORY", "Use views observed before the target day"),
        (2.91, "2  FILTER", "Remove channels the viewer already watched"),
        (5.10, "3  RANK", "Score the remaining fit-catalog channels"),
        (7.29, "4  CHECK", "Did a future first-time view enter Top-10?"),
    ]
    for x, heading, body in test_steps:
        rect(slide, x, 3.57, 1.90, 0.82, WHITE, line=GRID)
        text(slide, heading, x + 0.10, 3.69, 1.70, 0.18,
             size=10, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
        text(slide, body, x + 0.12, 3.96, 1.66, 0.32,
             size=9.5, color=GRAY, align=PP_ALIGN.CENTER)

    rect(slide, 0.72, 4.65, 8.62, 0.43, LIGHT, line=GRID)
    safeguards = [
        (0.86, "NO LEAKAGE", "past-only features"),
        (3.52, "TEST SET", "53,212 users · 104,818 cases"),
        (6.58, "BOOTSTRAP", "10,000 draws · resample users"),
    ]
    for x, heading, body in safeguards:
        text(slide, heading, x, 4.77, 1.02, 0.16,
             size=8.8, color=TEAL, bold=True)
        text(slide, body, x + 1.00, 4.74, 1.82, 0.20,
             size=8.7, color=NAVY, bold=True)
    add_notes(slide, "Experimental Protocol", "3:25–4:45 (80 sec)",
              "Here is how we make the evaluation behave like a real recommendation decision. We move strictly from past "
              "to future: days zero through twenty-nine train the models, and the next six days choose the settings without "
              "touching the test set. Once the settings are fixed, we refit on everything through day thirty-five and use "
              "days thirty-six through forty-two exactly once. For each user-day, we look only at earlier history, remove "
              "channels the viewer already knows, rank the remaining catalog, and ask whether a future first-time view "
              "appears in the Top-10. All statistics are built from past data, and because one viewer can contribute several "
              "days, the bootstrap resamples entire users rather than pretending those cases are independent.")

    # 6 — Models
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Compared Models",
               "The comparison isolates global popularity, local co-view structure, and latent preference.",
               6, seal)
    rows = [
        ["Model", "Scoring signal", "Strength", "Primary limitation"],
        ["Popularity", "Distinct viewers", "Fast, interpretable baseline", "No personalization"],
        ["Recent popularity", "Last seven fit days", "Tracks recency", "Still non-personalized"],
        ["ItemKNN", "Cosine similarity of co-viewers", "Preserves local structure", "Neighbor computation"],
        ["BPR", "Pairwise user/item factors", "Personalized ranking objective", "Negative sampling"],
        ["Hybrid", "Standardized BPR + ItemKNN", "Combines complementary hits", "Lower coverage"],
    ]
    add_flat_table(slide, rows, 0.60, 1.58, [1.55, 2.45, 2.55, 2.65],
                   row_h=0.48, font_size=11.4)
    rect(slide, 0.92, 4.60, 8.16, 0.035, TEAL)
    text(slide,
         "Hybrid score = α · z(BPR) + (1 − α) · z(ItemKNN) − λ · log(1 + popularity)",
         0.92, 4.75, 8.16, 0.34, size=14.5, color=NAVY, bold=True,
         align=PP_ALIGN.CENTER)
    text(slide, "BPR: Rendle et al., UAI 2009.", 0.92, 5.08, 2.60, 0.16,
         size=8.5, color=MID)
    add_notes(slide, "Compared Models", "4:45–6:15 (90 sec)",
              "The model comparison is designed to move from the simplest explanation to more personalized ones. "
              "Popularity and recent popularity tell us how far we can get by recommending what everyone already watches. "
              "ItemKNN then asks a local question: given the channels this viewer knows, which other channels share the "
              "same audience? BPR takes a more global approach by learning latent user and item factors from pairwise "
              "preferences. We also compare binary and count-weighted ItemKNN to see whether repeated viewing helps or just "
              "reinforces familiar channels. Finally, the hybrid combines standardized ItemKNN and BPR scores, with an "
              "optional popularity penalty, so validation can decide whether their different signals are genuinely "
              "complementary.")

    # 7 — Implementation and tuning
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Model Selection",
               "Sparse computation avoids materializing the 162K × 162K item-similarity matrix.",
               7, seal)
    picture_fit(slide, ROOT / "outputs/assignment2/figures/hybrid_ablation.png",
                0.50, 1.24, 5.55, 3.70)
    text(slide, "Selected configuration", 6.45, 1.35, 2.70, 0.30,
         size=15.5, color=NAVY, bold=True)
    add_flat_table(slide, [
        ["Component", "Selected setting"],
        ["ItemKNN", "200 neighbors"],
        ["BPR", "64 factors; lr 0.03"],
        ["BPR", "reg 0.0025; 20 epochs"],
        ["Hybrid", "α = 0.75; λ = 0"],
    ], 6.38, 1.82, [1.12, 2.12], row_h=0.46, font_size=10.8)
    rect(slide, 6.38, 4.35, 3.24, 0.58, LIGHT, line=GRID)
    text(slide, "ENGINEERING", 6.56, 4.52, 0.92, 0.18,
         size=9.5, color=TEAL, bold=True)
    text(slide, "Sparse blocks · top-200 neighbors · seed 258",
         7.47, 4.48, 1.96, 0.26, size=10.5, color=NAVY, bold=True)
    add_notes(slide, "Model Selection", "6:15–7:30 (75 sec)",
              "Before looking at the test results, we use validation data to make every modeling choice. ItemKNN performs "
              "best with 200 neighbors, which suggests that a fairly broad local co-view neighborhood is useful. For BPR, "
              "the selected configuration uses 64 factors, a learning rate of 0.03, and twenty epochs. The curve on the "
              "left shows that the hybrid is strongest when ItemKNN carries most of the weight: validation chooses alpha "
              "0.75 and no popularity penalty. There is also an engineering constraint behind this experiment. A dense "
              "162,000-by-162,000 similarity matrix is not practical, so we multiply sparse blocks and retain only the best "
              "neighbors for each channel.")

    # 8 — Metrics
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Evaluation and Inference",
               "Ranking accuracy and recommendation breadth answer different scientific questions.",
               8, seal)
    metric_cards = [
        (0.62, "Recall@10", "How many future discoveries are retrieved?", TEAL),
        (2.84, "NDCG@10", "Are correct channels ranked near the top?", BLUE),
        (5.06, "Hit Rate", "Does a case contain at least one hit?", GREEN),
        (7.28, "Coverage", "How much of the catalog is exposed?", ORANGE),
    ]
    for x, label, definition, color in metric_cards:
        rect(slide, x, 1.34, 2.05, 1.18, WHITE, line=GRID)
        rect(slide, x, 1.34, 2.05, 0.055, color)
        text(slide, label, x + 0.10, 1.58, 1.85, 0.28,
             size=16, color=color, bold=True, align=PP_ALIGN.CENTER)
        text(slide, definition, x + 0.14, 1.96, 1.77, 0.40,
             size=10.5, color=GRAY, align=PP_ALIGN.CENTER)
    rect(slide, 0.72, 2.82, 8.62, 0.035, GRID)
    add_flat_table(slide, [
        ["Metric", "Interpretation", "Why it matters"],
        ["Novelty", "Self-information of recommended channels", "Penalizes only-head recommendations"],
        ["Long-tail exposure", "Fraction of recommendations in the tail", "Measures creator-side breadth"],
        ["Candidate coverage", "Novel positives present in fit catalog", "Separates ranking from item cold-start"],
    ], 0.82, 3.18, [1.85, 3.15, 3.35], row_h=0.45, font_size=10.8)
    text(slide, "Model selection uses validation NDCG@10; all other metrics are diagnostic.",
         1.18, 4.90, 7.65, 0.26, size=12, color=TEAL, bold=True,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Evaluation and Inference", "7:30–8:45 (75 sec)",
              "Before reading the results, it helps to separate accuracy from breadth. Recall asks how many future "
              "discoveries appear anywhere in the Top-10, while NDCG gives more credit when the correct channel appears "
              "near the top, so NDCG is the metric we use to choose models. Hit rate answers a simpler question—did this "
              "user-day get at least one useful recommendation? Coverage, novelty, and long-tail exposure tell us whether "
              "the system keeps showing the same head channels or spreads attention more broadly. Candidate coverage is "
              "also important because some future channels never appeared during fitting and were impossible for any "
              "collaborative model to retrieve. For uncertainty, we compare models with user-level bootstrap samples and "
              "correct for multiple tests.")

    # 9 — Experiment 1: overall model comparison
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Experiment 1: Model Comparison", "", 9, seal)
    add_experiment_question(slide,
                            "Which model best ranks unseen channels, and what accuracy–coverage trade-off follows?")
    picture_fit(slide, ROOT / "outputs/figures/test_accuracy.png",
                0.45, 1.50, 5.55, 3.08)
    add_flat_table(slide, [
        ["Model", "NDCG@10", "Recall@10", "Coverage"],
        ["Hybrid", "0.13148", "0.22342", "26.36%"],
        ["ItemKNN", "0.12584", "0.21437", "36.71%"],
        ["Count ItemKNN", "0.11694", "0.19862", "40.50%"],
        ["BPR", "0.05420", "0.09328", "0.62%"],
        ["Recent popularity", "0.03779", "0.06195", "0.02%"],
    ], 6.18, 1.60, [1.32, 0.78, 0.78, 0.78], row_h=0.44, font_size=9.5)
    text(slide, "Primary metric: NDCG@10", 6.32, 4.40, 2.92, 0.22,
         size=10.5, color=MID, align=PP_ALIGN.CENTER)
    add_experiment_finding(slide,
                           "Hybrid gains 4.48% NDCG over ItemKNN, but exposes 10.35 pp less of the catalog.")
    add_notes(slide, "Experiment 1: Model Comparison", "8:45–10:30 (105 sec)",
              "This first experiment gives us the overall ranking. The hybrid is best, with NDCG 0.13148 and Recall "
              "0.22342, while ItemKNN is the strongest single model at 0.12584 NDCG. The larger message is that every "
              "personalized method beats popularity by a wide margin, so the viewer's own history contains real predictive "
              "signal. The hybrid improves NDCG by 4.48 percent over ItemKNN, which means BPR is contributing something "
              "useful even though it performs poorly alone. But that gain is not free: hybrid coverage falls to 26.36 "
              "percent, compared with 36.71 percent for ItemKNN, and count-weighted ItemKNN reaches 40.50 percent coverage "
              "despite lower accuracy. So if the objective is pure ranking quality, hybrid wins; if broader creator exposure "
              "matters, ItemKNN or a diversity-aware reranker may be the better operating choice.")

    # 10 — Experiment 2: BPR failure and complementarity
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Experiment 2: BPR Analysis", "", 10, seal)
    add_experiment_question(slide,
                            "Why does BPR lag ItemKNN, and can its unique hits still improve the hybrid?")
    text(slide, "Failure hypotheses", 0.72, 1.62, 2.45, 0.28,
         size=14.5, color=NAVY, bold=True)
    mismatch = [
        ("Sparse tail", "item factors receive little evidence"),
        ("Noisy negatives", "offline may be mistaken for dislike"),
        ("Easy sampling", "uniform negatives rarely challenge ranking"),
        ("Objective gap", "pairwise loss differs from full-catalog Top-10"),
    ]
    for index, (heading, explanation) in enumerate(mismatch):
        y = 2.00 + index * 0.62
        oval(slide, 0.76, y + 0.06, 0.13, 0.13, TEAL)
        text(slide, heading, 1.02, y, 1.38, 0.25,
             size=12, color=NAVY, bold=True)
        text(slide, explanation, 2.34, y, 2.37, 0.34,
             size=10.5, color=GRAY)
    rect(slide, 5.02, 1.55, 0.035, 3.02, GRID)
    text(slide, "Hit overlap analysis", 5.42, 1.62, 2.05, 0.28,
         size=14.5, color=NAVY, bold=True)
    add_metric_line(slide, 5.30, 1.98, "22,559", "ItemKNN only", BLUE)
    add_metric_line(slide, 7.42, 1.98, "5,540", "BPR only", ORANGE)
    add_metric_line(slide, 5.30, 3.08, "7,648", "both models", GREEN)
    text(slide, "Hybrid − ItemKNN", 7.20, 3.17, 2.0, 0.24,
         size=12, color=GRAY, align=PP_ALIGN.CENTER)
    text(slide, "+0.005638", 7.20, 3.49, 2.0, 0.33,
         size=21, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    text(slide, "95% CI [0.005201, 0.006088] · Holm p = 0.0024",
         5.42, 4.34, 3.78, 0.24, size=10.5, color=MID,
         align=PP_ALIGN.CENTER)
    add_experiment_finding(slide,
                           "BPR is weak alone but adds complementary hits; the hybrid gain is significant.")
    add_notes(slide, "Experiment 2: BPR Analysis", "10:30–12:10 (100 sec)",
              "The surprising result is not simply that BPR loses; it is that BPR still helps the winning hybrid. The long "
              "tail is one reason for the weak standalone result, because many channels do not have enough positive examples "
              "to learn stable factors. The negatives are noisy as well: a viewer may miss a channel because it was offline "
              "or never exposed, not because they disliked it. Uniform negative sampling then gives BPR many easy comparisons, "
              "and its pairwise objective is not exactly the same as ranking the full catalog. We checked five random seeds, "
              "so this is not just an unlucky run. Still, BPR finds 5,540 positives that ItemKNN misses. That complementary "
              "signal lifts the hybrid by 0.005638 NDCG, and the confidence interval remains above zero after correction, so "
              "the smaller contribution is statistically credible.")

    # 11 — Experiment 3: representation and subgroup analysis
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Experiment 3: Subgroup Analysis", "", 11, seal)
    add_experiment_question(slide,
                            "Do counts help, and which user or channel subgroups are hardest?")
    picture_fit(slide, ROOT / "outputs/assignment2/figures/feature_representation.png",
                0.48, 1.52, 4.18, 2.52)
    picture_fit(slide, ROOT / "outputs/assignment2/figures/channel_popularity_subgroups.png",
                5.02, 1.52, 4.50, 2.52)
    text(slide, "Binary vs. count: 0.12584 vs. 0.11694 NDCG",
         0.74, 4.18, 3.70, 0.22, size=10.5, color=TEAL,
         bold=True, align=PP_ALIGN.CENTER)
    text(slide, "Least-popular target recall: 0.0328",
         5.36, 4.18, 3.70, 0.22, size=10.5, color=TEAL,
         bold=True, align=PP_ALIGN.CENTER)
    add_experiment_finding(slide,
                           "Distinct-channel history beats counts; sparse targets and long histories are hardest.")
    add_notes(slide, "Experiment 3: Subgroup Analysis", "12:10–13:40 (90 sec)",
              "We then looked beyond the overall average to understand where the models succeed and fail. Binary ItemKNN "
              "beats the count-weighted version, 0.12584 versus 0.11694 NDCG, which makes sense for this task: repeated views "
              "tell us about loyalty to channels the viewer already knows, while we are trying to predict a first-time "
              "discovery. The much larger gap appears across target popularity. Recall is only 0.0328 for the least-popular "
              "quartile, but rises above 0.40 for the most-popular quartile. Performance also declines for viewers with long "
              "histories, probably because the easiest neighboring channels have already been consumed and the remaining "
              "choices are less obvious. At the extreme, a viewer with no usable history cannot be personalized by these "
              "collaborative models at all, so the product still needs a popularity fallback.")

    # 12 — Experiment 4: temporal robustness
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Experiment 4: Temporal Robustness", "", 12, seal)
    add_experiment_question(slide,
                            "Does the model ranking persist when the target window moves through time?")
    picture_fit(slide, ROOT / "outputs/assignment2/figures/rolling_backtest.png",
                0.45, 1.48, 5.58, 3.08)
    add_flat_table(slide, [
        ["Model", "Early", "Middle", "Late"],
        ["Hybrid", "0.1591", "0.1491", "0.1315"],
        ["ItemKNN", "0.1467", "0.1407", "0.1258"],
        ["BPR", "0.0723", "0.0681", "0.0542"],
        ["Best popularity", "0.0427", "0.0411", "0.0378"],
    ], 6.05, 1.62, [1.35, 0.78, 0.78, 0.78], row_h=0.48, font_size=10.8)
    text(slide, "NDCG@10 across rolling-origin windows", 6.20, 4.20, 3.15, 0.22,
         size=10.5, color=MID, align=PP_ALIGN.CENTER)
    add_experiment_finding(slide,
                           "Every window preserves Hybrid > ItemKNN > BPR > popularity, although NDCG declines.")
    add_notes(slide, "Experiment 4: Temporal Robustness", "13:40–14:55 (75 sec)",
              "A single test week can always be unusually easy or hard, so we repeated the comparison in early, middle, and "
              "late windows. Absolute accuracy does decline: the hybrid moves from 0.1591 NDCG early to 0.1315 late, and the "
              "other models show the same direction. What gives us confidence is that the ordering never changes. Hybrid "
              "stays first, ItemKNN stays second, BPR stays third, and popularity stays last. That consistency makes the "
              "relative conclusion much stronger than a result from one lucky holdout. At the same time, the falling scores "
              "are an operational warning: viewer behavior and channel availability drift, so a deployed model would need "
              "monitoring and regular retraining rather than assuming one offline score will remain valid.")

    # 13 — Experiment 5: scalability
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Experiment 5: Scalability", "", 13, seal)
    add_experiment_question(slide,
                            "Do the conclusions remain stable as the user cohort grows from 100K to 1M?")
    picture_fit(slide, ROOT / "outputs/assignment2/figures/scalability_ndcg.png",
                0.45, 1.48, 5.62, 3.08)
    add_flat_table(slide, [
        ["Scale", "Hybrid", "ItemKNN", "BPR"],
        ["100K", "0.1317", "0.1267", "0.0558"],
        ["200K", "0.1301", "0.1261", "0.0530"],
        ["500K", "0.1289", "0.1269", "0.0419"],
        ["1M", "0.1317", "0.1304", "0.0430"],
    ], 6.12, 1.62, [0.82, 0.96, 0.96, 0.86], row_h=0.48, font_size=10.6)
    text(slide,
         "Matched protocol: seed 258 · same search grid · full-catalog ranking\nCohorts are not nested; interpret this as robustness, not a causal learning curve.",
         6.14, 4.10, 3.45, 0.48, size=9.8, color=MID,
         align=PP_ALIGN.CENTER)
    add_experiment_finding(slide,
                           "Hybrid and ItemKNN remain stable; BPR weakens as the channel catalog expands.")
    add_notes(slide, "Experiment 5: Scalability", "14:55–16:10 (75 sec)",
              "We also wanted to know whether the story survives when the system grows. Using the same seed and search "
              "protocol, we repeated the experiment from 100,000 users up to one million. Hybrid and ItemKNN remain "
              "remarkably stable: hybrid stays between 0.1289 and 0.1317 NDCG, and ItemKNN stays in a similarly narrow range. "
              "BPR moves in the opposite direction, falling from 0.0558 to roughly 0.043 as the catalog expands. In other "
              "words, adding interactions does not automatically solve the problem when it also creates a much larger and "
              "sparser item space. These cohorts are not nested, so I would not call this a causal learning curve. What we "
              "can say is that the overall conclusion is robust and that the pipeline can support the larger experiment.")

    # 14 — Related work
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Connection to Prior Work",
               "", 14, seal)
    add_flat_table(slide, [
        ["Aspect", "LiveRec (Rappaz et al., 2021)", "This study"],
        ["Target", "Currently available streams", "Never-watched channels"],
        ["Repeat behavior", "Central signal", "Excluded from primary target"],
        ["Availability", "Explicitly modeled", "Seven-day activity proxy"],
        ["Model family", "Self-attentive sequential ranking", "ItemKNN, BPR, Hybrid"],
    ], 0.72, 1.60, [1.62, 3.65, 3.65], row_h=0.53, font_size=11.5)
    text(slide, "Relevant methodological references", 0.72, 4.42, 2.65, 0.25,
         size=13, color=NAVY, bold=True)
    text(slide,
         "Rendle et al. (2009): Bayesian Personalized Ranking · "
         "He et al. (2020): LightGCN for graph collaborative filtering",
         3.10, 4.39, 6.20, 0.48, size=11.5, color=GRAY)
    add_notes(slide, "Connection to Prior Work", "16:10–17:25 (75 sec)",
              "This work is closely related to LiveRec because it uses the same Twitch source, but it is not a direct "
              "replication. LiveRec recommends streams that are currently available and treats repeat consumption as an "
              "important signal. We deliberately ask a different question by removing channels the viewer already knows "
              "and measuring future first-time discovery. LiveRec also models exact availability, while we only have a "
              "recent-activity proxy, which is one reason our missing interactions are difficult to interpret. Methodologically, "
              "Rendle and colleagues provide the BPR objective we test, and LightGCN is a natural next graph-based extension. "
              "Because the targets, candidates, and metrics differ, prior work guides our design, but its numerical results "
              "should not be compared directly with ours.")

    # 15 — Limitations and future work
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Limitations and Next Steps",
               "The dominant open problems are candidate generation, live availability, and objective alignment.",
               15, seal)
    rows = [
        ["Limitation", "Consequence", "Next experiment"],
        ["Catalog cold-start", "~12% of novel positives cannot be ranked", "Content or creator metadata"],
        ["Unknown live status", "Missing views are noisy negatives", "Timestamped availability mask"],
        ["Uniform BPR negatives", "Training sees mostly easy comparisons", "Popularity-aware hard negatives"],
        ["Offline metrics", "No direct evidence of satisfaction", "Online A/B test: watch time and exposure"],
        ["Accuracy–diversity tradeoff", "Best NDCG reduces catalog coverage", "Two-stage diversity reranking"],
    ]
    add_flat_table(slide, rows, 0.62, 1.52, [2.15, 3.40, 3.35], row_h=0.54,
                   font_size=11.2)
    text(slide,
         "A stronger model alone cannot solve missing candidates or unavailable channels.",
         1.05, 4.85, 7.90, 0.28, size=14, color=TEAL, bold=True,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Limitations and Next Steps", "17:25–18:45 (80 sec)",
              "The remaining gaps are larger than a single model upgrade. About twelve percent of future positive channels "
              "never appear in the fit catalog, so a collaborative ranker has no representation to score. Solving that "
              "requires creator, game, language, or text features, but this dataset gives us identifiers and interaction "
              "times only. We also do not know exact live status, which means an unobserved pair may reflect unavailability "
              "rather than dislike. For BPR, harder or popularity-aware negatives would make training look more like the "
              "full-catalog decision. And finally, offline NDCG cannot tell us whether viewers were satisfied or whether "
              "exposure was fair to creators. The practical next step is an online test that measures watch time, retention, "
              "and exposure, potentially followed by a diversity-aware reranker.")

    # 16 — Conclusion
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Conclusions", "", 16, seal)
    conclusions = [
        ("1", "Personalization is valuable",
         "Hybrid NDCG@10 = 0.1315 versus 0.0370 for global popularity."),
        ("2", "ItemKNN matches the observed structure",
         "Local co-view relationships are more reliable than the current latent factors."),
        ("3", "Hybrid gains are real but not universal",
         "Accuracy improves significantly, while catalog coverage decreases."),
        ("4", "More data is not an automatic remedy",
         "BPR weakens as the item space expands; availability and negatives remain limiting."),
    ]
    for i, (num, heading, body) in enumerate(conclusions):
        y = 1.55 + i * 0.83
        rect(slide, 0.78, y, 0.48, 0.48, TEAL)
        text(slide, num, 0.78, y + 0.09, 0.48, 0.24, size=15, color=WHITE,
             bold=True, align=PP_ALIGN.CENTER)
        text(slide, heading, 1.48, y - 0.02, 3.05, 0.28,
             size=14.5, color=NAVY, bold=True)
        text(slide, body, 4.52, y - 0.01, 4.62, 0.52,
             size=12.5, color=GRAY)
    rect(slide, 0.92, 4.90, 8.16, 0.04, TEAL)
    text(slide,
         "Recommendation quality depends on aligning the data, target definition, and learning objective.",
         1.02, 5.02, 7.96, 0.24, size=13.5, color=NAVY, bold=True,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Conclusions", "18:45–20:00 (75 sec)",
              "Let me close with the practical takeaway. Personalization clearly matters: the hybrid reaches 0.1315 NDCG, "
              "compared with about 0.037 for popularity. ItemKNN is the strongest individual model because local co-view "
              "relationships remain useful even when the data is extremely sparse. BPR is much weaker on its own, but it "
              "finds some channels ItemKNN misses, and that complementary signal gives the hybrid a statistically credible "
              "gain. The trade-off is lower catalog coverage, and simply adding more users does not repair BPR when the item "
              "space grows at the same time. So the main lesson is not that the most complex model wins. The better system is "
              "the one whose data representation, training objective, and evaluation target all match the discovery problem "
              "we actually want to solve.")

    flatten_presentation_effects(prs)
    prs.save(OUT)
    lines = [
        "# Group 9 Twitch presentation — speaker notes",
        "",
        "Deck: `Group_9_Presentation_Twitch.pptx`",
        "",
        "The planned narration totals 20 minutes.",
        "",
    ]
    for index, item in enumerate(SLIDE_NOTES, 1):
        lines.extend([
            f"## {index}. {item['title']}", "", f"Timing: {item['timing']}", "",
            item["note"], "",
        ])
    NOTES_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {NOTES_OUT}")


if __name__ == "__main__":
    build()
