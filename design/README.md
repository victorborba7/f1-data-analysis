# F1 Analytics — Design System

One palette, one type scale, three surfaces. Every colour the portfolio shows —
on the website, in the matplotlib charts, and in Power BI — is defined **once**
in [`tokens.yml`](tokens.yml) and compiled out to each surface. Change a colour
there, run one command, and it propagates everywhere. No more hunting for
`#009382` across thirty files.

```
                       design/tokens.yml          <-- edit colours & type here
                              │
                              │  python design/build_tokens.py
                              ▼
        ┌─────────────────────────────────────────────────┐
        │                design/generated/                 │
        ├──────────────┬──────────────┬────────────────────┤
        │ _tokens.scss │  tokens.py   │ f1.mplstyle        │  theme.json
        │      │       │  + .mplstyle │                    │     │
        ▼      ▼       ▼              ▼                     ▼
   Quarto website   Python charts (matplotlib)        Power BI report
   (styles.scss)    (utils/f1_helpers.py, season_etl)  (F1Analytics.theme.json)
```

## Rebuild

```bash
python design/build_tokens.py      # or:  make tokens  /  python tasks.py tokens
```

Idempotent — run it any time `tokens.yml` changes. The files under
`generated/` carry a "DO NOT EDIT" banner; they are build output.

## Palette

Brand anchors come from the logo: **teal `#009382`** and **slate `#333A41`**.
Dark theme — teal is the accent, deep slate the surfaces, and the logo slate
itself is the structural border.

| Token group | Token | Hex | Used for |
|---|---|---|---|
| **Brand** | `brand.teal` | `#009382` | primary accent (logo teal) |
|  | `brand.teal_bright` | `#1fc1ac` | links & hover on dark |
|  | `brand.teal_deep` | `#006b5f` | pressed / depth |
| **Surface** | `surface.base` | `#15191d` | page & chart background |
|  | `surface.raised` | `#1e252b` | panels, cards, legends |
|  | `surface.sunken` | `#0f1316` | code blocks, deepest layer |
|  | `surface.border` | `#333a41` | card / panel borders (logo slate) |
|  | `surface.outline` | `#2a3137` | faint full-track chart outline |
| **Text** | `text.primary` | `#e6e9eb` | body text on dark |
|  | `text.muted` | `#9aa3aa` | secondary / benchmark |
|  | `text.faint` | `#6f7880` | axis annotations, corner labels |
|  | `text.on_chart` | `#ffffff` | chart tick & label ink |
| **Axis** | `axis.spine` | `#3a444b` | visible axis spines |
|  | `axis.grid` | `#ffffff` | gridlines (low alpha) |
|  | `axis.marker` | `#4a555c` | corner-marker lines |
|  | `axis.zero` | `#5b666e` | zero / reference lines |
| **Semantic** | `semantic.positive` | `#3fb950` | gain / faster |
|  | `semantic.negative` | `#e5484d` | loss / slower |
|  | `semantic.neutral` | `#9aa3aa` | benchmark / reference |
| **Compound** | `compound.soft` | `#e5484d` | soft tyre |
|  | `compound.medium` | `#ffd700` | medium tyre |
|  | `compound.hard` | `#ebebeb` | hard tyre |
|  | `compound.intermediate` | `#3fb950` | intermediate tyre |
|  | `compound.wet` | `#4a8bdf` | wet tyre |

**Categorical ramp** (`color.data` → `T.DATA_COLORS`, matplotlib colour cycle,
Power BI `dataColors`) — a teal family distinguished by lightness, with one
gold accent: `#009382 · #2bb6a3 · #1f7a8c · #4f9bd0 · #6f7880 · #3fb07a ·
#8aa0c0 · #d6a63f`.

> Driver & constructor colours are **not** tokens — they come straight from
> FastF1 (`get_team_color` / `get_driver_color`), the canonical source for
> team liveries. The design system owns everything *around* the data.

## How each surface consumes it

| Surface | Generated file | Wired up in |
|---|---|---|
| **Website** (Quarto) | `_tokens.scss` | [`styles.scss`](../styles.scss) — `@import "design/generated/tokens"` in the `scss:defaults` layer; sets `$primary`, `$body-bg`, … and the `--f1-*` CSS variables |
| **Charts** (matplotlib) | `tokens.py`, `f1.mplstyle` | [`utils/f1_helpers.py`](../utils/f1_helpers.py) — `from design.generated import tokens as T`; `setup()` applies `plt.style.use(T.MPLSTYLE)` |
| **Power BI** | `theme.json` | [`serve/powerbi/`](../serve/powerbi/) — copied to `F1Analytics.theme.json`; import via *View → Themes → Browse* |

## Editing

1. Change a value in [`tokens.yml`](tokens.yml) (the **only** file you hand-edit).
2. `python design/build_tokens.py`.
3. Website: `quarto preview` picks up `_tokens.scss` automatically.
   Charts: re-run the notebooks (or `setup()`) to re-render with the new theme.
   Power BI: re-import `F1Analytics.theme.json`.

To add a new token, add it under the right group in `tokens.yml` and (if a chart
needs it) reference `T.<GROUP>_<NAME>` — e.g. `axis.spine` → `T.AXIS_SPINE`.
