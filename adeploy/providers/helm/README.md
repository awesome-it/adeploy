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

The Helm chart in the `chart` folder will be installed with variables for each namespace and deployment-release merged with the variables from `defaults.yml`. 

If no chart folder is given, an upstream chart can be automatically downloaded using `--repo-url URL` in the render step.
The chart name is given by the deployment name i.e. the foldername (here: `mydeployment`) or you specify another name using
`--name` parameter.
 
```bash
$ adeploy [--name customer_chart_name] -p helm render . --repo-url https://chart.url
```

If using `--repo-url`, you should make sure, that the content of `chart` is ignored by git. To always fetch the latest chart version when rendering.