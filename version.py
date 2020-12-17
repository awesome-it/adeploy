__all__ = ("get_git_version")

from subprocess import Popen, PIPE


def call_git_describe(abbrev=4):
    try:
        p = Popen(['git', 'describe', '--abbrev=%d' % abbrev],
                  stdout=PIPE, stderr=PIPE, universal_newlines=True)
        p.stderr.close()
        line = p.stdout.readlines()[0]
        return line.strip()

    except:
        return None


def get_git_version(abbrev=4):

    # Try to get the current version using “git describe”.
    version = call_git_describe(abbrev)
    if version is None:
        raise ValueError("Cannot find the version number!")

    return version


if __name__ == "__main__":
    print(get_git_version())