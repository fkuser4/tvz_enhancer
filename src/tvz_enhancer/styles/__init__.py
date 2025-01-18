# styles/__init__.py

import os


def load_stylesheet():
    """
    Load and combine all QSS files into a single stylesheet.
    """
    stylesheet = ""
    styles_dir = os.path.join(os.path.dirname(__file__))
    for filename in sorted(os.listdir(styles_dir)):
        if filename.endswith(".qss"):
            filepath = os.path.join(styles_dir, filename)
            with open(filepath, "r") as f:
                stylesheet += f.read() + "\n"
    return stylesheet
