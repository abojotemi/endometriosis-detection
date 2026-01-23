import pickle
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# STACKED MODEL CLASS (Module Level - Must match doctor_routes.py)
# ==============================================================================
class AdvancedStackedEndometriosisModel:
    """
    Advanced ensemble model for endometriosis prediction combining:
    - Gradient Boosting
    - Random Forest
    - AdaBoost
    - Support Vector Machine
    with a meta-learner
    """
    
    def __init__(self, gb, rf, ada, svm, meta, scaler):
        self.gb = gb
        self.rf = rf
        self.ada = ada
        self.svm = svm
        self.meta = meta
        self.scaler = scaler
        self.feature_names = [
            'menstrual_irregularity',
            'hormone_level',
            'infertility',
            'family_history',
            'ovulation_dysfunction',
            'prior_surgery'
        ]
    
    def predict(self, X):
        """Make binary prediction (0 or 1)"""
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from base models
        gb_pred = self.gb.predict_proba(X_scaled)
        rf_pred = self.rf.predict_proba(X_scaled)
        ada_pred = self.ada.predict_proba(X_scaled)
        svm_pred = self.svm.predict_proba(X_scaled)
        
        # Stack predictions
        meta_features = np.hstack([gb_pred, rf_pred, ada_pred, svm_pred])
        
        # Final prediction from meta-learner
        return self.meta.predict(meta_features)
    
    def predict_proba(self, X):
        """Get probability estimates"""
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from base models
        gb_pred = self.gb.predict_proba(X_scaled)
        rf_pred = self.rf.predict_proba(X_scaled)
        ada_pred = self.ada.predict_proba(X_scaled)
        svm_pred = self.svm.predict_proba(X_scaled)
        
        # Stack predictions
        meta_features = np.hstack([gb_pred, rf_pred, ada_pred, svm_pred])
        
        # Final probabilities from meta-learner
        return self.meta.predict_proba(meta_features)
    
    def predict_with_confidence(self, X):
        """Get predictions with confidence scores and reasoning"""
        proba = self.predict_proba(X)
        pred = self.predict(X)
        
        results = []
        for i in range(len(pred)):
            confidence = max(proba[i]) * 100
            risk_level = "HIGH" if proba[i][1] >= 0.7 else "MODERATE" if proba[i][1] >= 0.4 else "LOW"
            
            results.append({
                'prediction': pred[i],
                'probability_no_endo': float(proba[i][0]) * 100,
                'probability_endo': float(proba[i][1]) * 100,
                'confidence': float(confidence),
                'risk_level': risk_level
            })
        
        return results

def train_endometriosis_model():
    """
    Train stacked ensemble model for endometriosis detection
    Using the clinical training data from create_model.py
    """
    
    print("🔬 Creating Advanced Endometriosis Prediction Model...")
    print("=" * 60)

    # ==============================================================================
    # TRAINING DATA (6 FEATURES)
    # ==============================================================================

    X_train = np.array([
        # No Endometriosis Cases (Label: 0)
        [0, 0, 0, 0, 0, 0],  # Completely healthy
        [0, 0, 0, 0, 0, 0],  # Healthy variant
        [1, 0, 0, 0, 0, 0],  # Minor menstrual irregularity only
        [0, 0, 0, 1, 0, 0],  # Family history but no other symptoms
        [0, 1, 0, 0, 0, 0],  # Slight hormone variation
        [0, 0, 0, 0, 0, 1],  # Past surgery, no other issues
        [1, 1, 0, 0, 0, 0],  # Minor hormonal/menstrual issues
        [0, 0, 0, 0, 1, 0],  # Minor ovulation issue resolved
        [1, 0, 0, 1, 0, 0],  # Menstrual + family history
        [0, 1, 0, 1, 0, 0],  # Hormone + family history
        [1, 1, 0, 0, 0, 1],  # Multiple minor issues, no infertility
        
        # Endometriosis Cases (Label: 1)
        [1, 1, 1, 1, 1, 1],  # Severe case: all symptoms present
        [1, 1, 1, 1, 0, 0],  # Classic presentation
        [1, 1, 1, 0, 1, 1],  # Severe with surgery history
        [0, 1, 1, 1, 1, 0],  # Hormone abnormality with infertility
        [1, 0, 1, 1, 1, 0],  # Infertility with family history
        [1, 1, 0, 1, 1, 1],  # Multiple active symptoms
        [1, 1, 1, 0, 0, 1],  # Classic case with prior surgery
        [0, 1, 1, 0, 1, 1],  # Hormone, infertility, dysfunction, surgery
        [1, 1, 1, 1, 1, 0],  # Very strong indicator pattern
        [1, 0, 1, 1, 0, 1],  # Menstrual, infertility, family, surgery
        [0, 1, 1, 1, 1, 1],  # Multiple strong indicators
        
        # Borderline/Moderate Cases
        [1, 1, 1, 1, 0, 1],  # Multiple strong indicators
        [1, 1, 1, 0, 1, 0],  # Primary symptoms present
        [0, 0, 1, 1, 1, 1],  # Infertility with family history
        [1, 1, 0, 1, 1, 0],  # Menstrual, hormone, family, dysfunction
        [1, 0, 1, 1, 1, 1],  # Infertility with complications
        [0, 1, 0, 1, 1, 1],  # Hormone, family, dysfunction, surgery
    ])

    y_train = np.array([
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # No endometriosis
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # Endometriosis
        1, 1, 1, 1, 1, 1,                 # Borderline/Moderate
    ])

    # ==============================================================================
    # FEATURE DESCRIPTION
    # ==============================================================================
    feature_names = [
        "Menstrual Irregularities",
        "Hormonal Abnormalities", 
        "Infertility Issues",
        "Family History",
        "Ovulation Dysfunction",
        "Previous Surgery"
    ]

    print("\n📊 Training Data:")
    print(f"   Samples: {len(X_train)}")
    print(f"   Features: {X_train.shape[1]}")
    print(f"   Positive cases: {np.sum(y_train)}")
    print(f"   Negative cases: {len(y_train) - np.sum(y_train)}")
    print(f"\n📋 Features:")
    for i, name in enumerate(feature_names):
        print(f"   {i+1}. {name}")

    # ==============================================================================
    # STANDARDIZE FEATURES
    # ==============================================================================
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    print("\n🔄 Training Base Learners...")
    print("-" * 60)

    # ==============================================================================
    # BASE LEARNER 1: RANDOM FOREST
    # ==============================================================================
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    rf_model.fit(X_train_scaled, y_train)
    rf_scores = cross_val_score(rf_model, X_train_scaled, y_train, cv=5)
    print(f"✅ Random Forest - CV Accuracy: {rf_scores.mean():.4f} (+/- {rf_scores.std():.4f})")

    # ==============================================================================
    # BASE LEARNER 2: GRADIENT BOOSTING
    # ==============================================================================
    gb_model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    gb_model.fit(X_train_scaled, y_train)
    gb_scores = cross_val_score(gb_model, X_train_scaled, y_train, cv=5)
    print(f"✅ Gradient Boosting - CV Accuracy: {gb_scores.mean():.4f} (+/- {gb_scores.std():.4f})")

    # ==============================================================================
    # BASE LEARNER 3: ADABOOST
    # ==============================================================================
    ab_model = AdaBoostClassifier(n_estimators=100, learning_rate=1.0, random_state=42)
    ab_model.fit(X_train_scaled, y_train)
    ab_scores = cross_val_score(ab_model, X_train_scaled, y_train, cv=5)
    print(f"✅ AdaBoost - CV Accuracy: {ab_scores.mean():.4f} (+/- {ab_scores.std():.4f})")

    # ==============================================================================
    # BASE LEARNER 4: SUPPORT VECTOR MACHINE
    # ==============================================================================
    svm_model = SVC(kernel='rbf', probability=True, random_state=42)
    svm_model.fit(X_train_scaled, y_train)
    svm_scores = cross_val_score(svm_model, X_train_scaled, y_train, cv=5)
    print(f"✅ SVM - CV Accuracy: {svm_scores.mean():.4f} (+/- {svm_scores.std():.4f})")

    # ==============================================================================
    # GENERATE META-FEATURES
    # ==============================================================================
    print("\n🔄 Generating Meta-Features...")
    gb_proba = gb_model.predict_proba(X_train_scaled)
    rf_proba = rf_model.predict_proba(X_train_scaled)
    ab_proba = ab_model.predict_proba(X_train_scaled)
    svm_proba = svm_model.predict_proba(X_train_scaled)
    
    X_meta = np.hstack([gb_proba, rf_proba, ab_proba, svm_proba])

    # ==============================================================================
    # META-LEARNER: LOGISTIC REGRESSION
    # ==============================================================================
    print("🔄 Training Meta-Learner...")
    meta_learner = LogisticRegression(random_state=42, max_iter=1000)
    meta_learner.fit(X_meta, y_train)
    meta_scores = cross_val_score(meta_learner, X_meta, y_train, cv=5)
    print(f"✅ Meta-Learner - CV Accuracy: {meta_scores.mean():.4f} (+/- {meta_scores.std():.4f})")

    # ==============================================================================
    # SAVE MODEL
    # ==============================================================================
    stacked_model = AdvancedStackedEndometriosisModel(gb_model, rf_model, ab_model, svm_model, meta_learner, scaler)
    
    model_path = os.path.join(os.path.dirname(__file__), "stacked_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(stacked_model, f)

    print("\n" + "=" * 60)
    print(f"✅ MODEL TRAINING COMPLETE!")
    print(f"✅ Model saved to: {model_path}")
    print("=" * 60)
    
    return stacked_model

if __name__ == "__main__":
    train_endometriosis_model()


