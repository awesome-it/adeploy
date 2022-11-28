# Create Secrets

An example deployment that creates secrets for a Jinja based `adeploy` project that includes:

* namespace `playground`,
* two releases: `prod`,`test` and
* an `ImagePullSecret`, an environment variable `my_secret` and
* an `Ingress` with a TLS Secret created by `adeploy`.

For demonstration purpose, we are using `cat secrets/*` to retrieve secrets. But in practise this should be replaced 
with a password tool i.e. `gopass`, `Ansible Vault` or `Vault by HashiCorp` or by a command to generate random 
passwords.

Deploy as follows:

```
$ kubectl create namespace playground
$ adeploy -p jinja [-n <name>] render .
$ adeploy -p jinja [-n <name>] test
$ adeploy -p jinja [-n <name>] deploy
```

By default `adeploy` is using the project folder as deployment name (i.e. `002-secrets`). 
If you want to use another deployment name, pass it with `-n <name>`.

## More Info

* https://github.com/awesome-it/adeploy#jinja-secret-functions