# Endometriosis Detection Application

A comprehensive web-based diagnostic tool designed to assist healthcare professionals in detecting and managing endometriosis cases. This application integrates machine learning models with a user-friendly interface to provide preliminary diagnostic support based on patient symptoms and medical data.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [API Routes](#api-routes)
- [Machine Learning Model](#machine-learning-model)
- [Contributing](#contributing)
- [License](#license)

## Overview

Endometriosis is a chronic condition affecting millions of women worldwide, characterized by tissue similar to the uterine lining growing outside the uterus. Early detection and proper management are crucial for improving patient outcomes. This application leverages machine learning to provide doctors with data-driven diagnostic support, while maintaining a comprehensive patient management system.

### Purpose
- Assist healthcare professionals in early endometriosis detection
- Maintain detailed patient records and medical history
- Generate diagnostic reports based on ML model predictions
- Track patient progress and treatment outcomes
- Provide secure authentication and role-based access

## Features

### Core Functionality
- **Patient Management**: Create, manage, and track patient information
- **Symptom Assessment**: Comprehensive questionnaire for symptom evaluation
- **Diagnostic Detection**: Machine learning-based endometriosis risk assessment
- **Medical Records**: Maintain complete patient medical history and diagnoses
- **Report Generation**: Generate detailed diagnostic and treatment reports
- **Doctor Dashboard**: Centralized view of patient cases and diagnoses

### User Management
- Secure authentication system with login/registration
- Role-based access control (Doctor/Admin)
- User profile management and settings

### Data Security
- Password encryption and secure storage
- Database-backed persistent storage
- User session management

## Technology Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Machine Learning**: scikit-learn, pandas, numpy
- **Model Type**: Stacked ensemble model for classification

### Frontend
- **HTML5**: Semantic markup for accessibility
- **CSS3**: Responsive design with custom styling
- **JavaScript**: Client-side interactivity and form validation
- **Bootstrap**: Responsive UI components (optional)

### Python Dependencies
- Flask: Web framework
- Flask-SQLAlchemy: Database ORM
- Flask-Login: User authentication
- scikit-learn: Machine learning library
- pandas: Data manipulation
- numpy: Numerical computing
- Werkzeug: Utilities for WSGI applications

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/Animichael/endometriosis-detection.git
cd endometriosis-detection
```

### Step 2: Create Virtual Environment
```bash
# Using venv
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database
```bash
python create_model.py
```

This will create the SQLite database and initialize all tables.

## Configuration

### Application Settings
Edit `config.py` to configure application parameters:

```python
# Development/Production mode
DEBUG = True  # Set to False in production

# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/endometriosis.db'

# Secret key for session management
SECRET_KEY = 'your-secret-key-here'  # Change in production
```

### Environment Variables
Create a `.env` file in the project root (optional):
```
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key
```

## Usage

### Running the Application
```bash
python run.py
```

The application will start on `http://localhost:5000`

### Default Access
1. Navigate to `http://localhost:5000/login`
2. Register a new account or use existing credentials
3. Access the dashboard to manage patients and create diagnoses

### Workflow

#### For Doctors:
1. **Login**: Authenticate with your credentials
2. **Create Patient**: Add new patient information
3. **Assess Symptoms**: Fill out the diagnostic questionnaire
4. **Run Diagnosis**: Use the ML model to assess endometriosis risk
5. **Generate Report**: Create detailed diagnostic reports
6. **Track Progress**: Monitor patient cases and outcomes

#### Patient Management:
- View all patients in dashboard
- Edit patient information
- Access diagnosis records
- Generate comprehensive reports

## Project Structure

```
endometriosis-detection/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── run.py                          # Application entry point
├── create_model.py                 # Database initialization script
├── requirements.txt                # Python dependencies
├── stacked_model.pkl               # Trained ML model
│
├── database/
│   └── models.py                   # SQLAlchemy database models
│
├── routes/
│   ├── auth_routes.py              # Authentication endpoints
│   └── doctor_routes.py            # Doctor-specific endpoints
│
├── services/                       # Business logic layer
│
├── static/
│   ├── css/
│   │   └── style.css               # Application styles
│   ├── images/                     # UI images and assets
│   ├── js/                         # Client-side scripts
│   └── uploads/                    # User uploaded files
│
├── templates/                      # HTML templates
│   ├── base.html                   # Base template
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── dashboard.html              # Main dashboard
│   ├── create_patient.html         # Patient creation form
│   ├── manage_patients.html        # Patient management
│   ├── detect_endometriosis.html   # Diagnosis assessment
│   ├── diagnosis_records.html      # View diagnosis history
│   ├── generate_report.html        # Report generation
│   └── settings.html               # User settings
│
└── instance/
    └── endometriosis.db            # SQLite database file
```

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: User email
- `password_hash`: Encrypted password
- `full_name`: Full name
- `created_at`: Account creation timestamp

### Patients Table
- `id`: Primary key
- `doctor_id`: Foreign key (Doctor)
- `first_name`: Patient first name
- `last_name`: Patient last name
- `date_of_birth`: Patient DOB
- `gender`: Patient gender
- `medical_history`: Previous medical conditions
- `current_medications`: Active medications
- `created_at`: Record creation date

### Diagnoses Table
- `id`: Primary key
- `patient_id`: Foreign key (Patient)
- `doctor_id`: Foreign key (Doctor)
- `symptoms`: Assessed symptoms
- `ml_prediction`: Model prediction probability
- `doctor_diagnosis`: Doctor's diagnosis
- `recommendations`: Treatment recommendations
- `created_at`: Diagnosis date

## API Routes

### Authentication
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /register` - Registration page
- `POST /register` - Create new account
- `GET /logout` - Logout user

### Doctor Routes
- `GET /dashboard` - Main dashboard
- `GET /create_patient` - Patient creation form
- `POST /create_patient` - Save new patient
- `GET /manage_patients` - List all patients
- `GET /detect_endometriosis` - Diagnosis form
- `POST /detect_endometriosis` - Process diagnosis
- `GET /diagnosis_records` - View diagnosis history
- `GET /generate_report/<id>` - Generate patient report
- `GET /settings` - User settings page

## Machine Learning Model

### Model Type
Stacked Ensemble Classifier combining multiple algorithms for robust predictions

### Input Features
The model analyzes various clinical symptoms and patient data:
- Pelvic pain characteristics
- Menstrual irregularities
- Fertility history
- Imaging findings
- Laboratory markers

### Output
- **Risk Probability**: 0-1 scale indicating endometriosis likelihood
- **Recommendation**: Suggested follow-up actions

### Model Performance
The trained model (`stacked_model.pkl`) is evaluated on comprehensive clinical datasets and provides reliable preliminary diagnostic support.

**Note**: Model predictions should always be reviewed by qualified healthcare professionals.

## Responsive Design

The application features a fully responsive design that works seamlessly across:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Tablet devices
- Mobile phones

See [RESPONSIVE_DESIGN_UPDATES.md](RESPONSIVE_DESIGN_UPDATES.md) for detailed responsive design implementation details.

## Security Considerations

### Implemented Security Measures
- Password hashing using werkzeug
- CSRF protection for forms
- SQL injection prevention via SQLAlchemy ORM
- User session management
- Secure cookie handling

### Recommendations for Production
1. Change SECRET_KEY in config.py
2. Use environment variables for sensitive data
3. Enable HTTPS/SSL
4. Implement database backups
5. Set up proper logging and monitoring
6. Use a production-grade server (Gunicorn, uWSGI)
7. Implement rate limiting for API endpoints

## Development and Testing

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Lint code
pylint routes/
pylint database/

# Format code
black .
```

## Troubleshooting

### Common Issues

**Database not initializing**
```bash
# Delete existing database and reinitialize
rm instance/endometriosis.db
python create_model.py
```

**Import errors**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

**Port already in use**
```bash
# Run on different port
python run.py --port 5001
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Standards
- Follow PEP 8 Python style guide
- Add docstrings to functions
- Write meaningful commit messages
- Test new features thoroughly

## Disclaimer

**Medical Disclaimer**: This application is designed as a diagnostic support tool and should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical concerns. The machine learning model provides preliminary risk assessment only.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact & Support

For questions, bug reports, or feature requests, please:
- Open an issue on GitHub
- Contact the development team

## Acknowledgments

- Built with Flask and scikit-learn
- Inspired by real-world clinical diagnostic processes
- Dedicated to improving women's health outcomes

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Maintainer**: Anietie Michael
