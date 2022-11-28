# Create Secrets

A Jinja based `adeploy`  project that includes:

* namespace `playground`,
* two releases: `prod`,`test` and
* two deployments that are using a shared, single environment file using `include_file()` and
* a config map that includes files from the folder `files`. 

Deploy as follows:

```
$ kubectl create namespace playground
$ adeploy -p jinja [-n <name>] render .
$ adeploy -p jinja [-n <name>] test
$ adeploy -p jinja [-n <name>] deploy
```

By default `adeploy` is using the project folder as deployment name (i.e. `003-include-files`). 
If you want to use another deployment name, pass it with `-n <name>`.

## More Info

* https://github.com/awesome-it/adeploy/tree/master/adeploy/providers/jinja