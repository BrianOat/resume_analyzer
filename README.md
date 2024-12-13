# Resume Scanner

**Project Name**: AI-Powered Resume Analyzer and Job Matcher

**Description**: A platform where users can upload resumes and receive feedback on improving them, with personalized job recommendations based on resume content.

### Team Members & Contact Info
- **Charles Wang**: [cw44@njit.edu](mailto:cw44@njit.edu)
- **Haley Patel**: [hnp4@njit.edu](mailto:hnp4@njit.edu)
- **Jhanvi Pai**: [jp295@njit.edu](mailto:jp295@njit.edu)
- **Aaron Hsu**: [ah722@njit.edu](mailto:ah722@njit.edu)
- **Brian Ochoa**: [beo3@njit.edu](mailto:beo3@njit.edu)
- **Nick Fortis**: [nff4@njit.edu](mailto:nff4@njit.edu)

---

## High-Level Project Overview and Goals

**Project Goal**: Create an AI-driven platform that helps users improve their resumes and match them with job opportunities tailored to their skills and experiences.

### Features:
- Resume analysis and feedback.
- Personalized job recommendations based on content analysis.
- User-friendly interface for seamless interactions.

**Tech Stack**:
- **Backend**: FastAPI for handling resume uploads and feedback processing.
- **Frontend**: React for an intuitive user interface.
- **Communication**: An API to bridge the backend and NLP model.

**New Technology**:
- **Natural Language Processing (NLP)** for analyzing resume content.
- **Machine Learning** for matching job descriptions with skills and keywords found in resumes.

**Challenge Level**: Building an NLP pipeline and processing text data, while ensuring meaningful and user-friendly feedback, presents a challenging yet rewarding development experience.

---

## Instructions for Setting Up the Project Locally
- create .env file under /resume_scanner and include the following in the .env file
    ```
    PYTHONPATH=.
    secret="superSecret"
    algorithm="HS256" 
    ```

- docker-compose build
- docker-compose up
- **View Backend at http://localhost:8000**
- **View Frontend at http://localhost:3000**

## Run unit tests
### Run backend tests
- docker-compose build backend-tests
- docker-compose up backend-tests

### Run frontend tests
- docker-compose build frontend-tests
- docker-compose up frontend-tests
