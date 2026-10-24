# Contribution heatmap

The repository includes GitHub-compatible static 2D and isometric 3D SVG contribution previews embedded directly in `README.md`, plus an interactive React view that can be built by a separate host. The data generator fetches public contribution counts for `gptshivam595`, validates the calendar, writes the shared `public/contributions.json` data source, calculates the summary metrics, and refreshes `assets/contribution-preview.svg` and `assets/contribution-skyline-preview.svg`.

The README previews are intentionally self-contained and static so GitHub renders them without JavaScript or React. Run `python scripts/fetch_contributions.py` to refresh both images and the interactive app data. The React app uses the supplied `ContributionSkyline` component for the animated 2D/3D toggle, isometric columns, orbiting, tooltips, keyboard navigation, and shared real data. No GitHub Pages deployment or README redirect is required.
