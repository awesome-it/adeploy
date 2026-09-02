class Error(Exception):
    """Base class for exceptions in this module."""


class InputError(Error):
    """Exception raised for errors in the user input."""


class RenderError(Error):
    """Exception raised for errors in the renderer."""


class TestError(Error):
    """Exception raised for errors in the tester."""


class DeployError(Error):
    """Exception raised for errors in the tester."""


class WrongClusterError(Error):
    """Exception raised if wrong cluster is targeted."""


if __name__ == "__main__":
    pass
