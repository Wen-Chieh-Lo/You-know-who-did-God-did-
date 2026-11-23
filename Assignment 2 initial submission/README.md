# Assignment 2 Initial Submission

This folder summarizes the required submission files and preparation checklist for **CSE 158 / 258 Assignment 2**.

---

## Initial Submission Files

The initial Gradescope submission requires **two files**:

```text
workbook.html
video_url.txt
```

---

## 1. `workbook.html`

`workbook.html` should be exported from a **Jupyter Notebook**.

### Requirements

- Must be a real HTML export from the notebook.
- Do **not** simply rename `.ipynb` to `.html`.
- It should open directly in a web browser.
- It should be **clean, documented, and readable as-is**.
- Peer graders should **not need to rerun the code** to understand the project.
- Important code cells should already have their outputs visible.
- Figures, tables, plots, metrics, and conclusions should already be displayed.

### Recommended Content

The notebook should contain both **code and results**, with Markdown explanations connecting them.

A good structure is:

1. **Project Introduction / Research Question**
   - What problem are we studying?
   - What is the predictive / recommendation task?

2. **Dataset**
   - Dataset source
   - Number of users, items/channels, interactions
   - Important fields
   - Data quality / preprocessing

3. **Exploratory Data Analysis (EDA)**
   - User activity distribution
   - Channel popularity / long-tail distribution
   - Interaction trends over time
   - New-channel vs. repeat viewing behavior
   - Relevant figures and statistics

4. **Train / Validation / Test Split**
   - Explain the chronological split
   - Explain why random splitting could cause temporal leakage
   - Show the final split used in the project

5. **Models**
   - Popularity baseline
   - Recent popularity
   - ItemKNN / item-item collaborative filtering
   - BPR
   - Hybrid model
   - Any additional models or ablations that are important to the final story

6. **Hyperparameter Selection**
   - Validation settings tested
   - Selected ItemKNN neighbors
   - Selected BPR settings
   - Selected hybrid alpha / other parameters
   - Make clear that test results were not used for model selection

7. **Evaluation Metrics**
   - Recall@10
   - NDCG@10
   - Hit Rate@10
   - Catalog Coverage
   - Novelty
   - Long-tail Exposure
   - Explain why these metrics matter

8. **Main Results**
   - Main comparison table
   - Important figures
   - Best-performing model
   - Baseline comparison

9. **Additional Analysis**
   - Accuracy vs. diversity trade-off
   - Binary vs. count-weighted feedback
   - User-history subgroup analysis
   - Channel-popularity subgroup analysis
   - Temporal robustness
   - Statistical significance / confidence intervals if included

10. **Related Work**
    - Original Twitch dataset / LiveRec paper
    - BPR and other recommender-system methods
    - Explain how our task differs from prior work

11. **Conclusion and Limitations**
    - What worked?
    - What did not work?
    - What did we learn?
    - Cold-start limitations
    - Live-availability limitation
    - Possible future work

### Important

The notebook should not just contain code such as:

```python
display(pd.read_csv(...))
display(Image(...))
```

Each important result should also include a short explanation of:

- What is being shown?
- Why was this experiment performed?
- What does the result mean?
- How does it answer the research question?

The final exported HTML should allow a peer grader to understand the full project without executing anything.

---

## 2. `video_url.txt`

This file should contain **one line only**: the public link to the presentation video.

Example:

```text
https://drive.google.com/file/d/FILE_ID/view?usp=drive_link
```

or:

```text
https://www.youtube.com/watch?v=VIDEO_ID
```

### Presentation Requirements

- Approximately **20 minutes**.
- Camera is **not required**.
- Slides may be used.
- A notebook walkthrough is also acceptable.
- A combination of slides + notebook/code walkthrough is recommended.
- The presentation should match the code, results, and conclusions in `workbook.html`.

### If Using Google Drive

- Upload the video as an `.mp4`.
- Enable **Anyone with the link** sharing.
- Verify that another person can open/download the video without requesting access.
- Put only the final shared link inside `video_url.txt`.

---

## Suggested GitHub Folder Structure

```text
Assignment 2 initial submission/
├── README.md
├── workbook.html
└── video_url.txt
```

The repository may still keep the original notebook, source code, reports, and outputs elsewhere. The files above are simply the final submission package.

For example:

```text
repo/
├── Assignment 2 initial submission/
│   ├── README.md
│   ├── workbook.html
│   └── video_url.txt
│
├── notebooks/
├── src/
├── outputs/
├── reports/
└── README.md
```

---

## Submission Checklist

Before submitting:

- [ ] Final Jupyter Notebook is complete.
- [ ] All important notebook cells have been executed.
- [ ] Tables, plots, metrics, and outputs are visible.
- [ ] Markdown explanations are included throughout the notebook.
- [ ] Notebook has been exported as `workbook.html`.
- [ ] `workbook.html` opens correctly in a browser.
- [ ] Presentation is approximately 20 minutes.
- [ ] Presentation matches the notebook and reported results.
- [ ] Video is uploaded to Google Drive or YouTube.
- [ ] Video link is publicly accessible.
- [ ] `video_url.txt` contains only the final video link.
- [ ] Both `workbook.html` and `video_url.txt` are ready for Gradescope.

---

## After the Initial Submission: Peer Grading

Peer grading happens later and is **not part of the initial submission package**.

The instructor will assign other projects to review after submissions have been collected.

For the peer-grading assignment:

1. Upload an empty file named:

```text
responses.txt
```

2. Gradescope will provide the assigned projects and grading instructions.

3. Complete the peer evaluations.

4. Re-upload the completed:

```text
responses.txt
```

Peer grading is worth **4 marks**.

---

## Current Project Status

For our Twitch New-Channel Recommendation project, the main research and experiments are already largely complete.

Remaining submission-focused work:

- [ ] Turn the current results notebook into a complete, readable Assignment 2 notebook.
- [ ] Export the final notebook as `workbook.html`.
- [ ] Prepare presentation slides / presentation flow.
- [ ] Record the ~20-minute presentation.
- [ ] Upload the video and create `video_url.txt`.
- [ ] Submit the two required files to Gradescope.
