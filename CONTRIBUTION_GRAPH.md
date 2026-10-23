# Contribution Skyline (2D + 3D)

This graph is part of the existing profile repository, gptshivam595/gptshivam595. The README includes one generated SVG heatmap preview that links to the interactive GitHub Pages view. The live page toggles between a calendar heatmap and a 3D contribution skyline.

## Data

The workflow reads the public GitHub contribution calendar for gptshivam595, validates that the expected dates and tooltips were parsed, fetches public profile metadata, and creates:
- site/contributions.json for the live graph;
- assets/contribution-preview.svg for the profile README.

If GitHub changes its markup and the parser cannot validate the calendar, the workflow fails instead of publishing a fake or empty graph. No token is needed because only public profile data is used.

## Deployment

The GitHub Actions workflow is configured to deploy the static site to GitHub Pages. In repository Settings → Pages, choose GitHub Actions as the source if it is not already selected. The interactive view will be at https://gptshivam595.github.io/.

The README itself remains GitHub-compatible: it embeds the SVG preview and links to the live graph because README Markdown cannot execute JavaScript or canvas graphics.
