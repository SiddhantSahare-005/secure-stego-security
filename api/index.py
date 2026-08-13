import os
import sys


# Get the project root directory
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# Make sure the project root is available
# for Python imports
if ROOT_DIR not in sys.path:
    sys.path.insert(
        0,
        ROOT_DIR
    )


# Import Flask application
from app import app


# Explicitly tell Flask where the
# templates and static files are
app.template_folder = os.path.join(
    ROOT_DIR,
    "templates"
)

app.static_folder = os.path.join(
    ROOT_DIR,
    "static"
)
