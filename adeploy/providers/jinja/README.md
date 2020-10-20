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

### Templates

Jina templates in the `templates` folder will be compiled for each namespace and deployment-release. 
The following variables are available for the Jinja templates:

* `name`: The deployment name derived from the repo folder name or specified by `--name`
* `release`: Release name derived from file `namespaces/mynamespace/<release>.yml`
* `namespace`: The namespace for the deployment derived from folder `namespaces/<namespace>/...`
* `deployment`: Variables from `defaults.yml` overwritten by `namespaces/mynamespace/prod.yml`

Legacy variables (do not use them in a new deployment):

* `node_selector`: Derived from `deployment.node`
* `default_version`: Derived from `deployment.versions` (i.e. `versions` in `default.yml`)

#### Global Functions & Filters

There are a various number of global functions and filters that can be used within a Jinja template:

```bash
$ grep "def create__" adeploy/common/jinja/globals.py | sed -s 's/def create__//'
get_version(deployment, **kwargs):
version(deployment, **kwargs):
get_url(deployment, **kwargs):
create_generic_secret(deployment, **create_kwargs):
create_secret(deployment, **kwargs):
create_tls_secret(deployment, **kwargs):
create_docker_registry_secret(deployment, **kwargs):
include_file(deployment, **kwargs):
``` 

See [adeploy/common/jinja/globals.py](adeploy/common/jinja/globals.py) for reference.

```bash
$ grep "def " adeploy/common/jinja/filters.py | sed -s 's/def //'
yaml(obj, flow_style):
quote(string):
base64_encode(string):
sha265sum(string: str):
```

See [adeploy/common/jinja/filters.py](adeploy/common/jinja/filters.py) for reference.

#### Macros

You can include macros or Jinja files from 

* the current dir
* the current parent dir
* the directory of the template
* the parent directory of the template.

Example (assuming a `macros.jinja` in `/` or in `/mydeployment/templates/`):

```jinja2
{% from "macros.jinja" import k8s_create_ingress, k8s_get_version with context %}
``` 

#### Global Probe Configuration

You can specify a global probe configuration in `default.yml` or in your deployment configuration as follows:

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

The example above will update all probes in the generated deployments with the given values. The `initialDelaySeconds` of
the `liveness` probe for the deployment `custom-deployment-name` will be additionally set to `300`. 

Note that you can either use snake casing (í.e. `period_seconds`) or camel casing as in the official docs (i.e. `periodSeconds`). 