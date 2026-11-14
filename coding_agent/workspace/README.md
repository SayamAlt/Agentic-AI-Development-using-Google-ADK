# Todo App

This is a simple Todo application built using FastAPI and a static HTML front-end with plain JavaScript.

## Features
- View todos
- Add new todos
- Complete todos by clicking on them
- Delete todos

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the application:
```bash
uvicorn app:app --reload
```

Then you can access the application at `http://localhost:8000/`.

## Testing

To run the tests:
```bash
pytest
```