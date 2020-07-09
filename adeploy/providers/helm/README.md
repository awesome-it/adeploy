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
* a `namespaces` directory containing deployment configuration for different namespaces and releases.

### Deployment Configurations

A deployment configuration is a file in the appropriate namespace folder with release name as filename:

```
/mydeployment/namespaces/<namespace>/<release>.yml
```

#### Alternative Namespace Structure

If you have a repo with multiple deployments, you can have a separate namespace folder i.e:

```
/repo/deployment-1
/repo/deployment-2
/repo/deployment-3
...
/repo/namespaces/<namespace>/deployment-1/<release>.yml
/repo/namespaces/<namespace>/deployment-2/<release>.yml
/repo/namespaces/<namespace>/deployment-3/<release>.yml
```

### Charts

The Helm chart in the `chart` folder will be installed with variables for each namespace and deployment-release merged with the variables from `defaults.yml`. 

If no chart folder is given, an upstream chart can be automatically downloaded using `--repo-url URL` in the render step:
```bash
$ adeploy -p helm render . --repo-url https://chart.url
```

If using `--repo-url`, you should make sure, that the content of `chart` is ignored by git. To always fetch the latest chart version when rendering.