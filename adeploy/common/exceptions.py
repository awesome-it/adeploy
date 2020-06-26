class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the user input."""
    pass


class RenderError(Error):
    """ Exception raised for errors in the renderer."""
    pass


if __name__ == '__main__':
    pass