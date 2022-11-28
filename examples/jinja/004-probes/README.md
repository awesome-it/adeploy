# Create Secrets

A Jinja based `adeploy`  project that includes:

* namespace `playground`,
* two releases: `prod`,`test` and
* a global probes configuration for all deployments defined in `defaults.yml`.

Note that a global probes configuration makes sense if you deploy a larger number of similar deployments
like microservices etc. or if you need different probe parameters for different namespaces or releases i.e. test vs. prod.

Deploy as follows:

```
$ kubectl create namespace playground
$ adeploy -p jinja [-n <name>] render .
$ adeploy -p jinja [-n <name>] test
$ adeploy -p jinja [-n <name>] deploy
```

By default `adeploy` is using the project folder as deployment name (i.e. `004-probes`). 
If you want to use another deployment name, pass it with `-n <name>`.

## More Info

* https://github.com/awesome-it/adeploy/tree/master/adeploy/providers/jinja
* https://github.com/awesome-it/adeploy/tree/master/adeploy/providers/jinja#global-probes-configuration