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
$ adeploy -p <provider> (render|config|test|deploy|watch) --help
```

### Example: Helm Chart Deployment

Download an Helm chart and examine k8s resources that will be deployed before you apply them to k8s:

![adeploy-jinja-001.svg](https://awesome-it.de/wp-content/uploads/2020/09/adeploy-helm-001.svg)

### Render
Render manifests (to a "build" dir). This calls the renderer (i.e. Jinja, Helm, Kustomize, ...)
```bash
$ adeploy -p <provider> [-b ./build] render <args> src_dir [src_dir ...]
```
For example:
```bash
$ adeploy -p jinja render ../deployments/alertmanager
```

### Config
This is for debugging and testing purpose. You can print out the rendered namespace configurations i.e. variables that
can be used in Jinja for your deployments as follows:

```bash
$ adeploy -p <provider> config . [--out /path/to/output.json]
{
  <release>: <config>,
  <release>: <config>,
  ...
}
```

The rendered manifest (or similar depending on the provider) files is stored to `./build/<name>`.

### Test
Runs a dry run using the appropriate provider (requires a valid k8s config):
```bash
$ adeploy -p <provider> test src_dir [src_dir ...]
```

### Deploy
Deploy the manifests to the active cluster
```bash
$ adeploy -p <provider> deploy src_dir [src_dir ...]
```

### Watch
Watches a project for changes and render, test or deploy on change detection. 
```bash
$ adeploy -p <provider> watch 
```
## Providers

The following providers are currently supported. Check the sub-pages for details:

* Jinja: [README.md](adeploy/providers/jinja/README.md)
* Helm v3: [README.md](adeploy/providers/helm/README.md)

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
  version: 0.7
```

### Target cluster

A target cluster can be specified in the deployment configuration as follows:

```shell script
_adeploy:
  target_cluster_apiserver_url: <apiserver url>
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

### How do you create a k8s secret from sensitive information via CI/CD?
 
Short answer: You don't. Use implicit secret creation:

The secrets are created in the initial deployment process which is done by hand in most cases. So the person that creates
the deployment (and thus is likely to have access to the sensitive information) can use `gopass` or another password tool
to retrieve this information and put it into secrets. All consecutive deployments (i.e. executed by CI/CD) don't need to
re-create the secret and thus don't need access to the sensitive information. To manually re-create the secrets, 
you must specify `adeploy --recreate-secret`. If a CI/CD needs a secret that is not yet created, it will fail as long as
the CI/CD does not have access to the password tool which is a recommended limitation. 

### Jinja Secret Functions

There are the following Jinja functions in `common/secrets.py`. These Jinja global functions will create the appropriate 
secret and return the secret name so it can be used in your YAML i.e. Jinja template or deployment configuration (so this 
is also useful for Helm templates).

#### `create_secret(name: str = None, use_pass: bool = True, custom_cmd: bool = False, with_key: bool = False, data: dict = None, **kwargs)`

Examples:

```jinja2
env:
    - name: S3_SECRET_KEY
      valueFrom:
        secretKeyRef: 
          name: {{ create_secret(my_key='/pass/path/to/my_secret', name='optional_secret_name') }}
          key: my_key
```

Or using `as_ref = True`:

```jinja2
env:
    - name: S3_SECRET_KEY
      valueFrom:
        secretKeyRef: {{ create_secret(as_ref=True, my_key='/pass/path/to/my_secret', name='optional_secret_name') }}
```

Note you can also specify the args as `data` to support arbitrary secret keys:

```jinja2
my_deployment:
  config:
    secretName: {{ create_secret(data={'a_secret_file.dat': '/pass/path/to/my_secret'}) }}
```

#### `create_docker_registry_secret(server: str, username: str, password: str, email: str = None, name: str = None, use_pass: bool = True, custom_cmd: bool = False)`

Example:
```jinja2
  template:
    spec:
      imagePullSecrets:
        - name: {{ create_docker_registry_secret(
                    server='registry.awesome-it.de',
                    username='my_username',
                    password='/pass/path/to/my_secret') }}
```

#### `create_tls_secret(cert: str, key: str, name: str = None, use_pass: bool = True, custom_cmd: bool = False)`

Example:
```jinja2
my_deployment:
  config:
    tlsSecretName: {{ create_tls_secret(cert='/pass/path/to/my_cert.crt', key='/pass/path/to/my_cert.key') }}
```

### Password Tools

#### Direct Method

To specify a secret value without retrieving the data from `gopass` or another tool, you can skip this by 
passing `use_pass=False` as follows:

```jinja2
myjinjatemplate:
  config:
    secretName: {{ create_secret(secret_name, use_pass=False, my_key=my_secret_value) }}
    secretKey: my_key
```

#### Gopass

By default the secret value is taken from `gopass` password store using the specified path in the `create_secret()`
functions. A list of different repos can be specified by `--gopass-repo` or as comma separated list in the env variable 
`ADEPLOY_GOPASS_REPOS`. So if you set `ADEPLOY_GOPASS_REPOS=a,b`, `create_secret(key='/my/path')`, the following 
secret locations are tried:

- `/my/path`
- `a/my/path` 
- `b/my/path`

The first location containing a valid secret is taken. See `gopass --help` for more details.

#### Custom Password Command

If you don't use `gopass`, you can set `custom_cmd=True` and specify a custom command to retrieve the password data 
as follows:

```jinja2
my_deployment:
  config:
    secretName: {{ create_secret(
                    custom_cmd=True, 
                    my_key='my-custom-tool --arg1=$SOME_ENV_VARS my_password', 
                    secret_name='optional_secret_name') }}
    secretKey: my_key
```

The stdout of the custom command is used as secret value.

Note that the command string is used to create a unique secret name. So if you are using the same command to create secrets
i.e. using a random-password script for auto-rotation secret generation, you should make sure to add a unique expression
to the command.

Note that you can use environment variables (i.e. `$SOME_ENV_VARS`) in your command which are taken from the executing
shells environment.

## Writing Docs

In order to create the docs, you need to install `mkdocs-material` and dependencies as follows:

```bash
pipx install mkdocs-material
pipx inject mkdocs-material mkdocs-asciinema
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

## Read More

* https://awesome-it.de/2020/09/11/adeploy-an-universal-deployment-tool-for-kubernetes/