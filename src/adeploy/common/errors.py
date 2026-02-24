class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the user input."""
    pass


class RenderError(Error):
    """ Exception raised for errors in the renderer."""
    pass


class TestError(Error):
    """ Exception raised for errors in the tester."""
    pass


class DeployError(Error):
    """ Exception raised for errors in the tester."""
    pass


class WrongClusterError(Error):
    """ Exception raised if wrong cluster is targeted."""
    pass

if __name__ == '__main__':
    pass
