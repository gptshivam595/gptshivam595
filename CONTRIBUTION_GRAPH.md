# Contribution heatmap

The repository includes one GitHub-compatible static SVG contribution preview embedded directly in `README.md`, plus the interactive React view in the standalone app. The data generator fetches public contribution counts for `gptshivam595`, validates the calendar, writes the shared `public/contributions.json` data source, calculates the summary metrics, and refreshes `assets/contribution-preview.svg`.

The README preview is intentionally self-contained and static because GitHub does not execute JavaScript or React in profile Markdown. Run `python scripts/fetch_contributions.py` to refresh the preview and interactive app data. The React app uses the supplied `ContributionSkyline` component as one shared canvas scene for the animated 2D/3D toggle, isometric columns, orbiting, tooltips, keyboard navigation, and shared real data. No GitHub Pages deployment or README redirect is required.
