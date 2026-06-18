# Power BI — connecting to the F1 marts

The Power BI report consumes the **same `f1_analytics` star schema** that the
Quarto site does. There are two ways to connect; pick one.

> **Why no `.pbix` in the repo?** A `.pbix` is an opaque binary that doesn't diff
> or review well in git, and it embeds environment-specific connection state. The
> report is authored in Power BI Desktop from the steps below; this folder holds
> everything needed to rebuild it — the model definition, measures, and layout.

## Option A — live BigQuery (recommended, shows the cloud warehouse)

1. **Get Data → Google BigQuery** (or *BigQuery (Azure AD)* if using SSO).
2. Sign in with a Google account that can read the dataset, or use the service
   account configured for the project.
3. Navigate to **`<your-project>` → `f1_analytics`** and load these tables:
   - Dimensions: `dim_driver`, `dim_constructor`, `dim_circuit`, `dim_race`, `dim_season`, `dim_status`
   - Facts: `fct_race_results`, `fct_qualifying`, `fct_pit_stops`, `fct_driver_standings`, `fct_constructor_standings`
4. Use **Import** mode for snappy visuals (the marts are small), or **DirectQuery**
   if you want to show live cloud querying.

## Option B — local Parquet (no cloud account needed)

Point **Get Data → Folder** (or *Parquet*) at `serve/data/`. This loads the
reporting marts (`mart_driver_career`, `mart_constructor_career`,
`mart_season_summary`) — enough for the headline dashboard pages.

## Modeling (Option A)

In **Model view**, create relationships from each fact's foreign key to the
matching dimension key (single-direction, one-to-many, dimension → fact):

| From (fact) | Column | To (dimension) | Column |
|-------------|--------|----------------|--------|
| `fct_race_results` | `driver_key` | `dim_driver` | `driver_key` |
| `fct_race_results` | `constructor_key` | `dim_constructor` | `constructor_key` |
| `fct_race_results` | `circuit_key` | `dim_circuit` | `circuit_key` |
| `fct_race_results` | `race_key` | `dim_race` | `race_key` |
| `fct_race_results` | `status_key` | `dim_status` | `status_key` |
| `dim_race` | `season_key` | `dim_season` | `season_key` |
| `fct_qualifying` | `driver_key` / `race_key` | `dim_driver` / `dim_race` | … |
| `fct_driver_standings` | `driver_key` / `season_key` | `dim_driver` / `dim_season` | … |

This is a textbook star — single-direction filters flow from dimensions into the
facts. Add the measures from [`measures.dax`](measures.dax) to a dedicated
`_Measures` table.

## Suggested pages

1. **Driver leaderboard** — table (driver, titles, wins, podiums, points) + a
   wins bar chart, sliced by `dim_season[era]`.
2. **Constructor dominance** — stacked area of constructor wins over `season_year`.
3. **Circuit map** — map visual on `dim_circuit[latitude/longitude]`, bubble size
   = races held.
4. **Season explorer** — `dim_season` slicer driving a results matrix.

Drop a screenshot of the finished report at `serve/powerbi/screenshot.png` and it
will appear in the repo README.
