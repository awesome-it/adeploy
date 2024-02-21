# Helm Example

This is a hello-world Helm chart how to deploy Helm charts using `adeploy`.

Since Helm the repository URL, chart name and version are defined in `defaults.yml`, you just need to the following to 
render the chart:

```bash
$ adeploy -p helm render
```

You can check what would be deployed as follows:

```bash
$ adeploy -p helm test
```

You can now deploy the Helm chart by using `adeploy` as follows:

```bash
$ adeploy -p helm deploy
```

Note that `adeploy` is internally still using `helm install`. So you can fallback to your default helm commands
to maintain this installation.