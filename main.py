from src.routes import routes
from src.application import create_app

def main(argv):
    return create_app(argv, routes)
