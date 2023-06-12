import sys

_colors = {'black': '30', 'red': '31', 'green': '32', 'yellow': '33', 'blue':'34', 'pink':'35', 'cyan': '36', 'grey': '37'}

def colored(color: str, text: str) -> str:
    """ Takes in a color and a text and converts the text's foreground to an according color

    Args:
        * color(str): Available colors: black, red, green, yellow, blue, pink, cyan, grey
        * text(str): Text indended for recoloring

    Returns:
        * colored_text(str): The colored message.
    
    """
    if color.lower() in _colors.keys() == False:
        raise NameError('Unknown color.')
    colored_text = f'\x1b[{_colors[color]}m{text}\x1b[0m'
    return colored_text



