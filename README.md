# adeploy

<!-- --8<-- [start:intro] -->

We build `adeploy`, an universal deployment tool for Kubernetes that supports rendering and deployment of lightweight 
Jinja templated k8s manifests and also Helm charts. 

We’ve added support for ... 

* using **Jinja variables** from per cluster, namespaces or release configuration 
* easy **secret management** based on [Gopass](https://github.com/gopasspw/gopass) or other command line based password managers
* running deployment tests in **CI/CD pipelines**
* **previewing** and **patching** upstream [Helm Charts](https://artifacthub.io/) before deploying
* **extending** upstream Helm Charts with custom Jinja-templates manifests
* handy templating for **labels, annotations, probes, resource limits** and other metadata

... and even more to make your daily work with k8s easier.

<!-- --8<-- [end:intro] -->

## Documentation & Support 

* `adeploy` is Open Source and hosted on GitHub: [https://github.com/awesome-it/adeploy](https://github.com/awesome-it/adeploy).
* You can report issues on GitHub: [https://github.com/awesome-it/adeploy/issues](https://github.com/awesome-it/adeploy/issues).
* Find the documentation at [https://awesome-it.de/docs/adeploy/latest](https://awesome-it.de/docs/adeploy/latest).

## Examples

This is how you can render, test (preview) and deploy a Helm Chart:
[![asciicast](https://asciinema.org/a/iToqBOzT8t2Up6x6lRhjF0sk2.svg)](https://asciinema.org/a/iToqBOzT8t2Up6x6lRhjF0sk2)

Or you can render, test (preview) and deploy Jinja-templated manifests:
[![asciicast](https://asciinema.org/a/li2ZqLa5pnh6pj1KWoOrUIHOe.svg)](https://asciinema.org/a/li2ZqLa5pnh6pj1KWoOrUIHOe)

You'll find some examples in the [example](https://github.com/awesome-it/adeploy/tree/master/examples) directory.

## Getting Started

<!-- --8<-- [start:install] -->

You can find `adeploy` on [GitHub](https://github.com/awesome-it/adeploy). But it is recommended to install 
or upgrade [adeploy](https://pipy.org/project/adeploy) using `pip`:

```shell
$ pip install adeploy
```

Or use [pipx](https://github.com/pypa/pipx) to install, upgrade and run `adeploy` in an isolated environment:

```shell
$ pipx install adeploy
$ pipx upgrade adeploy
```

You should now be able to run `adeploy` from the command line:

```shell
adeploy --help
```

You can now start to use `adeploy`.  

<!-- --8<-- [end:install] -->

See the [usage documentation](https://awesome-it.de/docs/adeploy/latest/usage/) to start using `adeploy`.

## Read More

* https://awesome-it.de/2020/09/11/adeploy-an-universal-deployment-tool-for-kubernetes/