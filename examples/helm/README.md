# Example

This is a hello-world Helm chart how to deploy Helm charts using `adeploy`.

## Render

Since Helm repo-url, chart name and version are defined in `defaults.yml`, you just need to the the following to render the chart:

```bash
$ adeploy -p helm render .
```

