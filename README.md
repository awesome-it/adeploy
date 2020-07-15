# adeploy
An universal deployment tool for k8s deployments.

## Install

```shell script
$ pip install [--user] git+ssh://git@git.local.awesome-it.de/awesome/tools/adeploy.git 
```

## Usage

Check the help section of `adeploy`:
```bash
$ adeploy --help
$ adeploy -p <provider> (render|test|deploy) --help
```
#### Render
Render manifests (to a "build" dir). This calls the renderer (i.e. Jinja, Helm, Kustomize, ...)
```bash
$ adeploy -p <provider> [-b ./build] render <args> src_dir [src_dir ...]
```
For example:
```bash
$ adeploy -p jinja render ../deployments/alertmanager
```

The rendered manifest (or similar depending on the provider) files is stored to `./build/<name>`.

#### Test
Runs a dry run using the appropriate provider (requires a valid k8s config):
```bash
$ adeploy -p <provider> test src_dir [src_dir ...]
```

#### Deploy
Deploy the manifests to the active cluster
```bash
$ adeploy -p <provider> deploy src_dir [src_dir ...]
```

## Deployment Configurations

A deployment configuration is a file in the appropriate namespace folder with release name as filename:

```
/mydeployment/namespaces/<namespace>/<release>.yml
```

### Alternative Namespace Structure

If you have a repo with multiple deployments, you can have a separate namespace folder i.e:

```
/repo/deployment-1
/repo/deployment-2
/repo/deployment-3
...
/repo/namespaces/<namespace>/deployment-1/<release>.yml
/repo/namespaces/<namespace>/deployment-2/<release>.yml
/repo/namespaces/<namespace>/deployment-3/<release>.yml
```

## Providers

* Jinja: [README.md](adeploy/providers/jinja/README.md)
* Helm v3: [README.md](adeploy/providers/helm/README.md)

## Advanced Setup
### For development usage

Get the source code:

```bash
$ git clone https://gitlab.awesome-it.de/awesome/tools/adeploy.git ~/path/to/@NAME@
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
$ pip install git+https://gitlab.awesome-it.de/awesome/tools/adeploy.git
```