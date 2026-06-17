# F1 Data Analysis Portfolio

Weekly race analysis using [FastF1](https://github.com/theOehrly/Fast-F1) — published every Monday after each Formula 1 Grand Prix.

**Stack:** Python · FastF1 · Pandas · Matplotlib · Plotly · Jupyter

---

## Structure

```
├── template/                          ← Copy these each race weekend
│   ├── race_weekend_template.ipynb       Results, lap times, tyres, telemetry
│   ├── weekend_overview_template.ipynb   Quali → Sprint → Race in one run
│   ├── corner_time_loss_template.ipynb   Delta-time, corner by corner
│   └── advanced_analysis_template.ipynb  Race pace, tyre deg, track dominance
├── 2026/
│   ├── Season_Analysis.ipynb          ← Season ETL + championship & teammate battles
│   └── R{round}_{location}/
│       ├── analysis.ipynb
│       └── assets/                    ← Charts exported for LinkedIn
├── data/                              ← Tidy season datasets (CSV / parquet)
├── examples/                          ← Learning notebooks (FastF1 fundamentals)
└── utils/
    ├── f1_helpers.py                  ← Reusable plotting & analysis helpers
    └── season_etl.py                  ← Season ingestion pipeline
```

## Analyses

| Notebook | What it shows | Skill demonstrated |
|----------|---------------|--------------------|
| `race_weekend_template` | Results · lap times · tyre strategy · telemetry | Core EDA & viz |
| `weekend_overview_template` | Qualifying · Sprint · Race combined | Multi-source joins |
| `corner_time_loss_template` | Delta-time analysis, corner by corner | Signal processing |
| `advanced_analysis_template` | Race pace box · tyre degradation regression · track dominance map | Statistical modeling |
| `Season_Analysis` | ETL pipeline → standings → teammate battles | **Data engineering** |

## 2026 Season

| Round | Grand Prix | Analyses |
|-------|-----------|----------|
| 9 | Barcelona | [Ferrari Setup Difference](2026/Barcelona/NB01_Ferrari_Setup_Difference.ipynb) |

## Weekly Workflow

1. Race finishes on Sunday
2. Copy `template/` → `2026/R{n}_{city}/`
3. Set `YEAR`, `GRAND_PRIX`, `SESSION` at the top of the notebook
4. Run all cells — charts auto-saved to `assets/`
5. Write LinkedIn post using the draft generator in the last cell
6. `git commit` and `git push`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Website

The polished writeups are published with [Quarto](https://quarto.org) to GitHub Pages.

- **Blog posts** live in `posts/`, config in `_quarto.yml`, theme in `styles.css`
- A GitHub Action (`.github/workflows/publish.yml`) renders and deploys on every push
- Local preview: install Quarto, then `quarto preview`

**First-time GitHub Pages setup:**
1. Push this project to the GitHub repo
2. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**
3. (Optional) Replace the `YOUR_PROFILE` LinkedIn placeholder in `_quarto.yml` and `about.qmd`
4. Push — the Action publishes to `https://victorborba7.github.io/f1-data-analysis`

---

Follow my weekly analysis on [LinkedIn](https://www.linkedin.com/in/YOUR_PROFILE)
