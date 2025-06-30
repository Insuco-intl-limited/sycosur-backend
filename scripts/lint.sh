#!/bin/bash

set -e

echo "Running isort..."
isort --check-only --diff .

echo "Running flake8..."
flake8 .

echo "Running black..."
black --check .

echo "All checks passed!"
