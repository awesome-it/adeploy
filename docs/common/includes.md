# Includes

<!-- --8<-- [start:summary] -->
`adeploy` brings support to include and optionally render YAML parts or arbitrary files into k8s manifests. 

This allows you to define repeating YAML parts (i.e. environments, affinities) at a single place and include them into
all relevant manifest files. 

Further it is now possible to add all files from a directory i.e. into a ConfigMap in order to create config files in 
your deployment.
<!-- --8<-- [end:summary] -->

## Include YAML Parts
<!-- md:provider Jinja -->

If you want to include a common environment YAML part (i.e. `env`) into multiple k8s manifest files, you can create your
environment block at a single place:

```{.yaml title="templates/common/__env.yml"}
--8<-- "examples/jinja/003-include/templates/common/__env.yml"
```

!!!tip
    Make sure to start the part files intended to include in another YAML document start with a `_` in order to exclude
    them from being directly rendered by `adeploy`.

This part file can now be included in the manifest files as follows:

=== "Nginx Deployment"

    ```{.yaml title="templates/nginx/deployment.yml" hl_lines="9 11 16"}
    --8<-- "examples/jinja/003-include/templates/nginx/deployment.yml:template"
    ```
=== "Redis Deployment"

    ```{.yaml title="templates/redis/deployment.yml" hl_lines="9 11 16"}
    --8<-- "examples/jinja/003-include/templates/redis/deployment.yml:template"
    ```

See [`include_file()`](functions.md#adeploy.common.jinja.globals.Handler.include_file) for usage and parameters.

## Include Arbitrary Files
<!-- md:provider Jinja -->

To include an arbitrary file (i.e. `nginx.conf`) to a deployment you can use a ConfigMap as follows:

<!-- --8<-- [start:example] -->
```{.yaml title="templates/common/configmap.yml" hl_lines="11 12-14"}
--8<-- "examples/jinja/003-include/templates/common/configmap.yml"
```
This will read the content of `files/nginx.conf` as well as scan the directory `files/conf.d` for files, read the 
content and include them into the ConfigMap using the filename as key.
<!-- --8<-- [end:example] -->

Expect `dir`, you can pass the same parameters for [`list_dir()`](functions.md#adeploy.common.jinja.globals.Handler.list_dir) 
as for [`include_file()`](functions.md#adeploy.common.jinja.globals.Handler.include_file) to control how the files 
inside `dir` should be handled.

You can now mount these files into your deployment as usual:

```{.yaml title="template/nginx/deployment.yml" hl_lines="7-9 18-21 23-25"}
--8<-- "examples/jinja/003-include/templates/nginx/deployment.yml:template"
```

!!!tip
    You can use [`include_file()`](functions.md#adeploy.common.jinja.globals.Handler.include_file) and the filter  
    [`sha256sum`](filters.md#adeploy.common.jinja.filters.Handler.include_file) to hash the config map and thus trigger 
    `adeploy` (i.e. `kubectl`) to also re-create the deployments whenever a file in the config map has changed.

### Download Remote Files

You can also use external URLs with `include_file(path=https://....)` to download and render definitions e.g. from GitHub.

For example the following will download and CRDs for ServerMonitors from [prometheus-operator](https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml) 
and add them to your deployment: 

```{.jinja title="templates/crds.yml"}
{{ include_file('https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml', direct=True, render=False, indent=0) }}
```

### Skip & Escape

If you include the file content as a string, you can use `skip` to remove characters and `escape` to escape them as follows:

```{.jinja title="templates/configmap.yml" hl_lines="9"}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ name }}-{{ release }}-config
  namespace: {{ namespace }}
  labels:
    {{ create_labels(component='config') }}
data:
  single-line-string: {{ include_file('files/my-config-sccript.gohtml', direct=True, render=False, indent=0, skip=['\n', '\r'], escape=['\"'])) }}
```

This will include the content of `my-config-script.gohtml` while removing newlines and escape quotes `"` as `\"`.

---

Find more examples in the [examples folder](https://github.com/awesome-it/adeploy/tree/master/examples/jinja/003-inclnude) 
or see [`include_file()`](functions.md#adpeloy.common.jinja.globals.Handler.include_file) and 
[`list_dir()`](functions.md#adpeloy.common.jinja.globals.Handler.list_dir) for usage and parameters.