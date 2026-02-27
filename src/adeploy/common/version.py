from importlib.metadata import version, PackageNotFoundError


def get_package_version():
    try:
        return version("adeploy")
    except PackageNotFoundError:
        pass

    try:
        # Fallback to package name on test.pypi.org
        return version("adeploy_awesomeit")
    except PackageNotFoundError:
        pass
