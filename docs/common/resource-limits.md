# Resource Limits

<!-- --8<-- [start:summary] -->
For larger deployments it is sometimes hard to keep track of the defined resource limits. For example a deployment for a 
distributed system having lots of similar workloads are suitable for a global definition of resource limits. `adeploy` 
does support such a global definition at a single point in your default or namespace/release configuration.
<!-- --8<-- [end:summary] -->

## Global Resources Configuration <!-- md:provider Jinja -->

`adeploy` introduces the reserved variable `__resources` that allows to define resource limits for all workloads on a 
global, workload or container scope.

### Global Scope 

To set resource limits for all compatible API objects (`Deployment`, `StatefulSet`, `ReplicaSet`, ...) in your deployment, add 
the following to the `defaults.yml` or the namespace/release configuration:

```{.yaml title="defaults.yml"}
_resources:
--8<-- "examples/jinja/006-resources/defaults.yml:global-scope"
```

!!!note
    These globally set limits are ignored, if limits are already defined in the manifest files for the workload objects 
    in the `templates` folder.

### Workload Scope

To set resource limits for a specific API object queried by its name (i.e. `nginx`), add the following:

```{.yaml title="defaults.yml"}
_resources:
--8<-- "examples/jinja/006-resources/defaults.yml:workload-scope"
```

!!!note
    These globally set limits are ignored, if limits are already defined in the manifest file for the workload object 
    `nginx` in the `templates` folder.

### Container Scope

To set resource limits for a specific container queried by its name (i.e. `main`) and the workload object 
(i.e. `redis`), add the following:

```{.yaml title="defaults.yml"}
_resources:
--8<-- "examples/jinja/006-resources/defaults.yml:container-scope"
```

!!!warning
    These globally set limits take precedence and will overwrite any limit that is defined in the manifest file for the 
    image `main` of the workload object `redis`.