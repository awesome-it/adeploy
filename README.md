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
/repo/namespaces/<namespace>/<release>.yml
```

Or if you have a repo with multiple deployments, you can have a separate namespace folder i.e:

```
/repo/namespaces/<namespace>/<deployment_name>/<release>.yml
```

## Defaults

You can specify defaults (for all deployment configurations) in a separate defaults file or directory i.e. if you
want to specify image tags and versions for all deployments. The defaults will be overwritten from the appropriate 
deployment configurations.

Defaults can be specified in a single `defaults.yml` file:

```shell script
/repo/default.yml
```

Or if you have multiple deployments in a `defaults` folder:

```shell script
/repo/defaults/<deployment_name>.yml
```

## Secrets

Currently there are a few helpers in `common/secrets.py`, which can be used for implicit secret creation e.g:

```jinja2
myjinjatemplate:
  config:
    secretName: {{ create_secret(secret_name, my_key=/pass/path/to/my_secret) }}
    secretKey: my_key
```

By default the secret value is taken from `gopass` password store that must be available when for initial deployment.
If the secret is not attempt to change (i.e. during CI/CD), no password store is required.

You can optionally set `use_pass=False` to use the specified value as follows:

```jinja2
myjinjatemplate:
  config:
    secretName: {{ create_secret(secret_name, use_pass=False, my_key=my_secret_value) }}
    secretKey: my_key
```

The Jinja global function `create_secret()` will create the appropriate secret and return the secret name so it can 
be used in your YAML i.e. Jinja template or deployment configuration.

Additional there is `create_tls_secret()` and `create_docker_registry_secret()` to create the appropriate secret variants.


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