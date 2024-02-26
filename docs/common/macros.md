# Jinja Macros
<!-- md:provider Jinja --><!-- md:provider Helm -->

You can add and use custom [Jinja Macros](https://jinja.palletsprojects.com/en/3.0.x/templates/#macros) in your 
`defaults.yml`, the namespace/release configuration or in your Jinja templates.

You can add Jinja files containing your macros at the following places: 

* the current dir
* the current parent dir
* the directory of the template
* the parent directory of the template.

## Example

You can define the following macro to create a `ServiceMonitor`:

```{.jinja title="templates/macros/create_servicemonitor.jinja"}
{% macro create_servicemonitor(service, labels) -%}
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ service.name if 'name' in service else service }}
  namespace: {{ namespace }}
  labels:
    {{ create_labels(component='monitoring', labels=labels) }}
spec:
  selector:
    matchLabels:
      {{ labels }}
  endpoints:
    - port: http
      path: /actuator/prometheus
{%- endmacro %}
```
Now you can use this macro in your template as follows:

```{.jinja title="templates/service.yaml"}
{% from "macros/create_servicemonitor.jinja" import create_servicemonitor with context %}

{{ create_servicemonitor(service.name, service.labels) }}
``` 