# Common

`adeploy` has useful features that can be used in both, Helm chart templates and Jinja deployment templates.

## [Secrets](secrets.md)
--8<-- "docs/common/secrets.md:summary"

## [Includes](includes.md)
--8<-- "docs/common/includes.md:summary"

##  [Manage Labels](labels.md)
--8<-- "docs/common/labels.md:summary"

##  [Resource Limits](resource-limits.md)
--8<-- "docs/common/resource-limits.md:summary"

##  [Probes](probes.md)
--8<-- "docs/common/probes.md:summary"

## Jinja Helpers

Next to the features from above, you can use the complete Jinja templating support when creating Jinja deployment or
Helm chart templates using `adeploy`. Please see the official [Jinja documentation](https://jinja.palletsprojects.com/) 
for details.

Next to the full Jinja templating support, we've added some very useful functions and filters that can be used when 
creating Jinja deployment or Helm chart templates using `adeploy`:

* [Jinja Functions](functions.md)
* [Jinja Filters](filters.md)
* [Jinja Macros](macros.md) 