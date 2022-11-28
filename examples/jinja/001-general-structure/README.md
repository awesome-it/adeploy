# General Structure

This is the general structure for a Jinja based `adeploy` project that includes:

* namespace `playground` and
* two releases: `prod` and `test`

Deploy as follows:

```
$ kubectl create namespace playground
$ adeploy -p jinja [-n <name>] render .
$ adeploy -p jinja [-n <name>] test
$ adeploy -p jinja [-n <name>] deploy
```

By default `adeploy` is using the project folder as deployment name (i.e. `001-general-structure`). 
If you want to use another deployment name, pass it with `-n <name>`.




