# adeploy
An universal deployment tool for k8s deployments.

## Install

```shell script
$ pip install [--user] git+https://github.com/awesome-it/adeploy
```

## Usage

Check the help section of `adeploy`:
```bash
$ adeploy --help
$ adeploy -p <provider> (render|test|deploy) --help
```

#### Example: Helm Chart Deployment

Dowload an Helm chart and examine k8s resources that will be deployed before you apply them to k8s:

![adeploy-jinja-001.svg](https://awesome-it.de/wp-content/uploads/2020/09/adeploy-helm-001.svg)

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

### Minimum Version

For a deployment, you can set a minimum required adeploy version i.e. in `defaults.yml` as follows:

```shell script
_adeploy:
  version: 0.5
```

## Defaults

You can specify defaults (for all deployment configurations) in a separate defaults file or directory i.e. if you
want to specify image tags and versions for all deployments. The deployment configuration will be merge to this 
defaults. 

Defaults can be specified in a single `defaults.yml` file:

```shell script
/repo/default.yml
```

Or if you have multiple deployments in a `defaults` folder:

```shell script
/repo/defaults/<deployment_name>.yml
```

While your deployment configuration inherits from the defaults file, you can also access specified default variables
in your deployment configuration as follows:

```jinja2
mydeployment:
    image: registry/image:v{{ defaults.get('versions').get('image') }}
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
If the secret is applied another time and it is not attempt to change, the secret creation is skipped and no password store 
is required. This is useful for automated deployment in CI/CD, the secret is only touched during the initial deployment
which is thought to be done by a human beeing.

Note that you can export `ADEPLOY_GOPASS_REPOS` as comma separated a list of `gopass` repo names that are tried in the 
defined order to find the secret. See `--gopass-repo` arg in `adeploy --help` for further help. 

You can skip the `gopass` feature by passing `use_pass=False` as follows:

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

The following providers are currently supported. Check the sub-pages for details:

* Jinja: [README.md](adeploy/providers/jinja/README.md)
* Helm v3: [README.md](adeploy/providers/helm/README.md)

## Read More

* https://awesome-it.de/2020/09/11/adeploy-an-universal-deployment-tool-for-kubernetes/