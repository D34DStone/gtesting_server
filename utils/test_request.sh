#!/bin/bash

curl -X POST -F source=@sum.py localhost:8080/submit/$1
