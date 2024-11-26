## Instructions for Setting Up the Project Locally
- create .env file under /resume_scanner and include the following in the .env file
    ```
    PYTHONPATH=.
    secret="superSecret"
    algorithm="HS256" 
    ```

- docker-compose build
- docker-compose up
- **View Backend at http://127.0.0.1:8000**
- **View Frontend at http://127.0.0.1:3000**

## Run unit tests
### Run backend tests
- docker-compose build backend-tests
- docker-compose up backend-tests

### Run frontend tests
- docker-compose build frontend-tests
- docker-compose up frontend-tests
