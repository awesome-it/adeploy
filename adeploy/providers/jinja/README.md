# Deployment Provider: Jinja

## Structure

```
/mydeployment/

/mydeployment/templates
/mydeployment/templates/service.yml
/mydeployment/templates/deployment.yml

/mydeployment/namespaces
/mydeployment/namespaces/mynamespace/prod.yml
/mydeployment/namespaces/mynamespace/test.yml

/defaults.yml
```

* A jinja deployment consists of a `templates` folder containing the manifest Jinja templates, 
* a `default.yml` file i.e. containing versions and
* a `namespaces` directory containing deployment configuration for different namespaces and releases.

### Templates

All files in the `templates` folder will be compiled 