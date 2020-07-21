# Deployment Provider: Helm

## Structure

```
/mydeployment/

/mydeployment/chart

/mydeployment/namespaces
/mydeployment/namespaces/mynamespace/prod.yml
/mydeployment/namespaces/mynamespace/test.yml

/defaults.yml
```

* A Helm deployment consists of an optional `chart` folder containing a Helm chart,
* a `default.yml` file i.e. containing versions and
* a `namespaces` directory containing [deployment configuration for different namespaces and releases](../../README.md#Deployment Configurations).

### Charts

The Helm chart in the `chart` folder (default value of `--chart-dir`) will be installed with variables for each namespace and deployment-release merged with the variables from `defaults.yml`.:

```bash
$ adeploy -p helm render . [--chart-dir ./chart]
```

The chart name is given by the deployment name i.e. the folder name (here: `mydeployment`) or you specify another name using
`--name` parameter.

If no chart folder is given, an upstream chart can be automatically downloaded using `--repo-url URL` in the render step:
 
```bash
$ adeploy [--name customer_chart_name] -p helm render . --repo-url https://chart.url
```

#### Version & AppVersion
 
The chart version and the app version (`appVersion`) can be set globally in the `defaults.yml` (or `defaults/<release>.yml`) for the appropriate deployments:

```yaml
_chart:
    version: 0.0.0
    appVersion: 0.0.0
```