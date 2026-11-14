# Todo App

This application serves as a **Todo** manager, allowing users to efficiently keep track of their tasks.

This is a simple Todo application built using **FastAPI** for the backend and a static HTML front-end along with plain JavaScript for a seamless user experience.

## Features

The application includes several useful features:
- **View todos**: Display the list of tasks.
- **Add new todos**: Users can create new tasks easily.
- **Complete todos**: Simply click on a task to mark it as done.
- **Delete todos**: Remove tasks that are no longer needed.

## Installation

Follow these steps to set up the application on your local machine.

1. **Clone the repository**:
   You can use Git to clone the repository to your local machine.
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install the dependencies**: Make sure to install all the required packages.
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Once the setup is complete, you can run the application using the command below.

To run the application:
```bash
uvicorn app:app --reload
```

You can then access the application at `http://localhost:8000/` in your web browser.

## Testing

To ensure everything is getting tested properly:

To run the tests:
```bash
pytest
```