# Secrets

<!-- --8<-- [start:summary] -->
`adeploy` can create secrets for you in various ways:

* Retrieve secrets from the [supported secret Sources](#retrieving-sensitive-data) like gopass or shell commands
* Retrieve or auto-generate (rotate) arbitrary secrets using bash commands

Since `adeploy` will create non-existing secrets but won't touch existing secrets[^1], a very simple but effective concept
of secret management can be established and `adeploy` can be used to automate everything while excluding secret handling 
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

Since the first part requires to retrieve sensitive data i.e. passwords, tokens or certificates, this must be executed
by a trusted person and should never be executed by an automation. In most cases, this part will be executed on the
local machine by the author of the `adeploy` deployment template. This person also needs access to a local password
store (i.e. [Gopass](https://www.gopass.pw/)) or other compatible password source that provide a command line interface.

!!!warning "Deployment with creating or updating secrets"
    If secrets are missing on the destination cluster, `adeploy` tries to create them and thus assumes a 
    [deployment including sensitive information](#deployment-with-creating-or-updating-secrets).

### Deployment without handling secrets

The deployment part that is not touching the secrets does not need to be executed by a person having access to sensitive
data and thus is particularly suitable for automation. This includes changing all resources excluding secrets which is 
the most common case when changing k8s deployments.

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

`adeploy` supports different ways to retrieve (or generate) the sensitive data to create the secrets.
All supported sources of secret data are accessed by a corresponding jinja function which returns a `SecretsProvider` 
object. These objects are passed to a secret creation function - e.g. `create_secret()`. 
`SecretsProvider` objects can be rendered in order to test the secret retrieval - this implies a 
[Deployment with creating or updating secrets](#deployment-with-creating-or-updating-secrets) and must therefore not 
be used in a CI/CD pipeline. Best practice is to use the retrieval function as an argument to `create_secret()`

### Gopass

Secrets can be taken from [Gopass password store](https://www.gopass.pw/) that is properly installed
and setup on the local machine that will run the [trusted deployment](#deployment-with-creating-or-updating-secrets).

Gopass secrets are accessed using the [`from_gopass(paht="...")`](/common/functions/#adeploy.common.jinja.globals.Handler.from_gopass) function.


The path to the password of the Gopass repo must be specified in the `from_gopass()` function:
<!-- --8<-- [start:example-gopass] -->
```{.jinja}

{# Debug, print the secret value #}
{{ from_gopass(path="/my/path") }}

{# Create a secret with the secret value and use it in a deployment #}
my_deployment:
  config:
    secretName: {{ create_secret(my_secret=from_gopass(path="/my/path")) }}
    secretKey: my_secret
```

This will create a secret containing with a key `my_secret` and value from `gopass cat /my/path`.
<!-- --8<-- [end:example-gopass] -->

A list of different Gopass repos can be specified in `--gopass-repo` or as comma separated list in the environment 
variable `ADEPLOY_GOPASS_REPOS`. 

!!!note "Example"

    If `ADEPLOY_GOPASS_REPOS=a,b` is set and `from>_gopass(path='/my/path')` is used, the following 
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

### Random password
`adeploy` supports the generation of random passwords using the [`random_string()`](/common/functions/#adeploy.common.jinja.globals.Handler.random_string) function. This function takes a optional length

This function creates a random password. During a run of adeploy the password won't change,
subsequent runs will update the password.

<!-- --8<-- [start:example-random-password] -->
```{.jinja}

{# Debug, print the secret value #}
{{ random_string(length=64) }}

{# Create a secret with the secret value and use it in a deployment #}
my_deployment:
  config:
    secretName: {{ create_secret(my_secret=random_string()) }}
    secretKey: my_secret
```

### Custom Password Command

You can use custom commands i.e. bash scripts or other password managers that provide a compatible command line
interface using the [`from_shell_command()`](/common/functions/#adeploy.common.jinja.globals.Handler.from_shell_command)
function as follows:

```{.jinja}

{# Debug, print the secret value #}
{{ from_shell_command(cmd="cat /all_my_passwords | head -n 1") }}

{# Create a secret with the secret value and use it in a deployment #}
my_deployment:
  config:
    secretName: {{ create_secret(my_secret=from_shell_command(cmd="cat /all_my_passwords | head -n 1")) }}
    secretKey: my_secret
```

This will create a secret with a key `my_key` and the stdout of the custom command as value. 

!!!note

    Note that the command string is used to create a unique secret name. Don't use this function to call a 
    random-password script for auto-rotation - use the `random_string()` function instead.

!!!note

    Note that you can use environment variables (i.e. `$SOME_ENV_VARS`) in your command which are taken from the executing
    shells environment.

!!!warning

    Custom commands are a very powerful feature. Be aware that the command is executed on the local machine and this
    can be a security risk. Always use this feature with caution and only with trusted commands. If you're using this
    to regularly access a currently unsupported secret source, consider to implement a new secret provider.

### Plaintext Secrets

!!!danger

    You will have sensitive data in your `defaults.yml` or in your namespace/release configuration which might be
    uploaded to a Git repo or similar. This is strongly discouraged!

To specify a secret value directly in your configuration, use the from_plaintext() function.:

```{.jinja}
myjinjatemplate:
  config:
    secretName: {{ create_secret(secret_name, my_key=from_plaintext("my_secret_value")) }}
    secretKey: my_key
```



## Examples

### Create Image Pull Secret

<!-- --8<-- [start:example-docker] -->
```{.jinja title="namespaces/playground/prod.yml"}
secrets:
  registry: {{ create_docker_registry_secret(
                   server='registry.awesome-it.de',
                   username='sa_registry_ro',
                   password=from_shell_command(
                        'cat namespaces/playground/secrets/my_secret_prod'
                   )
               ) }}
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
<!-- --8<-- [end:example-docker] -->

### Create TLS Secrets for Ingress

<!-- --8<-- [start:example-tls] -->
```{.jinja title="namespaces/playground/prod.yml"}
ingress:
  className: external
  tls:
    - hosts:
        - mydomain.com
      secretName: {{ create_tls_secret(
                      custom_cmd=True,
                      cert=from_shell_command(
                        'cat namespaces/playground/secrets/domain_prod/mydomain.com.crt'
                      ),
                      key=from_shell_command(
                        'cat namespaces/playground/secrets/domain_prod/mydomain.com.key'
                      )
                    ) }}
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
<!-- --8<-- [end:example-tls] -->

---

Find more examples in the [examples folder](https://github.com/awesome-it/adeploy/tree/master/examples) or see
the [`create_secret()`](functions.md#adeploy.common.jinja.globals.Handler.create_secret) for details.