# General Structure

This is a Jinja based `adeploy` project that includes:

* namespace `playground`,
* two releases: `prod`, `test` and  
* two deployments for `nginx` and `redis` that is using 
  * a global resources configuration.

Note that this makes sense, if you don't want to modify your Jinja or Helm templates or
if you need to set the same resources for similar services i.e. microservices. 

Deploy as follows:

```
$ kubectl create namespace playground
$ adeploy -p jinja [-n <name>] render .
$ adeploy -p jinja [-n <name>] test
$ adeploy -p jinja [-n <name>] deploy
```

By default `adeploy` is using the project folder as deployment name (i.e. `006-resources`). 
If you want to use another deployment name, pass it with `-n <name>`.

## More Info

* https://github.com/awesome-it/adeploy/tree/master/adeploy/providers/jinja
* https://github.com/awesome-it/adeploy/tree/master/adeploy/providers/jinja#global-resources-configurations