# Using `adeploy`

The deploying process to Kubernetes clusters using `adeploy` consist of the following steps:

1. **Render** your Jinja or Helm templates and generate vanilla YAML manifest files in a `build` folder:
   ``` { .bash .copy }
   adeploy -p <provider> render .
   ```
   
2. **Test** your deployment and run a server-dry-run with the generated manifests or the Helm chart using the generated Helm configuration:
   ``` { .bash .copy }
   adeploy -p <provider> test
   ```
   
3. **Deploy** the deployment to a k8s cluster using `kubectl` or `helm` under the hood:
   ``` { .bash .copy }
   adeploy -p <provider> deploy
   ```

Currently `adeploy` supports creating deployments from [Jinja](jinja/index.md) or [Helm](helm/index.md) templates or both. These template providers
are called **providers** and must be specified with `-p/--provider` when `adeploy` is invoked.

!!!tip
    You can also mix the providers i.e. to create a template for an existing Helm chart and 
    add custom deployment objects using Jinja templates.

## Project Structure

In any cases the basic structure of your `adeploy` repository looks as follows:

```
<project_name>/
  namespaces/
    <namespace>/
      <release>.yml
  defaults.yml
```

!!!tip
    You can specify a custom project name using `adeploy --name <project_name>`.
    You can also use a different namespaces directory using `adeploy --namespaces <namespaces_dir>` i.e. to switch between variables/configs for different clusters.

The `defaults.yml` contains your global variables for the Helm chart or your Jinja templates for all namespaces. For example:

* Helm Chart URLs
* Image URls and versions
* Global labels, prob and resource definitions.

In the `namespaces` folder you define namespace- and release-specific variables (and secrets) which will overwrite the 
default variables from above: `namespaces/<namespace>/<release>.yml`.

## Variables

The variables you specify in `defaults.yml` and in `namespaces/<namespace>/<release>.yml` are recursively merged so that 

* you can use them as Jinja variables in the template files in the [`templates` folder](#jinja-templates) 
* or there are directly [passed as configuration](https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing) for your [Helm chart](#helm-charts).

Please note that the namespace/release configuration in `namespaces/<namespace>/<release>.yml` is also rendered using 
the Jinja renderer and the variables from `defaults.yml`. So you can also use Jinja templating and some of the `adeploy`
specific macros and filters for `namespace/<namespace>/<release>.yml`, too. 

This might be useful to create your namespace/release config for your templates or customize your Helm configuration.  

See [Jinja](jinja/index.md) for defaults about what you can do with Jinja templating.

### Reserved Variables

There are some reserved variables that you can use for the special purpose as described below:

#### `_adeploy`

``` {.yaml title="defaults.yml"}
_adeploy:
  version: 0.7
  target_cluster_apiserver_url: https://k8s-api.example.org:6443
```

| Attribute                                | Description                                                                                                                                                         |
|------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `version`                       | Set a minimum required adeploy version i.e. to make sure required features are supported.                                                                           |
| `target_cluster_apiserver_url`          | Force to use a specific target k8s cluster for your deployment. This will cause `apeploy` to fail if your current `kubectl` context points to a different cluster. |


#### `_chart`

The special purpose variable is to point to a specific upstream Helm chart.
See [Using Helm Chart Repo](#using-helm-chart-repo).

#### `versions`

In the `versions` variable you can define a dict containing versions for your images in your deployments. You can access
these versions using the `version(name)` macro that falls back to a `latest` string if no version was specified:

``` {.yaml title="defaults.yml" hl_lines="2"}
--8<-- "examples/jinja/001-general-structure/defaults.yml::3"
```

``` {.jinja title="templates/deployment.yml"  hl_lines="5"}
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: main
          image: {{ nginx.image }}:{{ version('nginx') }}
          imagePullPolicy: Always
```

### Example

``` {.yaml title="defaults.yml"}
--8<-- "examples/jinja/001-general-structure/defaults.yml"
```

``` {.jinja title="namespaces/playground/prod.yml"}      
--8<-- "examples/jinja/001-general-structure/namespaces/playground/prod.yml"
```

You can use `adeploy -p <provider> config` to print out the fully merged namespace configuration for each release (here: `prod`):

``` {.shell}
adeploy -p jinja config . | jq .prod
{
  "versions": {
    "nginx": 1.22
  },
  "nginx": {
    "image": "registry.awesome-it.de/upstream-docker/library/nginx",
    "listen": "0.0.0.0:80",
    "locations": [
      {
        "name": "service-1",
        "upstream": "0.0.0.0:8001"
      },
      {
        "name": "service-2",
        "upstream": "0.0.0.0:8002"
      }
    ]
  }
}
```

!!!note
    Please note that dicts are recursively merged while arrays will be overwritten. The namespace/release configuration
    always takes precedence.

As mentioned these variables are passed as configuration to your Helm charts or you can use them in your Jinja templates
as follows:

``` {.jinja title="templates/deployment.yml"}
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: main
          image: {{ nginx.image }}:{{ version('nginx') }}
          imagePullPolicy: Always
```

## Templates & Helm Charts

Depending on the selected provider, the templates or Helm charts can be included or references in the following ways:

### Jinja Templates

The Jinja templates must be placed in a sub-folder called `myproject/templates` in your project directory:

```
<project_name>/
  templates/
  namespaces/
    <namespace>/
      <release>.yml
  defaults.yml
```

!!!tip
    You can specify a custom template folder using `adeploy -p jinja render --templates <templates_dir>`

!!!tip
    You can also add sub-folders in your `templates` folder to get a better overview.
    Folders and files starting with an underline `_` will be excluded from the rendering. You can use them i.e. for common
    includes in the templates itself. (TODO: Add reference to the render_file() docs).

See [Jinja Quickstart](jinja/index.md) to create, test and deploy a Jinja templated deployment using `adeploy`.

### Helm Charts

To use a Helm Chart as template source, you need to specify the source of the chart. By default `adeploy` expects a Helm
chart in the subfolder `myproject/chart`: 

```
<project_name>/
  chart/
  namespaces/
    <namespace>/
      <release>.yml
  defaults.yml
```

!!!tip
    You can specify a custom chart folder using `adeploy -p helm render --chart-dir <chart_dir>`

#### Using Helm Chart Repo

If you want to download and use an Helm chart from an upstream repo, you can specify the URL of thie chart either as 
parameter:

```shell
adeploy -p helm render --repo-url <repo_url>
```

Or if you don't want to pass the repo URL each time, you can also set the `repo_url` and the `version` of an upstream 
Helm chart in the `defaults.yml` as follows:

``` { .yaml .copy title="defaults.yml"}
_chart:
  name: my-helm-chart
  repo_url: https://helm.github.io/examples
  version: 0.1.0
```

| Attribute  | Description                                                                                                                              |
|------------|------------------------------------------------------------------------------------------------------------------------------------------|
| `name`     | Optional Helm chart name. By default the project name i.e. from the project folder or the name specified by `adeploy -n/--name` is used. |
| `repo_url` | The repository URL of the Helm chart                                                                                                     |
| `version`  | The chart version to use. This version is defined as `version` in the `Chart.yaml` of the Helm chart.                                    |

!!!tip
    It is recommended to always set the `repo_url` and pin the `version` in the `defaults.yml` for automated deployment
    pipelines. 

See [Helm Quickstart](helm/index.md) to create, test and deploy a Helm chart using `adeploy`.