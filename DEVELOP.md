# adeploy

This doc is for developers.

## Setup for development usage

Get the source code:

```bash
$ git clone https://gitlab.awesome-it.de/tools/adeploy.git ~/path/to/atracker
```

`uv` supports editable installations. There is no need to create a `.venv` manually:

```bash
$ uv sync --frozen
$ uv run adeploy
```

## Writing Documentation

The docs are build via [MkDocs Material](https://squidfunk.github.io/mkdocs-material/), the markdown files are located in the `docs` subfolder.

In order to create the docs, you need to install `mkdocs-material` and dependencies as follows:

```bash
uv sync --extra dev --frozen
```

Now you run the `mkdocs` live preview at http://127.0.0.1:8000/ as follows:

```bash
uv run mkdocs serve
```

Or generate static docs as:

```bash
uv run mkdocs build
```

### Terminal records via `asciinema`

Install `asciinema` as follows:

```bash
uvx asciinema
```

To record you terminal sessions, use the following:

```bash
uvx asciinema rec -c "bash --rcfile ~/.bashrc-asciinema" --rows 10 --cols 75 <output_file>.cast
```

Make sure to set your `PS1` variable to `$ ` in your `~/.bashrc-asciinema`.