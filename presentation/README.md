# Assignment 2 presentation

Files:

- `assignment2_20min_zh_tw.pptx`: 17-slide Traditional-Chinese presentation for an
  approximately 20-minute recording.
- `assignment2_speaker_notes_zh_tw.md`: suggested timing and narration for every
  slide. The same notes are embedded in the PowerPoint speaker-notes area.

The deck explicitly covers all five Assignment 2 rubric sections: predictive task,
dataset/EDA, modeling and code, evaluation/results, and related work. Its results and
claims match `report.md` and the checked-in experiment artifacts.

To rebuild it:

```bash
python -m pip install -e '.[presentation]'
python scripts/build_assignment2_slides.py
```

Before recording, replace or add the group-member names on the title slide if needed.
During slide 9, briefly show the notebook or repository files mentioned on the slide;
this satisfies the assignment's recommendation to combine slides with a code
walkthrough. Keep the recording under roughly 22 minutes.
