from colorama import Style, Fore

_skip_colors = False


def skip_colors(skip=True):
    global _skip_colors
    _skip_colors = skip


def blue(text):
    return f'{Fore.BLUE}{text}{Fore.RESET}' if not _skip_colors else text


def green(text):
    return f'{Fore.GREEN}{text}{Fore.RESET}' if not _skip_colors else text


def red(text):
    return f'{Fore.RED}{text}{Fore.RESET}' if not _skip_colors else text


def orange(text):
    return f'{Fore.YELLOW}{text}{Fore.RESET}' if not _skip_colors else text


def gray(text):
    # Fore.Gray is not readable in some terminals.
    return f'{Fore.RESET}{text}' if not _skip_colors else text


def bold(text):
    return f'{Style.BRIGHT}{text}{Style.NORMAL}' if not _skip_colors else text


def red_bold(text):
    return bold(red(text))


def green_bold(text):
    return bold(green(text))


def blue_bold(text):
    return bold(blue(text))


def orange_bold(text):
    return bold(orange(text))