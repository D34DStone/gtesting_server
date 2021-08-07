from contextvars import ContextVar


app_var = ContextVar("gtesting:app")
config_var = ContextVar("gtesting:config")
