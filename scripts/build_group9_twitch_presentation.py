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


def narration(*parts: str) -> str:
    """Join source-wrapped narration into one natural PowerPoint notes paragraph."""
    return " ".join(" ".join(part.split()) for part in parts)


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
    text(slide, "Wen-Chieh Lo · Cheng-Yi Chen · Cheng-Yan Juang", 2.20, 3.32, 5.60, 0.30,
         size=15, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    text(slide, "CSE 258 · Fall 2026", 2.20, 3.72, 5.60, 0.26,
         size=12.5, color=MID, align=PP_ALIGN.CENTER)
    slide.shapes.add_picture(BytesIO(seal), Inches(8.72), Inches(0.25),
                             Inches(0.78), Inches(0.78))
    add_footer(slide, 1)
    add_notes(slide, "Twitch New-Channel Recommendation", "0:00–0:38 (38 sec)",
              narration(
                  "Let me begin with the distinction that defines this project. Most recommendation systems are happy "
                  "when a viewer returns to something familiar, but our target is discovery: we want to predict the next "
                  "channel that viewer will watch for the first time.",
                  "A new channel is therefore user-specific. It does not have to be newly created; it simply has not "
                  "appeared anywhere in that viewer's observed history. This is a natural recommendation problem because "
                  "the Twitch catalog is far too large for anyone to explore manually. Our job is to narrow that catalog "
                  "to ten relevant unseen choices. To understand why that is difficult, the next slide looks at how uneven "
                  "the available interaction evidence really is."
              ))

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
    add_notes(slide, "Motivation", "0:38–1:41 (63 sec)",
              narration(
                  "The first thing to notice is the mismatch between catalog size and behavioral evidence. The benchmark "
                  "contains more than 162,000 channels, while an average viewer contributes only about thirty interactions. "
                  "The chart is an empirical cumulative distribution: moving from left to right, it tells us what share of "
                  "channels have no more than a given number of observations.",
                  "At one interaction, we already cover 45 percent of the catalog. At two interactions, that rises to 60 "
                  "percent, and by five interactions it reaches 77 percent. So for most channels, the model has almost no "
                  "evidence from which to learn. Attention is concentrated at the other end as well: the top one percent of "
                  "channels receives 60 percent of all interactions. That is why popularity is not a trivial baseline; it is "
                  "a strong description of what viewers already do, and personalization has to beat it.",
                  "There is one more complication. Twitch is a live platform, so a missing view may mean the viewer was not "
                  "interested, but it may also mean the channel was offline or never exposed. With that motivation in place, "
                  "the next slide turns these data constraints into a precise research question."
              ))

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
    add_notes(slide, "Research Objective", "1:41–2:26 (45 sec)",
              narration(
                  "Given those constraints, our central question is simple to state: can past viewing history predict "
                  "which unseen Twitch channel a viewer will discover next? We organize the answer around three objectives.",
                  "The first is ranking quality. We compare a strong popularity baseline with ItemKNN, BPR, and a hybrid, "
                  "all producing a Top-10 list from channels the viewer has never watched. The second is explanation. A "
                  "leaderboard alone is not enough, so we study why the methods differ, which signals help, and which users "
                  "or channels remain difficult. The third is robustness. We repeat the comparison across time and from "
                  "100,000 to one million users.",
                  "Across every experiment, the outcome is the same: a future first-time channel view in a chronological "
                  "holdout. Before describing the protocol, the next slide clarifies exactly what information the dataset "
                  "does—and does not—give us."
              ))

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
    add_notes(slide, "Dataset Overview", "2:26–3:26 (60 sec)",
              narration(
                  "The complete Twitch source is genuinely large: 15.5 million users, almost 475 million viewing "
                  "interactions, and roughly 790,000 channel identifiers over forty-three relative days. Our main model "
                  "comparison uses the official 100,000-user benchmark, which still contains 3.05 million interactions and "
                  "162,625 channels. The larger source returns later when we test scalability.",
                  "The more important point is what each row means. These are viewing sessions, not ratings. A recorded view "
                  "is positive implicit feedback, but an absent row is not a statement that the viewer disliked the channel. "
                  "It may simply reflect no exposure or no live availability. The five fields are an anonymous user, a stream "
                  "identifier, a channel identifier, and start and stop slots.",
                  "We do not have game class, language, creator profile, text, or any other semantic category. That means we "
                  "cannot group channels by class or ask a content-based model to generalize to a new item. The system must "
                  "learn almost entirely from who watched what and when. Because temporal order is the strongest structure "
                  "we do have, the next slide shows how we use it to create a realistic and leakage-safe experiment."
              ))

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
    add_notes(slide, "Experimental Protocol", "3:26–4:37 (71 sec)",
              narration(
                  "This protocol is designed to make the offline experiment resemble a real recommendation decision. Read "
                  "the top row from left to right. Days zero through twenty-nine train the candidate models. Days thirty "
                  "through thirty-five are validation: we choose neighborhood size, factor settings, and hybrid weights there, "
                  "without looking at the final answer. Once those choices are frozen, we refit the selected model on all data "
                  "through day thirty-five. Days thirty-six through forty-two are then used exactly once as the simulated future.",
                  "The second row shows what happens for one test case. We take the viewer's history available before that "
                  "target day, remove every channel they have already watched, score the remaining channels that appeared in "
                  "the fit period, and keep the Top-10. A hit occurs when a channel viewed for the first time in the future "
                  "appears in that list. The filtering step is important because otherwise a model could look good by "
                  "recommending familiar favorites, which is not our research target.",
                  "Every mapping, popularity count, similarity, and embedding is built from past data only. The held-out test "
                  "contains 53,212 users and 104,818 user-day cases. Since the same viewer can contribute several cases, we "
                  "estimate uncertainty by resampling whole users in 10,000 bootstrap draws. With that evaluation contract "
                  "fixed, we can now compare models without changing the definition of success."
              ))

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
    add_notes(slide, "Compared Models", "4:37–5:50 (73 sec)",
              narration(
                  "The comparison moves from the simplest explanation of behavior to increasingly personalized ones. "
                  "Popularity recommends the channels with the most distinct viewers, and recent popularity repeats that "
                  "idea using only the latest seven fit days. These baselines tell us whether a complex model is adding value "
                  "or merely rediscovering the global head of the catalog.",
                  "ItemKNN is the first personalized model. For every channel a viewer has watched, it looks for other channels "
                  "with overlapping audiences, using cosine similarity between binary user sets. The intuition is local and "
                  "easy to explain: people who watched these channels also tended to watch those channels. We also build a "
                  "count-weighted version to test whether repeated viewing should make a known channel more influential. For "
                  "a discovery task, that is not obviously helpful, because repeat behavior describes loyalty rather than novelty.",
                  "BPR takes a different view. It learns latent user and channel factors and trains an observed channel to "
                  "score above a sampled unobserved channel. In principle, that can capture global structure beyond immediate "
                  "neighbors. Finally, the hybrid standardizes the BPR and ItemKNN scores separately for each user, combines "
                  "them with weight alpha, and can subtract a popularity penalty. This design lets validation decide whether "
                  "the two personalized models make useful different errors. The next question is how we choose those settings "
                  "without letting the test set influence the answer."
              ))

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
    add_notes(slide, "Model Selection", "5:50–6:56 (66 sec)",
              narration(
                  "Every setting on this slide is selected using validation data before we inspect the final test. For "
                  "ItemKNN, we compare 50, 100, and 200 retained neighbors, and validation chooses 200. That suggests useful "
                  "co-view evidence is spread across a reasonably broad local neighborhood rather than only a few nearly "
                  "identical channels. For BPR, the grid varies factor dimension, regularization, and training duration. The "
                  "selected configuration uses 64 factors, learning rate 0.03, regularization 0.0025, and twenty epochs.",
                  "The chart on the left is especially informative because alpha moves from ItemKNN alone at zero toward BPR "
                  "alone at one. Performance stays high while ItemKNN dominates and then drops sharply near pure BPR. The best "
                  "validation setting is alpha 0.75 with no popularity penalty, so BPR receives meaningful but secondary weight. "
                  "In other words, validation expects complementarity, not replacement.",
                  "There is also a practical engineering issue. A dense similarity matrix for more than 162,000 channels would "
                  "contain tens of billions of entries. We avoid creating it by multiplying sparse blocks and keeping only the "
                  "top 200 neighbors per item. The seed, search grid, and selected configuration are recorded so the experiment "
                  "can be reproduced. With the models fixed, the next slide explains exactly how we judge them."
              ))

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
    add_notes(slide, "Evaluation and Inference", "6:56–8:04 (68 sec)",
              narration(
                  "Before looking at the leaderboard, we need to separate several meanings of better. Recall at ten asks what "
                  "fraction of the viewer's future first-time channels appears anywhere in the Top-10. If two relevant channels "
                  "exist and we retrieve one, recall is one half. NDCG adds position: a correct answer at rank one earns more "
                  "credit than the same answer at rank ten. Because recommendation lists are ordered, NDCG at ten is our primary "
                  "validation metric.",
                  "Hit rate is easier to interpret at the case level: did this user-day receive at least one successful suggestion? "
                  "Coverage asks a different question—what fraction of the fit catalog is ever exposed across all recommendations? "
                  "A model can have strong NDCG and poor coverage if it repeatedly relies on the same safe channels. Novelty and "
                  "long-tail exposure give two more views of that concentration.",
                  "Candidate coverage prevents us from blaming the ranker for an impossible answer. If a future positive channel "
                  "never appeared in the fit catalog, no collaborative model could score it. Finally, all model comparisons are "
                  "paired on the same cases. We bootstrap whole users, not individual days, and use Holm correction across tests. "
                  "Now that we know how to read both accuracy and breadth, we can turn to the main result."
              ))

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
    add_notes(slide, "Experiment 1: Model Comparison", "8:04–9:25 (81 sec)",
              narration(
                  "This first experiment asks the most direct question in the project: when every model receives the same "
                  "history and ranks the same unseen catalog, which one places future discoveries closest to the top? The hybrid "
                  "finishes first with NDCG 0.13148 and Recall 0.22342. ItemKNN is the strongest individual model at 0.12584 "
                  "NDCG, while BPR reaches only 0.05420 and recent popularity reaches 0.03779. Because the head of this catalog attracts "
                  "so much attention, beating popularity by this margin is meaningful: it tells us that a viewer's own "
                  "history contains information that cannot be recovered from aggregate traffic alone.",
                  "The hybrid improves NDCG by 4.48 percent over ItemKNN, and later we test whether that difference is reliable. BPR is "
                  "weak as a complete recommender, yet some part of its latent representation must be correcting mistakes "
                  "made by the neighborhood model. Otherwise adding it could not improve the ranking.",
                  "Accuracy, however, is only one side of the result. The hybrid exposes 26.36 percent of the catalog, versus "
                  "36.71 percent for binary ItemKNN. Count-weighted ItemKNN reaches 40.50 percent coverage, even though its "
                  "NDCG falls to 0.11694. If our sole objective is putting the most likely "
                  "discovery near the top, the hybrid is the best choice. If we also care about giving a broader set of "
                  "creators an opportunity to be seen, ItemKNN or a second-stage diversity rule may be preferable. The most "
                  "interesting question is why a model that performs poorly alone can still improve the winner. That is the focus of the next experiment."
              ))

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
    add_notes(slide, "Experiment 2: BPR Analysis", "9:25–11:06 (101 sec)",
              narration(
                  "The surprising result is not simply that BPR loses to ItemKNN. The more useful question is why it loses, "
                  "and why it still helps the winning hybrid. BPR learns one vector for every user and every channel. That "
                  "works best when each vector receives enough evidence. Here, most channels sit in the extreme long "
                  "tail, so many item factors are updated from only a handful of positive observations. A local co-view method "
                  "can reuse concrete audience overlap, while a latent model estimates dozens of parameters from the same scarce evidence.",
                  "The definition of a negative is another mismatch. BPR samples an unobserved channel and trains the observed "
                  "one to rank above it. On Twitch, unobserved does not necessarily mean disliked. The channel may have been "
                  "offline, the viewer may never have encountered it, or it may not have been available in the viewer's time "
                  "zone. Uniform sampling also selects irrelevant tail items, creating easy comparisons that "
                  "do not resemble the difficult decision among plausible Top-10 candidates. Finally, BPR optimizes a sampled "
                  "pairwise objective, whereas evaluation ranks the full catalog. More users therefore do not automatically "
                  "fix the objective. Five random seeds show the poor result is not one unlucky initialization.",
                  "The overlap counts explain why we did not discard BPR. ItemKNN alone finds 22,559 successful cases, both "
                  "models find 7,648, and BPR uniquely finds another 5,540 that ItemKNN misses. Those unique hits are relatively "
                  "few, but they contain complementary information. Adding BPR raises NDCG by "
                  "0.005638 over ItemKNN. The 95 percent confidence interval, from 0.005201 to 0.006088, stays entirely above "
                  "zero, and the Holm-adjusted p-value is 0.0024. The interpretation is not that BPR is generally "
                  "better; it is that BPR makes different errors, and a carefully weighted version improves the local model. "
                  "That leads naturally to the next question: do these conclusions hold equally for every kind of viewer and "
                  "channel?"
              ))

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
    add_notes(slide, "Experiment 3: Subgroup Analysis", "11:06–12:42 (96 sec)",
              narration(
                  "An overall average can hide the fact that a method works well for one person and poorly for another, so "
                  "this experiment separates the result by representation, target popularity, and user history. We begin with "
                  "the left chart. Binary ItemKNN treats a channel as either present or absent in the viewer's history. The "
                  "count version gives additional weight to channels watched repeatedly. Binary performs better, with NDCG "
                  "0.12584 compared with 0.11694. For a discovery task, that result is intuitive. Repetition is a strong sign "
                  "of loyalty to something the viewer already knows, but it can make the profile narrower and dominate the "
                  "signal from less frequent interests. A set of distinct watched channels gives a cleaner description of "
                  "which communities the viewer has explored.",
                  "The larger inequality appears on the channel side. Recall is 0.0328 for targets in the least-popular "
                  "quartile, then rises steadily and exceeds 0.40 for the most-popular quartile. Tail channels have fewer "
                  "co-view links for ItemKNN and fewer positive updates for BPR, so both models have much less evidence exactly "
                  "where discovery could be most valuable. The models are not uniformly good or bad; quality depends on how much "
                  "evidence exists for the future target.",
                  "User history creates a second pattern. People with a small but nonzero set of distinct channels often give "
                  "ItemKNN a focused neighborhood from which to expand. As history becomes very long and varied, the profile "
                  "mixes several interests, and easy neighboring channels have already been removed by the unseen-item filter. "
                  "At the extreme, a viewer with zero usable history cannot receive collaborative personalization at all. The "
                  "responsible behavior is then a fallback such as recent popularity, context, or an onboarding signal. Having identified these subgroup effects, "
                  "we next ask whether the model ordering remains stable when the target period changes."
              ))

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
    add_notes(slide, "Experiment 4: Temporal Robustness", "12:42–13:52 (70 sec)",
              narration(
                  "Time can change the available evidence, so one final week might be unusually easy or difficult. "
                  "To test this, we repeat the entire comparison with rolling origins. In each window, training remains in the "
                  "past and the target remains in the future; we move the boundary rather than allowing future information to "
                  "enter the model.",
                  "The absolute values do change. Hybrid NDCG falls from 0.1591 in the early window to 0.1491 in the middle and "
                  "0.1315 in the late window. ItemKNN, BPR, and popularity decline in the same direction. That may reflect changes "
                  "in active channels, audience behavior, or harder discoveries. The "
                  "important robustness result is that the ordering never changes. Hybrid remains first, ItemKNN second, BPR "
                  "third, and popularity last in every window. This makes the relative conclusion much stronger than a result "
                  "from one holdout.",
                  "At the same time, stable ordering should not be confused with stable product performance. A deployment team "
                  "would still need to monitor the absolute NDCG, candidate coverage, and the distribution of active channels. "
                  "Retraining should be triggered when those quantities drift. Time supports the comparison while also "
                  "warning us that no single offline score is permanent. The next experiment changes a different dimension: "
                  "instead of moving the time window, we increase the system from 100,000 users to one million."
              ))

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
    add_notes(slide, "Experiment 5: Scalability", "13:52–15:26 (94 sec)",
              narration(
                  "Scalability has two meanings in this experiment. The first is computational: can the same pipeline train "
                  "and rank a much larger cohort? The second is statistical: when more interactions arrive, do the conclusions "
                  "remain stable? We repeat the comparison at 100,000, 200,000, 500,000, and one "
                  "million users. Every run uses seed 258, the same validation limit of 2,000 users, the same test limit of "
                  "5,000 users, the same hyperparameter search, and full-catalog ranking. Keeping those choices matched prevents "
                  "a larger cohort from receiving an easier protocol.",
                  "Hybrid and ItemKNN are remarkably stable. Hybrid stays between 0.1289 and 0.1317 NDCG, while ItemKNN remains "
                  "between 0.1261 and 0.1304. This suggests that the local co-view structure used by ItemKNN is already estimated "
                  "reasonably well at the smaller scale. BPR behaves differently. It begins at 0.0558 for 100,000 users and "
                  "falls to about 0.042 or 0.043 at the two largest scales. More user interactions arrive, but the channel "
                  "catalog expands at the same time, creating more sparse factors and a harder negative-sampling space. Scale "
                  "amplifies the mismatch seen earlier.",
                  "There is an important limitation to the claim. These cohorts are independently constructed rather than "
                  "nested subsets of the same population, so catalog composition and user mix can change with "
                  "training size. This is evidence of robustness and engineering scalability, not a causal learning curve. A "
                  "strict data-size experiment would hold the test users and catalog fixed while adding nested training data. "
                  "What we can conclude is that the ranking Hybrid above ItemKNN, BPR, and "
                  "popularity survives at one million users, and that more data alone does not repair a poorly matched learning "
                  "objective. To place that contribution in context, the next slide compares our target with the closest prior "
                  "work on the same Twitch source."
              ))

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
    add_notes(slide, "Connection to Prior Work", "15:26–16:49 (83 sec)",
              narration(
                  "The closest prior work is LiveRec by Rappaz, McAuley, and Aberer, because it introduced and studied this "
                  "Twitch source. Sharing a dataset does not mean sharing a prediction task. LiveRec recommends "
                  "streams that are currently available and treats repeat viewing as a central behavioral signal. Our study "
                  "removes every previously watched channel and asks which unfamiliar channel the viewer will discover next. "
                  "That change affects the labels, candidates, features, and metrics. A method "
                  "that is excellent at returning viewers to a favorite creator may receive no credit in our experiment.",
                  "Availability is another key distinction. LiveRec can reason about what is live at recommendation time. Our "
                  "benchmark lacks a complete availability mask, so we use recent activity as a proxy. This makes missing views "
                  "ambiguous and negative sampling difficult. We should not compare our NDCG directly with LiveRec's values, "
                  "because the model answers a different question over a different catalog.",
                  "On the methodological side, Rendle and colleagues introduced Bayesian Personalized Ranking, the pairwise "
                  "objective used in our latent model. Our result adds a useful boundary condition: an objective designed for "
                  "implicit ranking can struggle when items are sparse and non-observation reflects live "
                  "availability. LightGCN is a natural next extension because it propagates information through the user-item "
                  "graph without heavy transformations, although it still inherits the candidate and negative definitions. "
                  "Prior work gives us both a foundation and a warning: a more advanced architecture "
                  "does not remove a mismatch between data and task. That point becomes clearer when we state the limitations "
                  "of the current study directly."
              ))

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
    add_notes(slide, "Limitations and Next Steps", "16:49–18:22 (93 sec)",
              narration(
                  "The limitations show why improvement should begin with the system definition rather than "
                  "adding another model. First, about twelve percent of future positive channels never appear in the fit "
                  "catalog. For those cases, ItemKNN has no neighbors and BPR has no learned item vector, so the correct channel "
                  "is impossible to rank. This is catalog cold-start, not a ranking failure. A content-aware candidate "
                  "generator could use creator identity, game category, language, title text, or other metadata, but the current "
                  "dataset supplies only identifiers and interaction times. We therefore cannot perform that experiment here.",
                  "Second, exact live status is unknown. Treating every unobserved user-channel pair as a possible negative mixes "
                  "together dislike, lack of exposure, and simple unavailability. The cleanest next dataset would include a "
                  "timestamped availability mask, so training compares only channels the viewer could watch. BPR could also use "
                  "popularity-aware or hard negatives drawn from active, plausible "
                  "channels. That would create more informative comparisons than uniform sampling, although it would not fully "
                  "eliminate exposure bias.",
                  "Third, our best model reduces catalog coverage. That is not automatically wrong, but the "
                  "choice depends on the platform objective. A two-stage system could first retrieve accurate candidates with "
                  "the hybrid and then rerank them under an explicit diversity or creator-exposure constraint. We would report "
                  "the accuracy cost of additional coverage rather than hiding the trade-off in one score.",
                  "Finally, all evidence is offline. NDCG cannot tell us whether a recommendation creates satisfying watch "
                  "time, improves retention, or distributes opportunity fairly. The decisive follow-up is an online A/B test "
                  "that measures viewer response and creator exposure together. These limitations qualify the result, but they "
                  "do not erase the consistent pattern we observed. The final slide summarizes what that pattern teaches us."
              ))

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
    add_notes(slide, "Conclusions", "18:22–20:00 (98 sec)",
              narration(
                  "Let me close by returning to the question from the beginning: can a viewer's past behavior identify a channel "
                  "they have never watched before? In this dataset, the answer is yes. The hybrid reaches about 0.1315 NDCG, "
                  "compared with roughly 0.037 for global popularity. That gap is large enough to show that personalization is "
                  "not merely reproducing the most visible part of Twitch. Even under highly sparse implicit feedback, the "
                  "pattern of channels a person has explored contains useful information about what they may discover next.",
                  "Among the individual models, ItemKNN fits the observed structure best. It can turn local audience overlap "
                  "into a recommendation without estimating a high-dimensional representation for every rare channel. BPR is "
                  "much weaker alone because sparse item factors, ambiguous negatives, and uniform sampling do not align well "
                  "with full-catalog discovery. Yet BPR is not useless. It produces a smaller set of unique hits that ItemKNN "
                  "misses, and after validation assigns it the right weight, that complementary signal gives the hybrid a "
                  "statistically credible improvement.",
                  "The winning score comes with two cautions. Hybrid coverage is lower than ItemKNN coverage, so improving "
                  "viewer accuracy may concentrate creator exposure. And when we increase the cohort to one million users, BPR "
                  "does not recover, because the channel space becomes larger and sparser at the same time. More data is useful "
                  "only when it provides needed evidence; volume cannot compensate for missing availability, cold "
                  "items, or a mismatched learning objective.",
                  "The broader lesson is not that the most complex algorithm wins. A reliable system begins "
                  "by defining the behavior we truly want—in our case, first-time discovery—then aligning the candidate set, "
                  "representation, training objective, and evaluation protocol with that behavior. Here, a transparent local "
                  "model provides the strongest foundation, a latent model contributes selective complementary information, and "
                  "the hybrid works because their roles are validated rather than assumed. Thank you."
              ))

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
