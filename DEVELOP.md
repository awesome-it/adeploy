# adeploy

This doc is for developers.

## Setup for development usage

Get the source code:

```bash
$ git clone https://gitlab.awesome-it.de/tools/adeploy.git ~/path/to/atracker
```
Setup a virtualenv using `Python3` and activate it:

```bash
$ virtualenv -p python3 ~/.virtualenvs/adeploy
$ source ~/.virtualenvs/adeploy/bin/activate
# alternatively install it in your project directory
$ cd ~/path/to/adeploy
$ virtualenv -p python3 env3
$ source env3/bin/activate
(adeploy)$ 
```

Install requirements:

```bash
(adeploy)$ pip install -r requirements.txt
```
#### Usage while developing

There are two ways you can invoke adeploy while developing (i.e. while in your virtualenv).

1. There is a wrapper that can be used to run it from your PATH. This is only intended for quick usage while development,
not as a binary (i.e. don't link to it or anything; have a look at the next topic).
```bash
$ ./runner.py
```

2. The second way is via pip. Pip can install a python package in edit-mode. If you do this all code changes will
immediately take effect. To skip the virtualenv, you can append "--user" to pip in order to install adeploy using the user scheme.
 ```bash
 $ cd ~/path/to/adeploy
 $ pip install [--user] -e .
 $ adeploy
 # make changes
 $ adeploy
 # new behaviour, changes take effect immediately.
````

## Writing Documentation

The docs are build via [MkDocs Material](https://squidfunk.github.io/mkdocs-material/), the markdown files are located in the `docs` subfolder.

In order to create the docs, you need to install `mkdocs-material` and dependencies as follows:

```bash
pipx install mkdocs-material
pipx inject mkdocs-material beautifulsoup4 # Required for hooks/asciinema.py
pipx inject mkdocs-material "mkdocstrings[python]" # Required to read docstrings from python files i.e. filters.py
```

Now you run the `mkdocs` live preview at http://127.0.0.1:8000/ as follows:

```bash
mkdocs serve
```

Or generate static docs as:

```bash
mkdocs build
```

### Terminal records via `asciinema`

Install `asciinema` as follows:

```bash
pipx install asciinema
```

To record you terminal sessions, use the following:

```bash
asciinema rec -c "bash --rcfile ~/.bashrc-asciinema" --rows 10 --cols 75 <output_file>.cast
```

Make sure to set your `PS1` variable to `$ ` in your `~/.bashrc-asciinema`.