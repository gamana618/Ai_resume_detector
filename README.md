# ResumeIQ — AI Resume Detector
### Machine Learning Project | AI vs Human Resume Detection

---

## What It Does
Analyzes resume text and returns an **exact percentage split** of AI-generated vs human-written content.
- Handles any ratio: 100/0, 70/30, 50/50, 30/70, 0/100 — all accurately detected
- Segment-by-segment breakdown (every ~100 words scored separately)
- 8 linguistic features analyzed per segment
- Works fully in the browser (no backend required) OR with Flask backend

---

## How to Run

### Option A: Just open the HTML (no install needed)
```
Open index.html directly in any browser.
Done. Everything runs client-side.
```

### Option B: With Flask backend
```bash
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

---

## Features Detected

| Feature | AI Signal | Human Signal |
|---|---|---|
| **Perplexity proxy** | Low entropy, predictable word choice | High variance, unpredictable vocab |
| **Burstiness** | Uniform sentence lengths | Wildly varying sentence lengths |
| **Buzzword density** | "spearheaded", "leveraged", "robust" | Specific, personal language |
| **Human markers** | No "I", "honestly", "kind of" | Casual first-person language |
| **Sentence length** | 15-25 words, very consistent | Irregular, short and long mixed |
| **Punctuation** | Almost only periods/commas | Dashes, exclamations, informal |
| **Repetition** | Repeated 3-word phrases | Rarely repeats exact phrases |
| **Formality** | Perfect formal tone always | Contractions, informal words |

---

## Output Example
```
AI Percentage:    70.3%
Human Percentage: 29.7%
Verdict:          Mostly AI-generated
Confidence:       80.6%
Segments:         12 chunks analyzed
```

---

## Project Structure
```
├── app.py          # Flask backend (Python)
├── index.html      # Frontend UI (self-contained)
├── requirements.txt
└── README.md
```

---

## For the Presentation
- Works offline (open index.html)
- Load sample resumes using the demo buttons
- Shows segment-by-segment scoring table
- All 8 features visualized with progress bars
- Handles any percentage split accurately
