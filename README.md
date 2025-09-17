# TED Open data Notebooks


## Available notebooks

- [Display number of notices for certain day](https://docs.ted.europa.eu/ted-open-data-notebooks/apps/01-cellar-daily.html)

- [Cellar upload activity](https://docs.ted.europa.eu/ted-open-data-notebooks/apps/02-cellar-period.html)

- [Competition notices](https://docs.ted.europa.eu/ted-open-data-notebooks/apps/03-competition-notices-daily.html)

## 🚀 Usage

1. Add your marimo files to the `notebooks/` or `apps/` directory
   1. `notebooks/` notebooks are exported with `--mode edit`
   2. `apps/` notebooks are exported with `--mode run`

## Including data or assets

To include data or assets in your notebooks, add them to the `public/` directory.

For example, the `apps/charts.py` notebook loads an image asset from the `public/` directory.


## 🎨 Templates

This repository includes a template for the generated site:

1. `index.html.j2` (default): A template with styling and a footer

To use a specific template, pass the `--template` parameter to the build script:

```bash
uv run .github/scripts/build.py --template templates/index.html.j2
```

You can also create your own custom templates. See the [templates/README.md](templates/README.md) for more information.

## 🧪 Testing

To test the export process, run `.github/scripts/build.py` from the root directory.

```bash
uv run .github/scripts/build.py
```

This will export all notebooks in a folder called `_site/` in the root directory. Then to serve the site, run:

```bash
python -m http.server -d _site
```

This will serve the site at `http://localhost:8000`.
