# Oddpub API

This is a FastAPI application for processing PDF files using the oddpub functions: `pdf_convert`, `pdf_load`, and `open_data_search`.

## Project structure
services/
└── oddpub/
    ├── dockerfile
    ├── main.py
    ├── pyproject.toml
    └── README.md

## Requirements

- Python 3.11
- Docker (optional, for containerized deployment)

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nimh-dsst/dsst-etl.git
   cd services/oddpub
   ```

2. **Install dependencies**:
   If you are using Poetry:
   ```bash
   poetry install
   ```

3. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

## Usage

- Access the API at `http://localhost:8000/oddpub` to upload a PDF file and receive JSON output.

## Docker

To build and run the application using Docker:

1. **Build the Docker image**:
   ```bash
   docker build -t oddpub-api .
   ```

2. **Run the Docker container**:
   ```bash
   docker run -p 80:80 oddpub-api
   ```

## License

This project is licensed under the MIT License.