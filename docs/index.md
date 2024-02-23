# About

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

## Examples

This is how you can render, test (preview) and deploy a Helm Chart:
![asciicast](helm.cast){ auto_play="true" loop="true" }

Or you can render, test (preview) and deploy Jinja-templated manifests:
![asciicast](jinja.cast){ auto_play="true" loop="true" }

You'll find more examples in the [example](https://github.com/awesome-it/adeploy/tree/master/examples) directory or 
follow the [install guide](install.md) to get started.