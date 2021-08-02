from .routes import routes
from .application import create_app

def get_app(argv):
    return create_app(routes, argv)
