# Deployment Provider: Jinja

## Structure

```
/mydeployment/

/mydeployment/templates
/mydeployment/templates/service.yml
/mydeployment/templates/deployment.yml

/mydeployment/namespaces
/mydeployment/namespaces/mynamespace/prod.yml
/mydeployment/namespaces/mynamespace/test.yml

/defaults.yml
```

* A jinja deployment consists of a `templates` folder containing the manifest Jinja templates, 
* a `default.yml` file i.e. containing versions and
* a `namespaces` directory containing [deployment configuration for different namespaces and releases](../../README.md#Deployment Configurations).

## Templates

Jina templates in the `templates` folder will be compiled for each namespace and deployment-release. 
The following variables are available for the Jinja templates:

* `name`: The deployment name derived from the repo folder name or specified by `--name`
* `release`: Release name derived from file `namespaces/mynamespace/<release>.yml`
* `namespace`: The namespace for the deployment derived from folder `namespaces/<namespace>/...`
* `deployment`: Variables from `defaults.yml` overwritten by `namespaces/mynamespace/prod.yml`

Legacy variables (do not use them in a new deployment):

* `node_selector`: Derived from `deployment.node`
* `default_version`: Derived from `deployment.versions` (i.e. `versions` in `default.yml`)

## Global Functions

There are a various number of global helper functions that can be used within a Jinja template.

See [adeploy/common/jinja/globals.py](adeploy/common/jinja/globals.py) for a complete reference.

#### `get_version(package: str) / version(package: str)`

Return a package version from `defaults.yml` or from the deployment config. 

Example `defaults.yml`:
```yaml
versions:
    matomo: 3.14.0 # https://hub.docker.com/r/crazymax/matomo/tags/
```

Now you can use the following in your deployments:

```yaml
- name: main
  image: crazymax/matomo:{{ version('matomo') }}
  ports:
```

#### `uuid()`

Generates a random UUID. This is useful i.e. to create a one-shot-container:

Examples:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ name }}-{{ release }}-provisioning-{{ uuid() }}
  namespace: {{ namespace }}
  labels:
    {{ labels.my_oneshot_container }}
```

If you hit the 64 characters limit for API objects, you can fallback to a short uuid:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ name }}-{{ release }}-provisioning-{{ uuid(short=True) }}
  namespace: {{ namespace }}
  labels:
    {{ labels.my_oneshot_container }}
```

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

```jinja2
my_deployment:
  config:
    secretName: {{ create_secret(data={'a_secret_file.dat': '/pass/path/to/my_secret'}) }}
```

See [README.md](adeploy/README.md) for more details.

#### `create_tls_secret(cert_data: str, key_data: str, name = None: str, use_pass: bool = True, custom_cmd: bool = False)`

Example:
```jinja2
my_deployment:
  config:
    tlsSecretName: {{ create_tls_secret(cert_data='/pass/path/to/my_cert.crt', key_data='/pass/path/to/my_cert.key') }}
```

See [README.md](adeploy/README.md) for more details.

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

See [README.md](adeploy/README.md) for more details.
                                      
#### `include_file(path: str, direct: bool = False, render: bool = True, indent: int = 4)`

Example:
```jinja2
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ name }}-{{ release }}-config
  namespace: {{ namespace }}
  labels:
    {{ create_labels(component='config') }}
data:
  entrypoint-common.sh: {{ include_file('files/entrypoint-common.sh') }}
  entrypoint-cronjob.sh: {{ include_file('files/entrypoint-cronjob.sh') }}
```

#### `create_labels(name: str = None, instance: str = default_instance, version: str = None, component: str = None, part_of: str = default_part_of, managed_by: str = 'adeploy', labels: dict = None, **kwargs)`

Create recommended default labels following [best practice](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/). 

Example:
```jinja2
apiVersion: v1
kind: Service
metadata:
  name: {{ name }}-{{ release }}-matomo
  namespace: {{ namespace }}
  labels:
    # Overwrite default labels with "more_labels" and add the label "name: matomo"
    {{ create_labels(name='matomo', labels=more_labels) }}
spec:
  selector:
    # Overwrite default labels with "labels1" and then with "labels2" and add the label "name: matomo"
    {{ create_labels(name='matomo', labels=[labels1, labels2, ...]) }}
  ports:
    - name: http
      port: 80
      targetPort: backend
      protocol: TCP
```

## Global Filters

There are a various number of global Jinja filters that can be used within a Jinja template.

See [adeploy/common/jinja/filters.py](adeploy/common/jinja/filters.py) for a complete reference.

#### `yaml(obj: Union[jinja_dict, dict], flow_style: bool)`

Converts a given `dict` or `adeploy.common.jinja.dict` into YAML code.  

Example:
```yaml
spec:
  tls:
    {{ ingress.get('tls') | yaml(false) | indent(4) }}
```

#### `quote(string: str)`

Quotes a given string.

Example:
```yaml
env:
    {% for k,v in labels.items() %}
    - name: {{ k }}
      value: {{ v | quote }}
    {% %}
```

#### `base64_encode(string: str)`

Encodes the given string into base64. 

Example:
```yaml
env:
    - name: my_var_in_base64
      value: {{ my_var | base64_encode }}        
```

#### `sha256sum(string: str)`

Returns the SHA265 sum for the given string.

Example:
```yaml
annotations:
  checksum/config: |
    {{ include_file("files/configmap.yml") | sha256sum }}
```

#### `basename(path: str)`

Return the basename of a given path.

Example:
```yaml
mypath: {{ '/this/is/my/basename' | basename }}
```

## Macros

You can include macros or Jinja files from 

* the current dir
* the current parent dir
* the directory of the template
* the parent directory of the template.

Example (assuming a `macros.jinja` in `/` or in `/mydeployment/templates/`):

```jinja2
{% from "macros.jinja" import k8s_create_ingress, k8s_get_version with context %}
``` 

## Global Probes Configuration

You can specify a global probes configuration in `default.yml` or in your deployment configuration as follows:

```yaml
_probes:
  liveness:
    initial_delay_seconds: 60
    period_seconds: 30
    timeout_seconds: 5
    failure_threshold: 5
    success_threshold: 1

  readiness:
    initial_delay_seconds: 10
    period_seconds: 5
    timeout_seconds: 5
    failure_threshold: 10
    success_threshold: 1

  custom-deployment-name:
    liveness:
      initial_delay_seconds: 300
``` 

The example above will update all probes in all generated deployments with the given values. The `initialDelaySeconds` of
the `liveness` probe for the deployment `custom-deployment-name` will be additionally set to `300`. 

Note that you can either use snake casing (í.e. `period_seconds`) or camel casing as in the official docs (i.e. `periodSeconds`). 

## Global Labels Configurations

Similar to probes, you can specify a global labels configuration in `default.yml` or in your deployment configuration as follows:

```yaml
_labels:
  app.kubernetes.io/component: matomo
  app.kubernetes.io/instance: {{ name }}-{{ release }}
  app.kubernetes.io/part-of: {{ name }}
```

These labels will be added to all appropriate `metadata`, `matchLabels` and `selector` properties. Please note that
you can use Jinja variables in the labels, too.  

## Global Resources Configurations

Similar to probes and labels, you can also specify resource limits in `default.yml` or in your dpeloyment configuration as follows:

```yaml
_resources:
  # Default resources, can be overwritten by the resources in the manifest (1)
  limits: {}
  requests: {}

  # Resources for a specific object (deployment, statefulset, replicaset, ...), can be overwritten by the resources in the manifest (2)
  my_deployment:
    limits: {}
    requests: {}

  # Resources for a specific container, can't be overwritten by the manifest (3)
  my_deployment:
    my_container:
      limits: {}
      requests: {}
```

**Note that the resources for a specific container (3) will overwrite the resources defined in the manifest.**
