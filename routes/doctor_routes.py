from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from database.models import Patient, Prediction, DiagnosisRecord
from datetime import datetime
import pickle
import numpy as np
import os

doctor = Blueprint("doctor", __name__)

# ===================== ML MODEL LOADING (DICTIONARY FORMAT) =====================

# Get project root directory (where run.py is located)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(BASE_DIR, "stacked_model.pkl")

stacked_model = None
model_loaded = False
print(MODEL_PATH)


def load_ml_model():
    global stacked_model, model_loaded
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                stacked_model = pickle.load(f)
            model_loaded = True
            print(f"✅ ML model loaded successfully from: {MODEL_PATH}")
        else:
            print(f"❌ Model file not found at: {MODEL_PATH}")
            model_loaded = False
    except Exception as e:
        print(f"❌ Error loading ML model: {str(e)}")
        model_loaded = False


def predict_endometriosis(features_array):
    """
    Make prediction using the stacked ensemble model
    features_array: np.array of shape (1, 6) or (n, 6)
    Returns: dict with predictions and confidence
    """
    global stacked_model, model_loaded

    if not model_loaded or stacked_model is None:
        load_ml_model()
        return None

    try:
        # Scale the input features
        X_scaled = stacked_model["scaler"].transform(features_array)

        # Get predictions from all base models
        gb_proba = stacked_model["gb_model"].predict_proba(X_scaled)
        rf_proba = stacked_model["rf_model"].predict_proba(X_scaled)
        ada_proba = stacked_model["ada_model"].predict_proba(X_scaled)
        svm_proba = stacked_model["svm_model"].predict_proba(X_scaled)

        # Stack predictions for meta-learner
        meta_features = np.hstack([gb_proba, rf_proba, ada_proba, svm_proba])

        # Get final prediction and probability
        final_proba = stacked_model["meta_learner"].predict_proba(meta_features)
        final_pred = stacked_model["meta_learner"].predict(meta_features)

        # Format results
        results = []
        for i in range(len(final_pred)):
            prob_no_endo = float(final_proba[i][0]) * 100
            prob_endo = float(final_proba[i][1]) * 100
            confidence = max(final_proba[i]) * 100

            # Risk level based on probability
            if prob_endo >= 70:
                risk_level = "HIGH"
            elif prob_endo >= 40:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            results.append(
                {
                    "prediction": int(final_pred[i]),
                    "probability_no_endo": prob_no_endo,
                    "probability_endo": prob_endo,
                    "confidence": confidence,
                    "risk_level": risk_level,
                }
            )

        return results[0] if len(results) == 1 else results

    except Exception as e:
        print(f"❌ Error during prediction: {str(e)}")
        return None


# Load model when module is imported
load_ml_model()

# ===================== ROUTES (UNCHANGED) =====================


@doctor.route("/base")
@login_required
def base():
    return render_template("dashboard.html")


@doctor.route("/dashboard")
@login_required
def dashboard():
    # Total patients created by current doctor
    total_patients = Patient.query.filter_by(created_by=current_user.id).count()

    # Total diagnosis records
    total_diagnosis = DiagnosisRecord.query.filter_by(doctor_id=current_user.id).count()

    # Positive diagnosis (diagnosis_text contains "Detected")
    total_positive = DiagnosisRecord.query.filter(
        DiagnosisRecord.doctor_id == current_user.id,
        DiagnosisRecord.diagnosis_text.contains("Detected"),
    ).count()

    # Negative diagnosis (diagnosis_text contains "Not Detected")
    total_negative = DiagnosisRecord.query.filter(
        DiagnosisRecord.doctor_id == current_user.id,
        DiagnosisRecord.diagnosis_text.contains("Not Detected"),
    ).count()

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_diagnosis=total_diagnosis,
        total_positive=total_positive,
        total_negative=total_negative,
    )


@doctor.route("/create-patient", methods=["GET", "POST"])
@login_required
def create_patient():
    if request.method == "POST":
        try:
            patient = Patient(
                full_name=request.form.get("full_name"),
                age=int(request.form.get("age")),
                gender=request.form.get("gender"),
                contact=request.form.get("contact"),
                email=request.form.get("email"),
                address=request.form.get("address"),
                medical_history=request.form.get("medical_history"),
                created_by=current_user.id,
            )

            db.session.add(patient)
            db.session.commit()

            flash(
                f"Patient {patient.full_name} created successfully with ID: {patient.id}",
                "success",
            )
            return redirect(url_for("doctor.manage_patients"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating patient: {str(e)}", "danger")
            return redirect(url_for("doctor.create_patient"))

    return render_template("create_patient.html")


@doctor.route("/manage-patients")
@login_required
def manage_patients():
    patients = (
        Patient.query.filter_by(created_by=current_user.id)
        .order_by(Patient.created_at.desc())
        .all()
    )
    return render_template("manage_patients.html", patients=patients)


@doctor.route("/detect-endometriosis")
@login_required
def detect_endometriosis():
    patients = Patient.query.filter_by(created_by=current_user.id).all()
    return render_template("detect_endometriosis.html", patients=patients)


@doctor.route("/api/patient/<patient_id>", methods=["GET"])
@login_required
def get_patient_api(patient_id):
    try:
        patient = Patient.query.filter_by(
            id=patient_id, created_by=current_user.id
        ).first()

        if not patient:
            return jsonify({"success": False, "message": "Patient not found"}), 404

        return jsonify(
            {
                "success": True,
                "patient": {
                    "id": patient.id,
                    "full_name": patient.full_name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "contact": patient.contact,
                    "email": patient.email,
                    "address": patient.address,
                    "medical_history": patient.medical_history,
                },
            }
        )
    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Error fetching patient: {str(e)}"}
        ), 500


@doctor.route("/api/patient/<patient_id>", methods=["PUT"])
@login_required
def update_patient_api(patient_id):
    try:
        patient = Patient.query.filter_by(
            id=patient_id, created_by=current_user.id
        ).first()

        if not patient:
            return jsonify({"success": False, "message": "Patient not found"}), 404

        data = request.get_json()

        # Update patient fields
        if "full_name" in data:
            patient.full_name = data["full_name"]
        if "age" in data:
            patient.age = data["age"]
        if "gender" in data:
            patient.gender = data["gender"]
        if "contact" in data:
            patient.contact = data["contact"]
        if "email" in data:
            patient.email = data["email"]
        if "address" in data:
            patient.address = data["address"]
        if "medical_history" in data:
            patient.medical_history = data["medical_history"]

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Patient updated successfully",
                "patient": {
                    "id": patient.id,
                    "full_name": patient.full_name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "contact": patient.contact,
                    "email": patient.email,
                    "address": patient.address,
                    "medical_history": patient.medical_history,
                },
            }
        )
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {"success": False, "message": f"Error updating patient: {str(e)}"}
        ), 500


@doctor.route("/api/patient/<patient_id>", methods=["DELETE"])
@login_required
def delete_patient_api(patient_id):
    try:
        patient = Patient.query.filter_by(
            id=patient_id, created_by=current_user.id
        ).first()

        if not patient:
            return jsonify({"success": False, "message": "Patient not found"}), 404

        # Delete all related diagnosis records and predictions
        DiagnosisRecord.query.filter_by(patient_id=patient_id).delete()
        Prediction.query.filter_by(patient_id=patient_id).delete()

        # Delete patient
        db.session.delete(patient)
        db.session.commit()

        return jsonify({"success": True, "message": "Patient deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify(
            {"success": False, "message": f"Error deleting patient: {str(e)}"}
        ), 500


@doctor.route("/diagnosis-records")
@login_required
def diagnosis_records():
    predictions = (
        Prediction.query.filter_by(doctor_id=current_user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    return render_template("diagnosis_records.html", predictions=predictions)


@doctor.route("/predict-endometriosis", methods=["POST"])
@login_required
def predict_endometriosis():
    try:
        if not model_loaded or stacked_model is None:
            return jsonify(
                {
                    "success": False,
                    "message": "ML model not loaded. Please check model file.",
                }
            ), 500

        patient_id = request.form.get("patient_id")
        menstrual_irregularity = int(request.form.get("menstrual_irregularity", 0))
        hormone_level = int(request.form.get("hormone_level", 0))
        infertility = int(request.form.get("infertility", 0))
        family_history = int(request.form.get("family_history", 0))
        ovulation_dysfunction = int(request.form.get("ovulation_dysfunction", 0))
        prior_surgery = int(request.form.get("prior_surgery", 0))

        patient = Patient.query.filter_by(
            id=patient_id, created_by=current_user.id
        ).first()

        if not patient:
            return jsonify(
                {"success": False, "message": "Patient not found or access denied"}
            ), 404

        input_data = np.array(
            [
                [
                    menstrual_irregularity,
                    hormone_level,
                    infertility,
                    family_history,
                    ovulation_dysfunction,
                    prior_surgery,
                ]
            ]
        )

        # Make predictions using the ensemble model
        X_scaled = stacked_model["scaler"].transform(input_data)

        # Get predictions from all base models
        gb_pred = stacked_model["gb_model"].predict_proba(X_scaled)
        rf_pred = stacked_model["rf_model"].predict_proba(X_scaled)
        ada_pred = stacked_model["ada_model"].predict_proba(X_scaled)
        svm_pred = stacked_model["svm_model"].predict_proba(X_scaled)

        # Stack predictions for meta-learner
        meta_features = np.hstack([gb_pred, rf_pred, ada_pred, svm_pred])

        # Final prediction from meta-learner
        prediction = stacked_model["meta_learner"].predict(meta_features)[0]
        probabilities = stacked_model["meta_learner"].predict_proba(meta_features)[0]

        prob_endo = probabilities[1] * 100
        prob_no_endo = probabilities[0] * 100

        diagnosis = (
            "Endometriosis Detected"
            if prob_endo >= 50
            else "Endometriosis Not Detected"
        )

        new_prediction = Prediction(
            patient_id=patient_id,
            doctor_id=current_user.id,
            menstrual_irregularity=menstrual_irregularity,
            hormone_level=hormone_level,
            infertility=infertility,
            family_history=family_history,
            ovulation_dysfunction=ovulation_dysfunction,
            prior_surgery=prior_surgery,
            prediction_result=int(prediction),
            probability_no_endo=float(prob_no_endo),
            probability_endo=float(prob_endo),
            diagnosis=diagnosis,
            confidence=float(max(prob_endo, prob_no_endo)),
        )

        db.session.add(new_prediction)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "prediction": {
                    "prediction_id": new_prediction.id,
                    "result": int(prediction),
                    "probability_no_endo": prob_no_endo,
                    "probability_endo": prob_endo,
                    "diagnosis": diagnosis,
                    "confidence": float(max(prob_endo, prob_no_endo)),
                },
            }
        )

    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify(
            {"success": False, "message": f"Prediction failed: {str(e)}"}
        ), 500


# ===================== DIAGNOSIS RECORD ENDPOINTS =====================


@doctor.route("/api/save-diagnosis", methods=["POST"])
@login_required
def save_diagnosis():
    """Save diagnosis record to database"""
    try:
        from database.models import DiagnosisRecord

        data = request.get_json()

        patient_id = data.get("patient_id")
        prediction_id = data.get("prediction_id")
        diagnosis_text = data.get("diagnosis")
        confidence_score = data.get("confidence")
        probability_positive = data.get("probability_endo")
        probability_negative = data.get("probability_no_endo")
        clinical_notes = data.get("clinical_notes", "")
        recommendations = data.get("recommendations", "")

        # Create new diagnosis record
        new_diagnosis = DiagnosisRecord(
            prediction_id=prediction_id,
            patient_id=patient_id,
            doctor_id=current_user.id,
            diagnosis_text=diagnosis_text,
            confidence_score=confidence_score,
            probability_positive=probability_positive,
            probability_negative=probability_negative,
            clinical_notes=clinical_notes,
            recommendations=recommendations,
            status="Active",
        )

        db.session.add(new_diagnosis)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Diagnosis saved successfully",
                "diagnosis_id": new_diagnosis.id,
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Save diagnosis error: {str(e)}")
        return jsonify(
            {"success": False, "message": f"Failed to save diagnosis: {str(e)}"}
        ), 500


@doctor.route("/api/diagnosis-records", methods=["GET"])
@login_required
def get_diagnosis_records():
    """Get all diagnosis records for current doctor"""
    try:
        from database.models import DiagnosisRecord
        from sqlalchemy.orm import joinedload

        records = (
            DiagnosisRecord.query.options(
                joinedload(DiagnosisRecord.patient), joinedload(DiagnosisRecord.doctor)
            )
            .filter_by(doctor_id=current_user.id)
            .order_by(DiagnosisRecord.created_at.desc())
            .all()
        )

        return jsonify(
            {"success": True, "records": [record.to_dict() for record in records]}
        )

    except Exception as e:
        print(f"Get diagnosis records error: {str(e)}")
        return jsonify(
            {"success": False, "message": f"Failed to retrieve records: {str(e)}"}
        ), 500


@doctor.route("/api/diagnosis/<int:diagnosis_id>", methods=["GET"])
@login_required
def get_diagnosis(diagnosis_id):
    """Get single diagnosis record"""
    try:
        from database.models import DiagnosisRecord
        from sqlalchemy.orm import joinedload

        diagnosis = (
            DiagnosisRecord.query.options(
                joinedload(DiagnosisRecord.patient), joinedload(DiagnosisRecord.doctor)
            )
            .filter_by(id=diagnosis_id, doctor_id=current_user.id)
            .first()
        )

        if not diagnosis:
            return jsonify(
                {"success": False, "message": "Diagnosis record not found"}
            ), 404

        return jsonify({"success": True, "diagnosis": diagnosis.to_dict()})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@doctor.route("/api/diagnosis/<int:diagnosis_id>", methods=["PUT"])
@login_required
def update_diagnosis(diagnosis_id):
    """Update diagnosis record"""
    try:
        from database.models import DiagnosisRecord

        diagnosis = DiagnosisRecord.query.filter_by(
            id=diagnosis_id, doctor_id=current_user.id
        ).first()

        if not diagnosis:
            return jsonify(
                {"success": False, "message": "Diagnosis record not found"}
            ), 404

        data = request.get_json()

        if "clinical_notes" in data:
            diagnosis.clinical_notes = data["clinical_notes"]
        if "recommendations" in data:
            diagnosis.recommendations = data["recommendations"]
        if "status" in data:
            diagnosis.status = data["status"]

        diagnosis.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Diagnosis updated successfully",
                "diagnosis": diagnosis.to_dict(),
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@doctor.route("/api/diagnosis/<int:diagnosis_id>", methods=["DELETE"])
@login_required
def delete_diagnosis(diagnosis_id):
    """Delete diagnosis record"""
    try:
        from database.models import DiagnosisRecord

        diagnosis = DiagnosisRecord.query.filter_by(
            id=diagnosis_id, doctor_id=current_user.id
        ).first()

        if not diagnosis:
            return jsonify(
                {"success": False, "message": "Diagnosis record not found"}
            ), 404

        db.session.delete(diagnosis)
        db.session.commit()

        return jsonify({"success": True, "message": "Diagnosis deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@doctor.route("/diagnosis-records")
@login_required
def diagnosis_records_page():
    """Render diagnosis records page"""
    return render_template("diagnosis_records.html")


# ===================== REPORT GENERATION ENDPOINTS =====================


@doctor.route("/api/report-data", methods=["POST"])
@login_required
def get_report_data():
    """Get report data based on filters"""
    try:
        from database.models import DiagnosisRecord
        from datetime import datetime, timedelta
        from sqlalchemy.orm import joinedload

        data = request.get_json()
        report_type = data.get("report_type")  # monthly, weekly, custom
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Build query with eager loading
        query = DiagnosisRecord.query.options(
            joinedload(DiagnosisRecord.patient), joinedload(DiagnosisRecord.doctor)
        ).filter_by(doctor_id=current_user.id)

        # Apply date filters
        if report_type == "monthly":
            # Last 30 days
            start_date = datetime.utcnow() - timedelta(days=30)
            query = query.filter(DiagnosisRecord.created_at >= start_date)
        elif report_type == "weekly":
            # Last 7 days
            start_date = datetime.utcnow() - timedelta(days=7)
            query = query.filter(DiagnosisRecord.created_at >= start_date)
        elif report_type == "custom" and start_date and end_date:
            # Custom date range
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(DiagnosisRecord.created_at >= start)
            query = query.filter(DiagnosisRecord.created_at <= end)

        records = query.order_by(DiagnosisRecord.created_at.desc()).all()

        # Calculate statistics
        total_diagnoses = len(records)
        positive_count = sum(1 for r in records if "Detected" in r.diagnosis_text)
        negative_count = total_diagnoses - positive_count
        avg_confidence = (
            sum(r.confidence_score for r in records) / total_diagnoses
            if total_diagnoses > 0
            else 0
        )

        # Group by status
        status_breakdown = {
            "active": sum(1 for r in records if r.status == "Active"),
            "reviewed": sum(1 for r in records if r.status == "Reviewed"),
            "archived": sum(1 for r in records if r.status == "Archived"),
        }

        return jsonify(
            {
                "success": True,
                "records": [r.to_dict() for r in records],
                "statistics": {
                    "total_diagnoses": total_diagnoses,
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "positive_percentage": (positive_count / total_diagnoses * 100)
                    if total_diagnoses > 0
                    else 0,
                    "negative_percentage": (negative_count / total_diagnoses * 100)
                    if total_diagnoses > 0
                    else 0,
                    "average_confidence": round(avg_confidence, 2),
                    "status_breakdown": status_breakdown,
                },
            }
        )

    except Exception as e:
        print(f"Report data error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@doctor.route("/api/export-csv", methods=["POST"])
@login_required
def export_csv():
    """Export report as CSV"""
    try:
        from database.models import DiagnosisRecord
        from datetime import datetime, timedelta
        import csv
        import io
        from flask import make_response
        from sqlalchemy.orm import joinedload

        data = request.get_json()
        report_type = data.get("report_type")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Build query with eager loading
        query = DiagnosisRecord.query.options(
            joinedload(DiagnosisRecord.patient)
        ).filter_by(doctor_id=current_user.id)

        if report_type == "monthly":
            start_date = datetime.utcnow() - timedelta(days=30)
            query = query.filter(DiagnosisRecord.created_at >= start_date)
        elif report_type == "weekly":
            start_date = datetime.utcnow() - timedelta(days=7)
            query = query.filter(DiagnosisRecord.created_at >= start_date)
        elif report_type == "custom" and start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(DiagnosisRecord.created_at >= start)
            query = query.filter(DiagnosisRecord.created_at <= end)

        records = query.order_by(DiagnosisRecord.created_at.desc()).all()

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(
            [
                "Patient Name",
                "Patient ID",
                "Diagnosis",
                "Confidence (%)",
                "Positive Prob (%)",
                "Negative Prob (%)",
                "Status",
                "Created Date",
            ]
        )

        # Write data
        for record in records:
            writer.writerow(
                [
                    record.patient.full_name if record.patient else "",
                    record.patient_id,
                    record.diagnosis_text,
                    f"{record.confidence_score:.2f}",
                    f"{record.probability_positive * 100:.2f}",
                    f"{record.probability_negative * 100:.2f}",
                    record.status,
                    record.created_at,
                ]
            )

        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = (
            f"attachment; filename=diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        response.headers["Content-Type"] = "text/csv"

        return response

    except Exception as e:
        print(f"CSV export error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@doctor.route("/api/export-excel", methods=["POST"])
@login_required
def export_excel():
    """Export report as Excel"""
    try:
        from database.models import DiagnosisRecord
        from datetime import datetime, timedelta
        from flask import make_response
        from sqlalchemy.orm import joinedload

        # Try to import openpyxl, if not available use xlsxwriter
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        except ImportError:
            return jsonify(
                {
                    "success": False,
                    "message": "Excel export requires openpyxl. Install with: pip install openpyxl",
                }
            ), 400

        data = request.get_json()
        report_type = data.get("report_type")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Build query with eager loading
        query = DiagnosisRecord.query.options(
            joinedload(DiagnosisRecord.patient)
        ).filter_by(doctor_id=current_user.id)

        if report_type == "monthly":
            start_date = datetime.utcnow() - timedelta(days=30)
            query = query.filter(DiagnosisRecord.created_at >= start_date)
        elif report_type == "weekly":
            start_date = datetime.utcnow() - timedelta(days=7)
            query = query.filter(DiagnosisRecord.created_at >= start_date)
        elif report_type == "custom" and start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(DiagnosisRecord.created_at >= start)
            query = query.filter(DiagnosisRecord.created_at <= end)

        records = query.order_by(DiagnosisRecord.created_at.desc()).all()

        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Diagnosis Report"

        # Define styles
        header_fill = PatternFill(
            start_color="2864BD", end_color="2864BD", fill_type="solid"
        )
        header_font = Font(color="FFFFFF", bold=True, size=12)
        header_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        # Write title
        ws["A1"] = "Endometriosis Detection Report"
        ws["A1"].font = Font(bold=True, size=14)
        ws.merge_cells("A1:H1")

        # Write timestamp
        ws["A2"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws.merge_cells("A2:H2")

        # Write headers (row 4)
        headers = [
            "Patient Name",
            "Patient ID",
            "Diagnosis",
            "Confidence (%)",
            "Positive Prob (%)",
            "Negative Prob (%)",
            "Status",
            "Created Date",
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = border

        # Write data
        for row_idx, record in enumerate(records, 5):
            ws.cell(row=row_idx, column=1).value = (
                record.patient.full_name if record.patient else ""
            )
            ws.cell(row=row_idx, column=2).value = record.patient_id
            ws.cell(row=row_idx, column=3).value = record.diagnosis_text
            ws.cell(row=row_idx, column=4).value = record.confidence_score
            ws.cell(row=row_idx, column=5).value = record.probability_positive * 100
            ws.cell(row=row_idx, column=6).value = record.probability_negative * 100
            ws.cell(row=row_idx, column=7).value = record.status
            ws.cell(row=row_idx, column=8).value = record.created_at

            # Apply border to all cells
            for col in range(1, 9):
                ws.cell(row=row_idx, column=col).border = border

        # Adjust column widths
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 25
        ws.column_dimensions["D"].width = 15
        ws.column_dimensions["E"].width = 15
        ws.column_dimensions["F"].width = 15
        ws.column_dimensions["G"].width = 15
        ws.column_dimensions["H"].width = 20

        # Save to bytes
        import io

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        # Create response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = (
            f"attachment; filename=diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        return response

    except Exception as e:
        print(f"Excel export error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@doctor.route("/api/export-pdf", methods=["POST"])
@login_required
def export_pdf():
    """Export report as PDF"""
    try:
        from database.models import DiagnosisRecord
        from datetime import datetime, timedelta
        from flask import make_response
        from sqlalchemy.orm import joinedload
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        import io

        data = request.get_json()
        report_type = data.get("report_type")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Build query with eager loading
        query = DiagnosisRecord.query.options(
            joinedload(DiagnosisRecord.patient)
        ).filter_by(doctor_id=current_user.id)

        if report_type == "monthly":
            start_date = datetime.utcnow() - timedelta(days=30)
            query = query.filter(DiagnosisRecord.created_at >= start_date)
        elif report_type == "weekly":
            start_date = datetime.utcnow() - timedelta(days=7)
            query = query.filter(DiagnosisRecord.created_at >= start_date)
        elif report_type == "custom" and start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(DiagnosisRecord.created_at >= start)
            query = query.filter(DiagnosisRecord.created_at <= end)

        records = query.order_by(DiagnosisRecord.created_at.desc()).all()

        # Calculate statistics
        total_diagnoses = len(records)
        positive_count = sum(1 for r in records if "Detected" in r.diagnosis_text)
        negative_count = total_diagnoses - positive_count

        # Create PDF
        output = io.BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#2864BD"),
            spaceAfter=10,
            alignment=1,
        )

        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=20,
            alignment=1,
        )

        # Add title
        elements.append(Paragraph("Endometriosis Detection Report", title_style))
        elements.append(
            Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                subtitle_style,
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        # Add statistics
        stats_data = [
            ["Total Diagnoses", "Positive Cases", "Negative Cases", "Positive %"],
            [
                str(total_diagnoses),
                str(positive_count),
                str(negative_count),
                f"{(positive_count/total_diagnoses*100):.1f}%"
                if total_diagnoses > 0
                else "0%",
            ],
        ]

        stats_table = Table(stats_data, colWidths=[1.5 * inch] * 4)
        stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2864BD")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(stats_table)
        elements.append(Spacer(1, 0.3 * inch))

        # Add detailed table
        elements.append(Paragraph("Detailed Diagnosis Records", styles["Heading2"]))
        elements.append(Spacer(1, 0.15 * inch))

        table_data = [
            ["Patient", "Patient ID", "Diagnosis", "Confidence", "Status", "Date"]
        ]

        for record in records:
            table_data.append(
                [
                    (record.patient.full_name if record.patient else "")[:15],
                    record.patient_id,
                    record.diagnosis_text[:20],
                    f"{record.confidence_score:.1f}%",
                    record.status,
                    record.created_at.strftime("%Y-%m-%d"),
                ]
            )

        # Create table with smaller width to fit page
        table = Table(
            table_data,
            colWidths=[
                1.2 * inch,
                1 * inch,
                1.3 * inch,
                1 * inch,
                1 * inch,
                1.2 * inch,
            ],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2864BD")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )
        elements.append(table)

        # Build PDF
        doc.build(elements)
        output.seek(0)

        # Create response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = (
            f"attachment; filename=diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        response.headers["Content-Type"] = "application/pdf"

        return response

    except ImportError:
        return jsonify(
            {
                "success": False,
                "message": "PDF export requires reportlab. Install with: pip install reportlab",
            }
        ), 400
    except Exception as e:
        print(f"PDF export error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@doctor.route("/generate-report")
@login_required
def generate_report():
    return render_template("generate_report.html")


@doctor.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings.html")


@doctor.route("/update-settings", methods=["POST"])
@login_required
def update_settings():
    try:
        section = request.form.get("section")

        if section == "account":
            # Update account information
            current_user.full_name = request.form.get("full_name")
            current_user.email = request.form.get("email")

            db.session.commit()
            flash("Account information updated successfully!", "success")

        elif section == "security":
            # Handle password change
            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")

            # Verify current password
            if not current_user.check_password(current_password):
                flash("Current password is incorrect", "danger")
                return redirect(url_for("doctor.settings"))

            # Validate new password
            if new_password != confirm_password:
                flash("New passwords do not match", "danger")
                return redirect(url_for("doctor.settings"))

            if len(new_password) < 8:
                flash("Password must be at least 8 characters long", "danger")
                return redirect(url_for("doctor.settings"))

            # Set new password
            current_user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully!", "success")

        elif section == "appearance":
            # Store theme preference (can be saved to user profile)
            theme = request.form.get("theme")
            # This can be stored in user preferences
            flash(f"Theme changed to {theme} mode successfully!", "success")

        elif section == "notifications":
            # Store notification preferences
            flash("Notification settings updated successfully!", "success")

        return redirect(url_for("doctor.settings"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating settings: {str(e)}", "danger")
        return redirect(url_for("doctor.settings"))
