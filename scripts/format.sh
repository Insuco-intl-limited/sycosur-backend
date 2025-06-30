#!/bin/bash

set -e

echo "Running isort..."
isort .

echo "Running black..."
black .

echo "Code formatting complete!"
