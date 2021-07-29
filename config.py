from pathlib import Path

class DefaultConfig:

    ROOT_DIR = Path(__file__).parent.resolve()
    TESTSETS_DIR = ROOT_DIR / "testsets"
    RUNNERS_DIR = ROOT_DIR / "runners"
    

class ConfigDevelopment(DefaultConfig):
    pass
