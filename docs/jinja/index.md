# Jinja Deployment

To start a new Jinja templated deployment i.e. for a NGINX server with releases `test` and `prod` in the namespace `playground`, 
create the basic repository structure as follows:

``` { .bash .copy }
mkdir my-deployment && cd my-deployment
mkdir -p namespaces/playground
touch defaults.yml namespaces/playground/test.yml namespaces/playground/prod.yml
```

## Default Variables

Add your defaults variables (for all namespaces and releases) to the `defaults.yml`. 

It has proved helpful to set all default values in `defaults.yml` so that the Jinja templates in the template directory 
can be rendered without errors.

!!! tip
    In addition it makes sens to pin the image versions in the [Namespace/Release Configuration] while setting the most 
    recent configuration in the `defaults.yml`. In doing so, you can deploy newer versions in non-production environments
    for testing purpose (i.e. using CI/CD) and have pinned versions and controlled updates in production environments.  

A possible `defaults.yml` might look as follows:

```{.yaml title="defaults.yml"}
--8<-- "examples/jinja/001-general-structure/defaults.yml"
```

## Namespace/Release Configuration

The destination namespace and the releases of the deployment must be defined by creating the namespace/release 
configurations in `namespaces/<namespace>/<release>.yml`.

For the namespace `playground` and releases `test` and `prod` the following configuration file must be created:

===+ "`prod.yml`"
    ``` { .yaml title="namespaces/playground/test.yml"}
    --8<-- "examples/jinja/001-general-structure/namespaces/playground/prod.yml"
    ```

=== "`test.yml`"
    ``` { .yaml title="namespaces/playground/test.yml"}
    --8<-- "examples/jinja/001-general-structure/namespaces/playground/test.yml"
    ```

## Render

After [default variable](#default-variables) and [namespace/release configuration](#namespacerelease-configuration) has 
been created, the template can be rendered into k8s resource manifest files:

```{.bash}
adeploy -p jinja render .
```
??? example "Example run ..."
    ![asciicast](jinja-render.cast)

This will create vanilla k8s manifest files in the `build` output folder for each release.

!!!tip

    You can (re-)create the output for a specific namespace or release by filter for the specific namespaces or releases
    as `adeploy --filter-namespace <namespace> --filter-release <release>`. You can pass these arguments multiple times to
    include multiple namespaces or release.

## Test

You can now test the generated deployment from the `build` folder by applying the manifest file in a dry-run using the 
`server` stragegy (i.e. `kubectl apply --dry-run=server`). In doing so, the API resources are submitted using server-side 
requests but not persisted by the API. This can be done as follows:

```{.bash}
adeploy -p jinja test
```
??? example "Example run ..."
    ![asciicast](jinja-test.cast)

!!!tip

    Similar to the build, you can also run the tests for specific namespaces or releases only by specifying both or
    one of the attributes `--filter-namespace <namespace>` or `--filter-release <release>` i.e. 
    `adeploy --filter-namespace playground -p jinja test .`

## Deploy

The generated and tested k8s resources can now be deployed to the k8s cluster as follows:

```{.bash}
adeploy -p jinja deploy
```
??? example "Example run ..."
    ![asciicast](jinja-deploy.cast)

!!! note
    `adeploy` will not create namespaces for you, so you still need to manually create i.e. the `playground` namespace first.

!!! tip
    `adpeloy` will store the destination cluster of your deployment in `~/.adeploy`. If you accidentally have a wrong cluster 
    enabled in your current context, `adeploy` will warn you accordingly before it continues.

!!! tip
    Run `adpeloy` in debug mode using `adeploy -d -p jinja deploy` to get verbose output e.g. the `kubectl` commands that
    are being executed by `adeploy`.

---
--8<-- "docs/common/_more.md"