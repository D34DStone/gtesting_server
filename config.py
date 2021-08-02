from pathlib import Path

class DefaultConfig:

    ROOT_DIR        = Path(__file__).parent.resolve()
    VAR_DIR         = ROOT_DIR / "var"
    TESTSETS_DIR    = VAR_DIR / "default" / "testsets"
    RUNNERS_DIR     = VAR_DIR / "default" / "runners"
    

class TestingConfig(DefaultConfig):
    
    TESTSETS_DIR    = DefaultConfig.VAR_DIR / "testing" / "testsets"
    RUNNERS_DIR     = DefaultConfig.VAR_DIR / "testing" / "runners"
    REDIS_HOST      = "localhost"
    REDIS_PORT      = 6379


class DevelopmentConfig(DefaultConfig):
    pass
