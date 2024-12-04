#!/bin/bash

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
elif [ -f .mockenv ]; then
    export $(cat .mockenv | grep -v '^#' | xargs)
fi

# Run alembic check
alembic check

# Store the exit code
exit_code=$?

# Return the alembic check exit code
exit $exit_code
