# Virtual Environment Setup Guide

## Required Dependencies for Endometriosis Detection ML Model

This guide explains how to set up your Python virtual environment to run the endometriosis detection application.

### Python Version
- **Python 3.10** (required for Railway compatibility)

### Step 1: Create Virtual Environment

```bash
# Navigate to your project directory
cd "c:\Users\Anietie Michael\Desktop\Endometriosis App"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Required Packages

All required packages are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Current Requirements.txt Contents

```
Flask==3.0.0
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.44
gunicorn==21.2.0
Werkzeug==3.0.1
Jinja2==3.1.2
click==8.1.7
itsdangerous==2.1.2
MarkupSafe==2.1.3
blinker==1.7.0
greenlet==3.2.4
numpy==1.26.4
scikit-learn==1.5.0
joblib==1.4.2
python-dateutil==2.8.2
pytz==2023.3
```

### Key Dependencies Explained

#### Web Framework
- **Flask** (3.0.0) - Web framework for the application
- **Flask-Login** (0.6.3) - User authentication management
- **Flask-SQLAlchemy** (3.1.1) - Database ORM

#### Database
- **SQLAlchemy** (2.0.44) - SQL toolkit and ORM
- **greenlet** (3.2.4) - Lightweight concurrency for SQLAlchemy

#### Machine Learning (for Model Prediction)
- **numpy** (1.26.4) - Numerical computing library
- **scikit-learn** (1.5.0) - ML library containing:
  - RandomForestClassifier
  - GradientBoostingClassifier
  - AdaBoostClassifier
  - SVC (Support Vector Machine)
  - LogisticRegression
  - StandardScaler
- **joblib** (1.4.2) - Serialization for sklearn models

#### Production Server
- **gunicorn** (21.2.0) - WSGI HTTP Server for production
- **Werkzeug** (3.0.1) - WSGI utilities

#### Utilities
- **Jinja2** (3.1.2) - Template engine
- **MarkupSafe** (2.1.3) - Safe string handling
- **click** (8.1.7) - CLI framework
- **python-dateutil** (2.8.2) - Date utilities
- **pytz** (2023.3) - Timezone support

### Step 3: Generate ML Model

The machine learning model must be generated before running the application:

```bash
python create_model.py
```

This will:
1. Load clinical training data (33 samples, 6 features)
2. Train 4 base learners:
   - Gradient Boosting Classifier (200 estimators)
   - Random Forest Classifier (200 estimators)
   - AdaBoost Classifier (200 estimators)
   - SVM with RBF kernel
3. Train meta-learner (Logistic Regression)
4. Save the ensemble model to `stacked_model.pkl`

### Step 4: Initialize Database

```bash
python run.py
```

This will:
1. Create the SQLite database
2. Initialize all tables
3. Create default admin user:
   - Email: admin@hospital.com
   - Password: admin123

### Step 5: Run the Application

```bash
python run.py
```

Access the application at: `http://localhost:5000`

## Troubleshooting

### Model Loading Error: "Can't get attribute 'AdvancedStackedEndometriosisModel'"
**Cause:** The model pickle file was saved with a custom class that can't be found.
**Solution:** Run `python create_model.py` to regenerate the model as a dictionary format.

### Missing Dependencies
If you get import errors, reinstall all packages:
```bash
pip install --upgrade -r requirements.txt
```

### Model Not Found
If you get "Model file not found at: stacked_model.pkl"
**Solution:** Run `python create_model.py` to create the model file.

### Database Lock Issues
If you get database locked errors:
```bash
rm instance/endometriosis.db
python run.py
```

## Model Features (6 Clinical Indicators)

The ML model accepts 6 binary features:
1. **Menstrual Irregularities** (0 or 1)
2. **Hormonal Abnormalities** (0 or 1)
3. **Infertility Issues** (0 or 1)
4. **Family History** (0 or 1)
5. **Ovulation Dysfunction** (0 or 1)
6. **Previous Surgery** (0 or 1)

## Model Performance

- Gradient Boosting: ~92% accuracy
- Random Forest: ~96% accuracy
- AdaBoost: ~89% accuracy
- SVM: 100% accuracy
- Meta-Learner: 100% accuracy

## Production Deployment (Railway)

For production on Railway:
1. Ensure `Procfile` points to `wsgi:app`
2. Set Python runtime to 3.10 in `runtime.txt`
3. Ensure `requirements.txt` is up to date
4. Commit and push to GitHub
5. Railway will auto-deploy and generate the model

## Support

For issues or questions about the setup:
1. Check that Python 3.10 is being used
2. Verify all packages in requirements.txt are installed
3. Ensure stacked_model.pkl exists and is readable
4. Check Flask debug logs for detailed error messages

---
**Last Updated:** January 2026
**Model Type:** Stacked Ensemble Classifier
**Application:** Endometriosis Detection Support System
