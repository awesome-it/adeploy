# Labels

<!-- --8<-- [start:summary] -->
`adeploy` provides functions and mechanisms to create default and custom labels following best practises in a single 
place of your default or namespace/release configuration.
<!-- --8<-- [end:summary] -->

## Default Labels 
<!-- md:provider Jinja --><!-- md:provider Helm -->

You can use the Jinja function [`create_labels()`](functions.md#create_labels) to create set of default labels plus 
additional labels that you can specify in your `defaults.yml` or namespace/release configuration as follows:

```{.yaml title="defaults.yml"}
--8<-- "examples/jinja/005-labels/defaults.yml:create_labels"
```

In your Jinja deployment template, you can use the `labels` variable as follows:

```{.yaml title="deployment.yml" hl_lines="6 9 18"}
--8<-- "examples/jinja/005-labels/templates/deployment.yml:use_labels"
```

See [`create_labels()`](functions.md#adpeloy.common.jinja.globals.Handler.create_labels) for usage and parameters.

### Nested Labels
<!-- --8<-- [start:nested_labels] -->

You can use `create_labels()` to define global labels i.e. in your `defaults.yml`:

```{.yaml title="defaults.yml"}
--8<-- "examples/jinja/006-nested-labels/defaults.yml:create_labels"
```

And use `create_labels()` another time to add object related labels i.e. in your template files:

```{.yaml title="templates/deployment.yml" hl_lines="6 9 18"}
--8<-- "examples/jinja/006-nested-labels/templates/deployment.yml:use_labels"
```

This will result in the following labels:

```{.yaml title="build/jinja/.../prod/deployment.yml"}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: 006-nested-labels-prod
  namespace: playground
  labels: 
    app.kubernetes.io/name: "nginx"
    app.kubernetes.io/instance: "prod"
    app.kubernetes.io/component: "my-deployment"
    app.kubernetes.io/part-of: "006-nested-labels"
    app.kubernetes.io/managed-by: "adeploy"
```

<!-- --8<-- [end:nested_labels] -->

See [`create_labels()`](functions.md#adpeloy.common.jinja.globals.Handler.create_labels) for usage and parameters.

## Global Label Configuration <!-- md:provider Jinja -->

Similar to [probes](probes.md) or [resource-limits](resource-limits.md), you can specify a global labels configuration 
in `defaults.yml` or in the namespace/release configuration as follows:

```{.yaml title="defaults.yml"}
--8<-- "examples/jinja/005-labels/defaults.yml:global_labels"
```

These labels will be added to all appropriate `metadata`, `matchLabels` and `selector` properties. 

!!!tip 
    Note that you can use Jinja variables in the labels, too.

