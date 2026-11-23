"""Rebuild the Twitch research talk using Group_9_Presentation.pptx as its template."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "Group_9_Presentation.pptx"
OUT = ROOT / "presentation" / "Group_9_Presentation_Twitch.pptx"
NOTES_OUT = ROOT / "presentation" / "Group_9_Presentation_Twitch_notes.md"

FONT = "Calibri"
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
    text(slide, title_value, 0.68, 0.28, 8.10, 0.45,
         size=24, color=NAVY, bold=True)
    rect(slide, 0.69, 0.96, 8.90, 0.045, TEAL)
    add_seal(slide, seal)
    if takeaway:
        text(slide, takeaway, 0.70, 1.10, 8.85, 0.34,
             size=13.5, color=TEAL, bold=True)
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
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if r == 0 else (WHITE if r % 2 else LIGHT)
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
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


def add_process_arrow(slide, x: float, y: float) -> None:
    shape = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(0.40), Inches(0.28)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = TEAL
    no_line(shape)


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs = Presentation(TEMPLATE)
    seal = template_seal(prs)
    clear_template_slides(prs)
    blank = prs.slide_layouts[10]
    SLIDE_NOTES.clear()

    # 1 — Title
    slide = prs.slides.add_slide(blank)
    text(slide, "Twitch New-Channel Recommendation", 0.72, 1.36, 8.56, 0.78,
         size=31, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    rect(slide, 1.55, 2.31, 6.90, 0.055, TEAL)
    text(slide,
         "Ranking unseen channels from highly sparse implicit feedback",
         1.15, 2.60, 7.70, 0.46, size=19, color=GRAY,
         align=PP_ALIGN.CENTER)
    text(slide, "Wen-Chieh Lo · Bing-You Yu", 2.20, 3.35, 5.60, 0.34,
         size=16, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    text(slide, "CSE 258 · Fall 2026", 2.20, 3.78, 5.60, 0.30,
         size=13.5, color=MID, align=PP_ALIGN.CENTER)
    slide.shapes.add_picture(BytesIO(seal), Inches(8.72), Inches(0.25),
                             Inches(0.78), Inches(0.78))
    add_footer(slide, 1)
    add_notes(slide, "Twitch New-Channel Recommendation", "0:00–0:30 (30 sec)",
              "This project studies new-channel recommendation on Twitch. Rather than "
              "predicting repeat viewing, we rank channels that a viewer has never watched "
              "before and ask whether those channels are discovered in the future. The main "
              "question is which modeling assumptions work under extremely sparse implicit feedback.")

    # 2 — Research question and contributions
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Research Question and Contributions",
               "Can past viewing behavior predict future discovery of unseen channels?", 2, seal)
    text(slide, "Research question", 0.72, 1.62, 2.25, 0.34,
         size=16, color=NAVY, bold=True)
    text(slide,
         "Given a viewer's history, rank ten fit-catalog channels that the viewer has never watched.",
         0.72, 2.03, 2.70, 1.15, size=15.5, color=GRAY)
    rect(slide, 3.55, 1.54, 0.035, 2.95, GRID)
    text(slide, "Contributions", 3.90, 1.62, 2.0, 0.34,
         size=16, color=NAVY, bold=True)
    bullets(slide, [
        "Leakage-safe chronological evaluation with full-catalog ranking",
        "Comparison of popularity, ItemKNN, BPR, and a score-level hybrid",
        "Accuracy–diversity, cold-start, subgroup, temporal, and scaling analyses",
        "Empirical diagnosis of why BPR underperforms on this dataset",
    ], 3.85, 2.00, 5.42, 2.35, size=14.5, space_after=6)
    text(slide, "Primary finding", 0.72, 3.67, 2.25, 0.30,
         size=13, color=TEAL, bold=True)
    text(slide, "Hybrid NDCG@10 = 0.1315", 0.72, 4.03, 2.70, 0.38,
         size=20, color=TEAL, bold=True)
    add_notes(slide, "Research Question and Contributions", "0:30–2:00 (90 sec)",
              "The prediction task is to recommend ten channels that are new to the viewer. "
              "The project makes four contributions. First, it uses a chronological, full-catalog "
              "evaluation that prevents future leakage. Second, it compares strong simple baselines "
              "with personalized neighborhood and latent-factor methods. Third, it studies diversity, "
              "cold-start, subgroups, time shifts, and scale rather than reporting one number. Finally, "
              "it diagnoses the weak BPR result instead of treating it as an unexplained failure.")

    # 3 — Dataset and EDA
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Dataset and Exploratory Analysis",
               "The interaction matrix is highly sparse, long-tailed, and dominated by implicit signals.",
               3, seal)
    picture_fit(slide, ROOT / "outputs/figures/channel_long_tail.png",
                0.45, 1.46, 5.55, 3.55)
    add_metric_line(slide, 6.30, 1.65, "100K", "viewers", TEAL)
    add_metric_line(slide, 7.95, 1.65, "162.6K", "channels", BLUE)
    add_metric_line(slide, 6.30, 2.70, "3.05M", "interactions", GREEN)
    add_metric_line(slide, 7.95, 2.70, "43", "relative days", ORANGE)
    text(slide, "Key observations", 6.22, 3.80, 2.5, 0.30,
         size=14.5, color=NAVY, bold=True)
    bullets(slide, [
        "No ratings or content metadata",
        "Average of only 30.5 interactions per viewer",
        "~12% of novel test positives are catalog-cold",
    ], 6.20, 4.12, 3.10, 0.90, size=12.5, space_after=3)
    add_notes(slide, "Dataset and Exploratory Analysis", "2:00–3:30 (90 sec)",
              "The public UCSD Twitch subset contains one hundred thousand users, over one "
              "hundred sixty-two thousand channels, and about three million interactions across "
              "forty-three relative days. There are no ratings, categories, or text features. "
              "The popularity curve spans several orders of magnitude even on log scales, so "
              "the catalog is strongly long-tailed. With only about thirty interactions per user, "
              "latent representations for tail channels are difficult to estimate. About twelve "
              "percent of novel test positives are absent from the fit catalog entirely.")

    # 4 — Task and protocol
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Prediction Task and Evaluation Protocol",
               "Model selection is chronological; the test set is used exactly once.", 4, seal)
    stages = [
        (0.60, "History", "Binary views\ndays 0–29"),
        (2.55, "Validation", "Select settings\ndays 30–35"),
        (4.55, "Refit", "Train + validation\nthrough day 35"),
        (6.62, "Rank", "Full fit catalog\nexclude seen items"),
        (8.43, "Test", "Novel positives\ndays 36–42"),
    ]
    for i, (x, heading, body) in enumerate(stages):
        rect(slide, x, 1.80, 1.28, 0.48, NAVY)
        text(slide, heading, x, 1.91, 1.28, 0.25, size=13, color=WHITE,
             bold=True, align=PP_ALIGN.CENTER)
        text(slide, body, x - 0.06, 2.50, 1.40, 0.65, size=12.5, color=GRAY,
             align=PP_ALIGN.CENTER)
        if i < len(stages) - 1:
            add_process_arrow(slide, x + 1.42, 1.91)
    rect(slide, 0.72, 3.55, 8.62, 0.035, GRID)
    text(slide, "Validity checks", 0.72, 3.82, 1.65, 0.28,
         size=14.5, color=NAVY, bold=True)
    bullets(slide, [
        "Mappings, popularity statistics, similarities, and embeddings use fit-period data only",
        "53,212 eligible users and 104,818 user-day cases in the primary held-out test",
        "10,000 user-clustered paired bootstrap draws with Holm correction",
    ], 2.35, 3.75, 6.95, 1.05, size=13, space_after=3)
    add_notes(slide, "Prediction Task and Evaluation Protocol", "3:30–5:00 (90 sec)",
              "The first thirty days fit candidate models, the next six select hyperparameters, "
              "and the final seven form the held-out test. After selection, the models are refit "
              "through day thirty-five. Each user is ranked against the full fit catalog after "
              "removing channels already watched. Every mapping and statistic uses only past data. "
              "Because users contribute multiple daily cases, the paired bootstrap resamples users "
              "and keeps all cases belonging to each sampled user.")

    # 5 — Models
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Models",
               "The comparison isolates global popularity, local co-view structure, and latent preference.",
               5, seal)
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
    add_notes(slide, "Models", "5:00–6:45 (105 sec)",
              "Popularity and recent popularity establish whether personalization is useful. "
              "ItemKNN uses cosine similarity between channels based on shared viewers, directly "
              "retaining local co-view relationships. BPR learns user and item factors with a "
              "pairwise objective. Because the two personalized models make different errors, the "
              "hybrid standardizes their candidate score distributions per user and combines them. "
              "A popularity penalty was also evaluated as a diversity control.")

    # 6 — Implementation and tuning
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Implementation and Hyperparameter Selection",
               "Sparse computation avoids materializing the 162K × 162K item-similarity matrix.",
               6, seal)
    picture_fit(slide, ROOT / "outputs/assignment2/figures/hybrid_ablation.png",
                0.42, 1.42, 5.90, 3.67)
    text(slide, "Selected configuration", 6.50, 1.62, 2.60, 0.30,
         size=15.5, color=NAVY, bold=True)
    add_flat_table(slide, [
        ["Component", "Selected setting"],
        ["ItemKNN", "200 neighbors"],
        ["BPR", "64 factors; lr 0.03"],
        ["BPR", "reg 0.0025; 20 epochs"],
        ["Hybrid", "α = 0.75; λ = 0"],
    ], 6.25, 2.05, [1.25, 2.40], row_h=0.46, font_size=11.5)
    text(slide, "Engineering", 6.50, 4.46, 1.2, 0.26,
         size=13.5, color=TEAL, bold=True)
    text(slide,
         "Sparse block multiplication; retain only top-200 neighbors per item; "
         "YAML-recorded search space and seed 258.",
         7.62, 4.42, 1.77, 0.65, size=11.5, color=GRAY)
    add_notes(slide, "Implementation and Hyperparameter Selection", "6:45–8:05 (80 sec)",
              "ItemKNN is computed with sparse block multiplication and only the top two hundred "
              "neighbors per channel are retained, so the dense item-item matrix is never created. "
              "Validation compares three neighborhood sizes, eight BPR configurations, and twenty "
              "hybrid settings. The selected hybrid uses alpha point seven five and no popularity "
              "penalty. The sharp drop at alpha one is BPR alone, illustrating that BPR is much weaker "
              "than the mixed model. Test performance is not used for any of these choices.")

    # 7 — Metrics
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Evaluation Metrics",
               "Ranking accuracy and recommendation breadth answer different scientific questions.",
               7, seal)
    add_metric_line(slide, 0.80, 1.70, "Recall@10", "fraction of novel positives retrieved", TEAL)
    add_metric_line(slide, 3.00, 1.70, "NDCG@10", "rank-discounted accuracy (primary)", BLUE)
    add_metric_line(slide, 5.28, 1.70, "Hit Rate", "cases with at least one hit", GREEN)
    add_metric_line(slide, 7.45, 1.70, "Coverage", "fit catalog exposed at least once", ORANGE)
    rect(slide, 0.72, 2.86, 8.62, 0.035, GRID)
    add_flat_table(slide, [
        ["Metric", "Interpretation", "Why it matters"],
        ["Novelty", "Self-information of recommended channels", "Penalizes only-head recommendations"],
        ["Long-tail exposure", "Fraction of recommendations in the tail", "Measures creator-side breadth"],
        ["Candidate coverage", "Novel positives present in fit catalog", "Separates ranking from item cold-start"],
    ], 0.92, 3.28, [2.05, 3.20, 3.10], row_h=0.48, font_size=11.5)
    text(slide, "Model selection uses validation NDCG@10; all other metrics are diagnostic.",
         1.18, 4.95, 7.65, 0.26, size=12.5, color=TEAL, bold=True,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Evaluation Metrics", "8:05–9:25 (80 sec)",
              "Recall measures how many future discoveries are recovered. NDCG additionally rewards "
              "placing correct channels earlier and is the primary validation metric. Hit rate asks "
              "whether a case has at least one success. Coverage asks how much of the catalog is ever "
              "shown, which is not the same as correctness. Novelty and long-tail exposure measure "
              "concentration, while candidate coverage identifies answers that no collaborative model "
              "could retrieve because the channel was absent during fitting.")

    # 8 — Main results
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Main Test Results",
               "Hybrid improves ranking accuracy, while ItemKNN retains broader catalog exposure.",
               8, seal)
    picture_fit(slide, ROOT / "outputs/figures/test_accuracy.png",
                0.30, 1.34, 6.05, 3.84)
    add_flat_table(slide, [
        ["Model", "NDCG@10", "Recall@10", "Coverage"],
        ["Hybrid", "0.13148", "0.22342", "26.36%"],
        ["ItemKNN", "0.12584", "0.21437", "36.71%"],
        ["Count ItemKNN", "0.11694", "0.19862", "40.50%"],
        ["BPR", "0.05420", "0.09328", "0.62%"],
        ["Recent popularity", "0.03779", "0.06195", "0.02%"],
    ], 6.28, 1.53, [1.30, 0.78, 0.78, 0.78], row_h=0.46, font_size=9.7)
    text(slide, "+4.48% NDCG vs. ItemKNN", 6.53, 4.50, 2.70, 0.28,
         size=15, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    text(slide, "but 10.35 percentage points less catalog coverage",
         6.38, 4.82, 3.05, 0.25, size=11.5, color=GRAY,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Main Test Results", "9:25–11:25 (120 sec)",
              "Hybrid is the most accurate model with NDCG point one three one five and recall point "
              "two two three four. ItemKNN is the strongest single model. All personalized methods "
              "beat popularity, establishing that viewer history contains predictive signal. The hybrid "
              "gain over ItemKNN is four point four eight percent in NDCG, but coverage falls from about "
              "thirty-seven to twenty-six percent. Count-weighted ItemKNN is less accurate yet exposes the "
              "largest share of the catalog. Thus the hybrid is best for ranking accuracy, but not for every "
              "diversity objective.")

    # 9 — BPR and hybrid
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Why BPR Underperforms—and Still Helps",
               "The latent model is mismatched to the data, yet it retrieves positives missed by ItemKNN.",
               9, seal)
    text(slide, "Observed mismatch", 0.72, 1.55, 2.25, 0.28,
         size=15, color=NAVY, bold=True)
    bullets(slide, [
        "Tail channels have insufficient data for stable item factors",
        "Non-interaction conflates dislike with channel unavailability",
        "One uniform negative per positive is usually too easy",
        "Pairwise training is not identical to unseen-channel Top-10 ranking",
    ], 0.72, 1.95, 4.18, 2.32, size=13.3, space_after=5)
    rect(slide, 5.10, 1.48, 0.035, 3.25, GRID)
    text(slide, "Complementarity", 5.48, 1.55, 1.90, 0.28,
         size=15, color=NAVY, bold=True)
    add_metric_line(slide, 5.42, 2.02, "22,559", "ItemKNN-only hits", BLUE)
    add_metric_line(slide, 7.10, 2.02, "5,540", "BPR-only hits", ORANGE)
    add_metric_line(slide, 5.42, 3.12, "7,648", "hits by both", GREEN)
    text(slide, "Hybrid − ItemKNN NDCG", 7.02, 3.20, 2.0, 0.24,
         size=12, color=GRAY, align=PP_ALIGN.CENTER)
    text(slide, "+0.005638", 7.02, 3.50, 2.0, 0.33,
         size=21, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    text(slide, "95% CI [0.005201, 0.006088] · Holm p = 0.0024",
         5.50, 4.46, 3.60, 0.24, size=10.5, color=MID,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Why BPR Underperforms—and Still Helps", "11:25–13:25 (120 sec)",
              "BPR is disadvantaged by the long tail because many item factors receive little data. "
              "A missing interaction is also a noisy negative on a live platform, and one uniformly "
              "sampled negative per positive is typically trivial. Finally, random pairwise training "
              "does not exactly match unseen-channel top-ten ranking. Five independent seeds remain "
              "far below ItemKNN, so this is not an unlucky initialization. Nevertheless, BPR uniquely "
              "retrieves more than five thousand positives. That complementary signal yields a modest "
              "hybrid gain whose user-clustered confidence interval excludes zero after correction.")

    # 10 — Ablations and subgroups
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Feature Ablation and Subgroup Behavior",
               "Discovery is hardest for long-history users and long-tail target channels.", 10, seal)
    picture_fit(slide, ROOT / "outputs/assignment2/figures/feature_representation.png",
                0.45, 1.40, 4.30, 2.55)
    picture_fit(slide, ROOT / "outputs/assignment2/figures/channel_popularity_subgroups.png",
                4.95, 1.40, 4.55, 2.55)
    rect(slide, 0.68, 4.25, 8.70, 0.035, GRID)
    text(slide, "Binary vs. count", 0.72, 4.48, 1.55, 0.25,
         size=13, color=NAVY, bold=True)
    text(slide, "NDCG 0.12584 vs. 0.11694", 2.05, 4.48, 2.35, 0.25,
         size=12.5, color=TEAL, bold=True)
    text(slide, "Viewer history", 4.60, 4.48, 1.35, 0.25,
         size=13, color=NAVY, bold=True)
    text(slide, "1–6 channels: 0.16794 NDCG · 25+: 0.09012",
         5.90, 4.48, 3.45, 0.25, size=11.5, color=TEAL, bold=True,
         align=PP_ALIGN.RIGHT)
    add_notes(slide, "Feature Ablation and Subgroup Behavior", "13:25–15:10 (105 sec)",
              "Binary ItemKNN outperforms count weighting for new-channel discovery, indicating that "
              "the set of distinct channels matters more than repeatedly amplifying familiar channels. "
              "The subgroup analysis reveals a larger limitation. Recall is only about point zero three "
              "three for targets in the least-popular quartile, compared with over point four for the "
              "most-popular quartile. NDCG also declines as viewer history grows, likely because easy "
              "similar channels have already been consumed. Zero-history viewers require a popularity fallback.")

    # 11 — Robustness and scale
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Temporal Robustness and Scalability",
               "Model ordering is stable, but additional data does not improve every method.", 11, seal)
    picture_fit(slide, ROOT / "outputs/assignment2/figures/rolling_backtest.png",
                0.38, 1.34, 4.60, 3.55)
    picture_fit(slide, ROOT / "outputs/assignment2/figures/scalability_ndcg.png",
                5.00, 1.34, 4.62, 3.55)
    text(slide, "Early → late: absolute NDCG declines; ordering remains unchanged",
         0.48, 4.87, 4.35, 0.22, size=10.5, color=GRAY,
         align=PP_ALIGN.CENTER)
    text(slide, "100K → 1M: Hybrid and ItemKNN stable; BPR declines",
         5.18, 4.87, 4.20, 0.22, size=10.5, color=GRAY,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Temporal Robustness and Scalability", "15:10–16:40 (90 sec)",
              "Rolling-origin evaluation shows that absolute performance declines in later windows, "
              "but the ordering remains Hybrid, ItemKNN, BPR, then popularity. Matched-protocol scale "
              "runs at one hundred thousand, two hundred thousand, five hundred thousand, and one million "
              "users also preserve the ordering. Hybrid and ItemKNN remain stable, whereas BPR declines as "
              "the item catalog expands. Because cohorts and catalogs are not nested, these results establish "
              "engineering scalability and robustness, not a causal learning curve for training size.")

    # 12 — Related work
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Relation to Prior Work",
               "The same Twitch data supports a different question when repeat viewing and live availability are modeled.",
               12, seal)
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
    add_notes(slide, "Relation to Prior Work", "16:40–17:55 (75 sec)",
              "LiveRec uses the same underlying Twitch data, but its target is currently available "
              "live content and repeat behavior. This project isolates discovery of never-watched channels "
              "and only has a seven-day activity proxy, so numerical results should not be compared directly. "
              "The key lesson borrowed from LiveRec is that exact availability matters. BPR provides the "
              "pairwise ranking foundation, while LightGCN is a relevant graph extension for future work.")

    # 13 — Limitations and future work
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Limitations and Future Work",
               "The dominant open problems are candidate generation, live availability, and objective alignment.",
               13, seal)
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
    add_notes(slide, "Limitations and Future Work", "17:55–19:10 (75 sec)",
              "The main limitations are not only model capacity. Catalog-cold channels cannot be ranked "
              "without content or creator features. Missing exact live status makes negative feedback noisy. "
              "Uniform BPR negatives are usually easy and should be replaced with hard or popularity-aware "
              "sampling. Offline NDCG cannot establish viewer satisfaction or creator impact, so an online "
              "test should measure watch time, retention, and exposure. Finally, the accuracy-diversity "
              "tradeoff motivates a two-stage reranker rather than optimizing only NDCG.")

    # 14 — Conclusion
    slide = prs.slides.add_slide(blank)
    add_header(slide, "Conclusions", "Model inductive bias matters more than complexity alone.", 14, seal)
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
         "Takeaway: recommendation quality depends on aligning the data, target, and learning objective.",
         1.02, 5.02, 7.96, 0.24, size=13.5, color=NAVY, bold=True,
         align=PP_ALIGN.CENTER)
    add_notes(slide, "Conclusions", "19:10–20:00 (50 sec)",
              "Personalization strongly outperforms popularity. ItemKNN is the strongest individual model "
              "because local co-view structure matches this sparse discovery task. The hybrid produces a "
              "statistically supported accuracy gain, but reduces catalog coverage, so it is not universally "
              "best. Scaling adds interactions but also expands the long tail, and BPR does not improve "
              "automatically. The central conclusion is that recommendation quality depends on aligning the "
              "data, prediction target, and training objective. Thank you.")

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
