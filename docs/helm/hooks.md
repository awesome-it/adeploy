# Helm Deployment

## Hooks 
<!-- md:version 0.4.0 --><!-- md:provider Helm -->

During rendering the Helm deployment templates, `adeploy` will run hooks (i.e. executables scripts) from the `hooks`
directory after the Helm chart was downloaded and extracted.

The `hooks` directory is used as current working directory. 

The path to the extracted Helm chart will be passed as argument to the executed hook:

```{.bash}
./hooks/script.sh /mydeployment/build/helm/charts/<chartname>/
```

This can be used i.e. to patch Helm charts without touching the upstream repos for quick and dirty fixes:

``` {.shell title="hooks/patch.sh"}
--8<-- "examples/helm/002-hooks/hooks/patch.sh"
```

Now patches added to `hooks/patches.d` will be automatically applied to the Helm chart on each `adeploy -p helm render .`.

!!!tip

    The stdout of your hooks is supressed by default but printed out in error cases. If you want to see the stdout of 
    your hooks, run `adeploy` in verbose mode i.e. `adeploy -d -p helm render .`.