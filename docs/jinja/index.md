# Jinja Deployment

## Quickstart

To start a new Jinja templated deployment i.e. for a NGINX server with releases `test` and `prod` in the namespace `playground`, 
create the basic repository structure as follows:

``` { .bash .copy }
mkdir my-deployment && cd my-deployment
mkdir -p namespaces/playground
touch defaults.yml namespaces/playground/test.yml namespaces/playground/prod.yml
```

### Default Variables

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

### Namespace/Release Configuration

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