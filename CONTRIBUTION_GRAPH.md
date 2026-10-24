# Contribution heatmap

The repository includes a GitHub-compatible SVG contribution heatmap embedded directly in `README.md` and an interactive React view that can be built by a separate host. The data generator fetches public contribution counts for `gptshivam595`, validates the calendar, writes the shared `public/contributions.json` data source, calculates the summary metrics, and refreshes `assets/contribution-preview.svg`.

The README SVG is intentionally self-contained and static so GitHub renders it without JavaScript or React. The React app uses the supplied `ContributionSkyline` component for the animated 2D/3D toggle, isometric columns, orbiting, tooltips, keyboard navigation, and shared real data. No GitHub Pages deployment or README redirect is required.
