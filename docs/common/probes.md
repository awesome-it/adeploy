# Probes

<!-- --8<-- [start:summary] -->
Next to labels and resources, `adeploy` also allows to update liveness, readiness and startup probes on a global or 
workload scope at a single point in the default or namespace/release configuration.
<!-- --8<-- [end:summary] -->

## Global Probes Configuration 
<!-- md:provider Jinja -->

`adeploy` introduces the reserved variable `__probes` that allows to update probes on a global or workload scope.

!!!warning
    `adeploy` will only update your probe definitions, but it won't add any new probes to your manifest! This feature is 
    thought to define the execution part of the probe in the manifest and set the probe parameters (i.e. timeouts etc.)
    at a single point in your configuration. 

    If you want to define also the execution part, you need to add the following minimal probe snippets to your manifest:

    ```{.yaml title="templates/deployment.yml" hl_lines="4-6"}
    containers:
      - name: main
        image: registry.k8s.io/busybox 
        livenessProbe: {}
        readinesProbe: {}
        startupProbe: {}
    ```

!!!note
    You can either use snake casing (í.e. `period_seconds`) or camel casing as in the 
    [official k8s docs](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) 
    (i.e. `periodSeconds`).

### Global Scope 

To update probes for all compatible API objects (`Deployment`, `StatefulSet`, `ReplicaSet`, ...) in your deployment, add 
the following to the `defaults.yml` or the namespace/release configuration:

```{.yaml title="defaults.yml"}
_probes:
--8<-- "examples/jinja/004-probes/defaults.yml:global-scope"
```

This will update all probes in the generated manifest files and overwrite it with the given values. 

### Workload Scope

To update the probe definition for a specific workload object queried by its name (i.e. `{{ name }}-{{ release }}-redis`), add the following:

```{.yaml title="defaults.yml"}
_resources:
--8<-- "examples/jinja/004-probes/defaults.yml:workload-scope"
```