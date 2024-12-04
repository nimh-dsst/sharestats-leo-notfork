#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "Loading variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
elif [ -f .mockenv ]; then
    echo "Loading variables from .mockenv file..."
    export $(cat .mockenv | grep -v '^#' | xargs)
else
    echo "Warning: Neither .env nor .mockenv file found!"
fi

# Show relevant database environment variables
echo "=== Database Environment Variables ==="
echo "POSTGRES_USER: ${POSTGRES_USER:-not set}"
echo "POSTGRES_DB: ${POSTGRES_DB:-not set}"
echo "POSTGRES_HOST: ${POSTGRES_HOST:-not set}"
echo "POSTGRES_PORT: ${POSTGRES_PORT:-not set}"
echo "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-(hidden)}"
echo "=================================="

# Run alembic check
echo "Running alembic check..."
alembic check

# Store the exit code
exit_code=$?

# Show the result
if [ $exit_code -eq 0 ]; then
    echo "✅ Alembic check passed successfully"
else
    echo "❌ Alembic check failed with exit code $exit_code"
fi

# Return the alembic check exit code
exit $exit_code
