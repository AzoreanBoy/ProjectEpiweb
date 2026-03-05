# EPIWEB

A web-based application for prediction of epileptic seizures.

## Description

Epilepsy is a chronic neurological disorder that affects millions of people worldwide. Despite advances in antiepileptic drugs, about a third of patients continue to be unable to control seizures through them, which severely impacts their quality of life. Trustworthy seizure prediction could adjust epilepsy care by enabling preventative actions and reducing the psychological and physical burden of unpredictability.

This dissertation proposes EPIWEB, a web-based application designed to support seizure prediction research. Based on the EPILAB toolbox, EPIWEB presents a modern, modular, and scalable platform that enables advanced signal processing and machine learning workflows via a web browser. The application was developed using the Django framework, PostgreSQL, and asynchronous task management to handle computationally intensive processes. Its functionalities include EEG data management, preprocessing, feature extraction, data splitting, normalisation, feature selection and dimensionality reduction, classification, and result visualisation.

The results indicate that EPIWEB provides an intuitive and extensible environment that lowers technical barriers for researchers and clinicians while addressing the limitations of EPILAB, such as scalability and accessibility. Despite the current limited set of algorithms implemented, the modular architecture establishes a basis for future integration of advanced approaches, including deep learning techniques.

By combining usability, reproducibility, and methodological rigour, EPIWEB constitutes a step forward towards the development of a relevant seizure prediction system and provides a solid basis for continued research in biomedical signal processing and computational neurology.

## Technologies Used

- Django
- PostgreSQL
- Python
- Machine Learning libraries (scikit-learn, etc.)
- Signal Processing libraries

## Prerequisites

- Python 3.8+
- PostgreSQL database server
- Redis server
- Node.js and npm (for Tailwind CSS)

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up the database (PostgreSQL).
4. Run migrations: `python manage.py migrate`
5. Start the server: `python manage.py runserver`
6. Start a Redis Instance: `redis-server`
7. Start at least one celery worker: `celery -A EPIWEB worker --pool=solo -l info`

## Environment Configuration

Create a `.env` file in the project root with the following variables (copy from the existing `.env` file and modify as needed):

```
DJANGO_SECRET_KEY=your-secret-key-here
DB_NAME=epiwebDB
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
```

## Database Setup

EPIWEB uses two PostgreSQL databases:
- **Default database**: Stores application data (users, studies, etc.)
- **EPIDB database**: Stores EEG data and patient information - EPILEPSIAE DATABASE (European Funded Epilepsy Database)

Ensure both databases are created and accessible with the credentials in `.env`.
In case you do not have access to the EPILEPSIAE Database, remove the models and ajust the router.

## Features

- EEG data upload and management
- Signal preprocessing (filtering, windowing)
- Feature extraction from EEG signals
- Data normalization
- Feature selection and dimensionality reduction
- Machine learning classification for seizure prediction
- Asynchronous task processing
- User management and permissions
- Real-time notifications
- Data visualization

## Project Structure

- `EPIWEB/`: Django project settings
- `app/`: Main application with models, views, and templates
- `epilab/`: Signal processing and ML algorithms
- `routers/`: Database routing configuration
- `theme/`: Tailwind CSS configuration
- `data/`: Directory for uploaded data files

## Usage

1. Access the web interface at `http://localhost:8000`
2. Register/Login as a user
3. Upload EEG data files
4. Create and run processing studies
5. View results and visualizations

## Keywords

Epilepsy, Web App, Machine Learning, Signal Processing, Seizure Prediction

## Author

Pedro Henrique Rego Ferreira

Master's Dissertation in Biomedical Engineering, specialization in Clinical Informatics and Bioinformatics.

Advisors: Professor César Teixeira and Professor Nuno Laranjeiro

University of Coimbra, January 2026