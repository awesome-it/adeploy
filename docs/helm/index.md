# Helm Deployment

## Quickstart

To start an Helm deployment i.e. `hello-world` with release `test` in the namespace `playground` using `adeploy`, 
create the basic repository structure as follows:

``` { .bash .copy }
mkdir hello-world && cd hello-world
mkdir -p namespaces/playground
touch defaults.yml namespaces/playground/test.yml
```

### Default Variables

Add the Helm Chart repo, the Chart version and default variables to configure the Helm Chart: 

=== "Minimum `defaults.yml`"

    ``` {.yaml title="defaults.yml"}
    --8<-- "examples/helm/defaults.yml::4"
    ```
    
=== "Add defaults from `values.yml`"

    The following includes defaults from the Chart's [values.yml](https://github.com/helm/examples/blob/main/charts/hello-world/values.yaml). 

    !!!tip
        It is up to you whether to include the defaults as reference, overwrite them to define custom defaults or skip 
        including the variables at all and use the upstream defaults.

    ``` {.yaml title="defaults.yml"}
    --8<-- "examples/helm/defaults.yml"
    ```
### Namespace/Release Configuration

### Render, Test & Deploy