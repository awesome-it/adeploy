# Helm Deployment

## Quickstart

To start an Helm deployment i.e. [hello-world](https://github.com/helm/examples/blob/main/charts/hello-world) with 
release `test` in the namespace `playground` using `adeploy`, create the basic repository structure as follows:

``` { .bash .copy }
mkdir hello-world && cd hello-world
mkdir -p namespaces/playground
touch defaults.yml namespaces/playground/test.yml
```

### Default Variables

Add the Helm Chart repo, the Chart version and default variables to configure the Helm Chart: 

===+ "Minimum `defaults.yml`"

    ``` {.yaml title="defaults.yml"}
    --8<-- "examples/helm/001-quickstart/defaults.yml::4"
    ```
    
=== "Add defaults from `values.yml`"

    The following includes defaults from the Chart's [values.yml](https://github.com/helm/examples/blob/main/charts/hello-world/values.yaml). 

    !!!tip
        It is up to you whether to include the defaults as reference, overwrite them to define custom defaults or skip 
        including the variables at all and use the upstream defaults.

    ``` {.yaml title="defaults.yml"}
    --8<-- "examples/helm/001-quickstart/defaults.yml"
    ```
### Namespace/Release Configuration

In the next step, the namespace and the release of the deployment must be defined by creating the namespace/release 
configuration in `namespaces/<namespace>/<release>.yml`.

For the namespace `playground` and release `test` the configuration look as follows:

``` { .yaml title="namespaces/playground/test.yml"}
--8<-- "examples/helm/001-quickstart/namespaces/playground/test.yml"
```

Note that the namespace/release configuration will be rendered using Jinja. So you can use the variables from 
`defaults.yml`, [Jinja native macros and filters](https://jinja.palletsprojects.com/) and the [Jinja macros, filters and functions provided by `adeploy`](../common/index.md). 


### Render

After the Helm Chart configuration consisting of [Default Variables](#default-variables) and [Namespace/Release Configuration](#namespacerelease-configuration)
has been created, the Helm deployment template can be rendered using `adeploy`:

```{ .bash}
adeploy -p helm render .
```
??? example "Example run ..."
    ![asciicast](helm-render.cast)

This will ...

* download and extract the Helm Chart in `build/helm/chars/hello-world` 
* create a single Kubernetes manifest file in `build/helm/playground/hello-world/test/manifest.yml` 
* create the final Helm Chart configuration in `build/helm/playground/hello-world/test/values.yml`.

!!! tip
    On each render command, the `build` directory will be generated from scratch. So it is recommended to exclude
    the build folder from Git.

### Test

Using these files, the deployment can now be applied in dry-run using the `server` strategy. Meaning that the API resources
are submitted using server-side requests but not persisted by the API. This can be done as follows:

```{.bash}
adeploy -p helm test .
```
??? example "Example run ..."
    ![asciicast](helm-test.cast)

As you can see in the example, `adeploy` will print out all resources that Helm is going to add to your k8s cluster. This
gives you a way better control about what is going to be deployed if you run a `helm install`:

```{.bash hl_lines="4-6"}
adeploy.Test Testing Helm deployment "playground/hello-world-test" ...
adeploy.Test ... Chart version 0.1.0, app version 1.16.0, last deployed 2024-02-21T12:24:03.762735593+01:00: Dry run complete, status pending-upgrade
adeploy.Test ... Testing raw manifests from "build/helm/playground/hello-world/test/manifest.yml" (may fail) ...
adeploy.Test ...... namespace: playground resource: serviceaccount, name: test-hello-world: configured
adeploy.Test ...... namespace: playground resource: service, name: test-hello-world: configured
adeploy.Test ...... namespace: playground resource: deployment.apps, name: test-hello-world: created
adeploy.Test Testing finished
```

### Deploy

The rendered Helm deployment can be deployed to the cluster as follows:

```{.bash}
adeploy -p helm deploy .
```
??? example "Example run ..."
    ![asciicast](helm-deploy.cast)

!!! note
    `adeploy` will not create namespaces for you, so you still need to manually create i.e. the `playground` namespace first.

!!! tip
    `adpeloy` will store the destination cluster of your deployment in `~/.adeploy`. If you accidentally have a wrong cluster 
    enabled in your current context, `adeploy` will warn you accordingly before it continues.

Helm is internally invoked using `helm uprade --install`, so `adeploy -p helm deploy` will also cover Helm upgrades. 

---

There is even more, have a look at the advanced topics using `adeploy` for Helm deployments. 

There is also some [common tools](../common/index.md) i.e. Jinja helper functions to create labels, secrets, resource limits 
etc. that can be used in both Helm and Jinja deployments.