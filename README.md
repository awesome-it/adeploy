# adeploy
An universal deployment tool for k8s deployments.

## Usage

Check the help section of `adeploy`:
```bash
$ adeploy --help
```

### Common Usage (WIP)

#### Rendering
Render manifests (to a "build" dir). This calls the renderer (i.e. Jinja, Helm, Kustomize*, ...)
```bash
$ adeploy build <build_opts> [--build-dir=./build]
```
(*) Sometimes, there is no need to render i.e. for Kustomize. In this case, it is just copied to the build dir and the
user has the chance to set another abstraction layer on Kustomize deployments i.e. using Jinja or Wildcards etc..

#### Linting
Runs linting on the rendered manifests. This gives the user a chance to hook in and make custom checks i.e. no secrets, 
conventions etc..

```bash
$ adeploy lint <lint_opts> [--build-dir=./build]
```

#### Testing
Runs dry-run or server-dry-run (in case k8s config is given) on the rendered manifests. Additional tests against the 
build dir can be specified by the user.

```bash
$ adeploy test <test_opts> [--build-dir=./build]
```

#### Deploy
Deploy manifests from the build dir to a cluster:
```bash
$ adeploy deploy <deploy_opts>
```

### Using Jinja Renderer
```bash
$ adeploy render --type jinja \
          [--build_dir ./build] \       # Stdout by default
          --template ./templates \         # Directory containing Jinja template files
          --variables ./variables \        # Directory containing Jinja variables as YML files
          --name deployment_name \         # The name of the deployment
          [--var1 value1 ...]              # Additional variables to use in the Jinja templates
... render manifests to ./build
$ adeploy lint --build_dir ./build
$ adeploy test --build_dir ./build
$ adeploy deploy --build_dir ./build
```

## Setup
### For development usage

Get the source code:

```bash
$ git clone https://gitlab.awesome-it.de/tools/adeploy.git ~/path/to/@NAME@
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
`````

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
 ```

### For production usage

For production usage you can just install the package like any other python package. There are two ways to do this:
1. Checkout by hand and install by hand or via pip:
```bash
$ git clone git@git.local.awesome-it.de:tools/adeploy.git
$ cd adeploy
$ python setup.py install
# OR:
$ pip install .
$ adeploy --help
```

2. Install via pip directly from gitlab:
```bash
# beware of the / instead of the : in the URL!
$ pip install git+ssh://git@git.local.awesome-it.de/tools/adeploy.git
# or if you prefer https over ssh
$ pip install git+https://gitlab.awesome-it.de/tools/adeploy.git
```