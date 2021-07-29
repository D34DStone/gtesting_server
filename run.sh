#!/bin/bash
export APP_CONFIG=config:ConfigDevelopment
python -m aiohttp.web -H localhost -P 8080 src.main:get_app
