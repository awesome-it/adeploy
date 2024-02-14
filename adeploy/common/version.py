from importlib.metadata import version, PackageNotFoundError
from subprocess import Popen, PIPE


def get_package_version():
    try:
        return version('adeploy')
    except PackageNotFoundError:
        pass

    try:
        # Fallback to package name on test.pypi.org
        return version('adeploy_awesomeit')
    except PackageNotFoundError:
        pass


def call_git_describe(abbrev=4):
    try:
        p = Popen(['git', 'describe', '--tags', '--contains', '--abbrev=%d' % abbrev],
                  stdout=PIPE, stderr=PIPE, universal_newlines=True)
        p.stderr.close()
        line = p.stdout.readlines()[0]
        return line.strip()

    except:
        return None


def get_git_version(abbrev=4):
    # Try to get the current version using “git describe”.
    git_version = call_git_describe(abbrev)
    if git_version is None:
        print("Cannot find the version number!")
        return None

    # Remove potential git appendix
    return git_version.split('-')[0]
