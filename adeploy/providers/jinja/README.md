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
* a `namespaces` directory containing deployment configuration for different namespaces and releases.

### Deployment Configurations

A deployment configuration is a file in the appropriate namespace folder with release name as filename:

```
/mydeployment/namespaces/<namespace>/<release>.yml
```

#### Alternative Namespace Structure

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