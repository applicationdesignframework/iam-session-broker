#!/bin/bash

set -o errexit
set -o verbose

targets=(service constants.py main.py)

# Find common security issues (https://bandit.readthedocs.io)
bandit --recursive "${targets[@]}"

# Python code formatter (https://black.readthedocs.io)
black --check --diff "${targets[@]}"

# Style guide enforcement (https://flake8.pycqa.org)
flake8 --config toolchain/config/.flake8 "${targets[@]}"

# Sort imports (https://pycqa.github.io/isort)
isort --src . --src service/api/app --settings-path toolchain/config/.isort.cfg --check --diff "${targets[@]}"

# Static type checker (https://mypy.readthedocs.io)
MYPYPATH="${PWD}" mypy --config-file toolchain/config/.mypy.ini --exclude service/api/app "${targets[@]}"
MYPYPATH="${PWD}/service/api/app" mypy --config-file toolchain/config/.mypy.ini --explicit-package-bases service/api/app

# Check for errors, enforce a coding standard, look for code smells (http://pylint.pycqa.org)
PYTHONPATH="${PWD}" pylint --rcfile toolchain/config/.pylintrc --ignore service/api/app "${targets[@]}"
PYTHONPATH="${PWD}/service/api/app" pylint --rcfile toolchain/config/.pylintrc service/api/app

# Report code complexity (https://radon.readthedocs.io)
radon mi "${targets[@]}"

# Check dependencies for security issues (https://pyup.io/safety)
safety check -r service/api/app/requirements.txt -r requirements.txt -r requirements-dev.txt

# Exit with non-zero status if code complexity exceeds thresholds (https://xenon.readthedocs.io)
xenon --max-absolute A --max-modules A --max-average A "${targets[@]}"
