# Secrets

<!-- --8<-- [start:summary] -->
`adeploy` can create secrets for you in various ways:

* Retrieve secrets from the [Gopass password manager](https://www.gopass.pw/) or any other command line based password manager
* Retrieve or auto-generate (rotate) arbitrary secrets using bash commands
* Use [ansible-vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html).

Since `adeploy` will create non-existing secrets but won't touch existing secrets[^1], a very simple but effective concept
of secret management can be established and `adeploy` can be used to automate everything while exluding secret handling 
in CI/CD pipelines.

[^1]: 
    If `--recreate-secrets` is specified, `adeploy` is forced to re-create also existing secrets. This is useful to 
    update secrets or rotate auto-generated secrets. 

<!-- --8<-- [end:summary] -->

## Principle

The idea behind handling secret in `adeploy` is to separate the process of deployment in two overlapping parts:

1. [Deployment with creating or updating secrets](#deployment-with-creating-or-updating-secrets)
2. [Deployment without handling secrets](#deployment-without-handling-secrets)

### Deployment with creating or updating secrets

Since the first part requires to retrieve sensitive data i.e. passwords, tokens or certificates, this should be executed
by a trusted person and should never be executed by an automation. In most cases, this part will be executed on the local
machine by the author of the `adeploy` deployment template. We assume that this person also has access to a local password
store (i.e. [Gopass](https://www.gopass.pw/)) or other compatible password managers that provide a command line interface.

!!!warning "Deployment with creating or updating secrets"
    If secrets are missing on the destination cluster, `adeploy` tries to create them and thus assumes a 
    [deployment including sensitive information](#deployment-with-creating-or-updating-secrets).

### Deployment without handling secrets

The deployment part that is not touching the secrets must not be executed by a person having access to sensitive data 
and thus is particularly suitable for automation. This includes changing all resources excluding secrets which is the
most common case when changing k8s deployments.

!!!success "Deployment without handling secrets"
    If no secrets are missing on the destination cluster, `adeploy` assumes a 
    [deployment without handling secrets](#deployment-without-handling-secrets) which fully supports a CI/CD based
    automation process.

## Jinja Helpers 
<!-- md:provider Jinja --><!-- md:provider Helm -->

To make `adpeloy` create secrets if they do not exist but leave them untouched if they do exist, you must use one of the
following Jinja functions:

* [`create_secret()`](functions.md#create_secret)
* [`create_docker_registry_secret()`](functions.md#create_docker_registry_secret)
* [`create_tls_secret()`](functions.md#create_tls_secret)

This function can be used in the `defaults.yml` or in the namespace/release configuration and will generate and return a 
unique[^1] secret name or secret reference (if passing `as_ref=True`):

[^1]: Based on non-sensitiv secret information like Gopass path, name the bash command used to generate the secret value.

```{.yaml title="playground/secrets/prod.yml"}
--8<-- "examples/jinja/002-secrets/namespaces/playground/prod.yml:4"
```

You can now use the Jinja variable containing the secret name or secret reference in your Jinja deployment templates or 
the Helm chart configuration as follows:

```{.yaml title="templates/deployment.yml" hl_lines="3-4 10-12"}
--8<-- "examples/jinja/002-secrets/templates/deployment.yml:28:39"
```

## Retrieving Sensitive Data

`adeploy` support different ways to retrieve (or generate) the sensitive data to create the secrets:

### Gopass

By default, the secret value is taken from [Gopass password store](https://www.gopass.pw/) that is properly installed
and setup on the local machine that will run the [trusted deployment](#deployment-with-creating-or-updating-secrets). 

The path to the password of the Gopass repo must be specified in the `create_secret()` functions:

```{.jinja}
my_deployment:
  config:
    secretName: {{ create_secret(my_secret="/my/path") }}
    secretKey: my_secret
```

This will create a secret containing with a key `my_secret` and value from `gopass cat /my/path`.

A list of different Gopass repos can be specified in `--gopass-repo` or as comma separated list in the environment 
variable `ADEPLOY_GOPASS_REPOS`. 

!!!note "Example"

    If `ADEPLOY_GOPASS_REPOS=a,b` is set and `create_secret(key='/my/path')` is used, the following 
    Gopass commands are tried to retrieve the secret value:
    
    - `gopass cat /my/path`
    - `gopass cat a/my/path` 
    - `gopass cat b/my/path`
    
    The first command returning a valid secret value is used.

!!!warning "Binary Data in Secrets"

    `adeploy` is using `gopass cat` to retrieve secret values. This allows to also create secrets containing binary data.
    To do so, you must use `gopass cat` or `gopass fscopy` to create Gopass secrets from binary content.
    See [Support for Binary Content](https://github.com/gopasspw/gopass/blob/master/docs/features.md#support-for-binary-content)
    for details.

### Custom Password Command

If you don't use [Gopass password store](https://www.gopass.pw/), you can use custom commands i.e. bash scripts or 
other password managers that provide a compatible command line interface by passing `custom_cmd=True` as follows:

```{.jinja}
my_deployment:
  config:
    secretName: {{ create_secret(
                    custom_cmd=True, 
                    my_key='my-custom-tool --arg1=$SOME_ENV_VARS my_password') }}
    secretKey: my_key
```

This will create a secret with a key `my_key` and the stdout of the custom command as value. 

!!!note

    Note that the command string is used to create a unique secret name. So if you are using the same command to create 
    multiple secrets i.e. using a random-password script for auto-rotation, you should make sure to add a unique expression
    to the command.

!!!note

    Note that you can use environment variables (i.e. `$SOME_ENV_VARS`) in your command which are taken from the executing
    shells environment.

### Direct Method

To specify a secret value directly in your configuration, you can prevent retrieving the data by passing `use_pass=False` 
as follows:

```{.jinja}
myjinjatemplate:
  config:
    secretName: {{ create_secret(secret_name, use_pass=False, my_key=my_secret_value) }}
    secretKey: my_key
```

!!!danger

    You will have sensitive data in your `defaults.yml` or in your namespace/release configuration which might be uploaded
    to a Git repo or similar. This is strongly discouraged!

## Examples

### Create Image Pull Secret

```{.jinja title="namespaces/playground/prod.yml"}
secrets:
  registry: {{ create_docker_registry_secret(
               server='registry.awesome-it.de',
               username='sa_registry_ro',
               custom_cmd=True,
               password='cat namespaces/playground/secrets/my_secret_prod') }}
```

```{.jinja title="templates/deployment.yml" hl_lines="9-10"}
apiVersion: apps/v1
kind: Deployment
metadata:
...
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 60
      imagePullSecrets:
        - name: {{ secrets.registry }}
      containers:
```

### Create TLS Secrets for Ingress

```{.jinja title="namespaces/playground/prod.yml"}
ingress:
  className: external
  tls:
    - hosts:
        - mydomain.com
      secretName: {{ create_tls_secret(
                      custom_cmd=True,
                      cert='cat namespaces/playground/secrets/domain_prod/mydomain.com.crt',
                      key='cat namespaces/playground/secrets/domain_prod/mydomain.com.key') }}
```

```{.jinja title="templates/ingress.yml" hl_lines="8-9"}
kind: Ingress
apiVersion: networking.k8s.io/v1
metadata:
  ...
spec:
  ingressClassName: {{ ingress.className }}
  {% if ingress.get('tls', False) %}
  tls:
    {{ ingress.get('tls') | yaml(false) | indent(4) }}
  {% endif %}
  rules:
    ...
```

---

Find more examples in the [examples folder](https://github.com/awesome-it/adeploy/tree/master/examples) or see
the [`create_secret()`](functions.md#adeploy.common.jinja.globals.Handler.create_secret) for details.