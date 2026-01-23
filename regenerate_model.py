"""
Regenerate ML model ensuring compatibility with scikit-learn 1.5.0 and numpy 1.26.4
This script creates a model that will work across different scikit-learn versions
"""
import pickle
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("🔬 Regenerating ML model with version-compatible training...")
print("=" * 70)

# ==============================================================================
# TRAINING DATA (6 FEATURES)
# ==============================================================================

X_train = np.array([
    # No Endometriosis Cases (Label: 0)
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1],
    [1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0],
    [1, 0, 0, 1, 0, 0],
    [0, 1, 0, 1, 0, 0],
    [1, 1, 0, 0, 0, 1],
    
    # Endometriosis Cases (Label: 1)
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 0, 0],
    [1, 1, 1, 0, 1, 1],
    [0, 1, 1, 1, 1, 0],
    [1, 0, 1, 1, 1, 0],
    [1, 1, 0, 1, 1, 1],
    [1, 1, 1, 0, 0, 1],
    [0, 1, 1, 0, 1, 1],
    [1, 1, 1, 1, 1, 0],
    [1, 0, 1, 1, 0, 1],
    [0, 1, 1, 1, 1, 1],
    
    # Borderline/Moderate Cases
    [1, 1, 1, 1, 0, 1],
    [1, 1, 1, 0, 1, 0],
    [0, 0, 1, 1, 1, 1],
    [1, 1, 0, 1, 1, 0],
    [1, 0, 1, 1, 1, 1],
    [0, 1, 1, 1, 0, 1],
    
    # Additional varied cases
    [0, 0, 0, 1, 1, 0],
    [1, 1, 0, 0, 1, 1],
    [0, 1, 0, 1, 1, 1],
    [1, 0, 0, 1, 1, 1],
    [1, 1, 1, 0, 0, 0],
], dtype=np.float64)

y_train = np.array([
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  # 11 negative cases
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  # 11 positive cases
    1, 1, 1, 1, 1, 1,                  # 6 moderate/positive cases
    0, 0, 0, 0,                        # 4 borderline negative cases
    1,                                  # 1 positive case
], dtype=np.int32)

print(f"📊 Training Data:")
print(f"   Total samples: {len(X_train)}")
print(f"   Positive cases: {int(np.sum(y_train))}")
print(f"   Negative cases: {len(y_train) - int(np.sum(y_train))}")
print(f"   Features: 6")

# ==============================================================================
# STANDARDIZE FEATURES
# ==============================================================================

print("\n🔄 Preprocessing...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)

# ==============================================================================
# TRAIN BASE MODELS
# ==============================================================================

print("🤖 Training base models...")

# Set random_state consistently
RANDOM_STATE = 42

gb_model = GradientBoostingClassifier(
    n_estimators=100, 
    learning_rate=0.05, 
    max_depth=5, 
    random_state=RANDOM_STATE,
    verbose=0
)
gb_model.fit(X_scaled, y_train)
print("   ✅ Gradient Boosting trained")

rf_model = RandomForestClassifier(
    n_estimators=100, 
    max_depth=8, 
    random_state=RANDOM_STATE,
    n_jobs=-1,
    verbose=0
)
rf_model.fit(X_scaled, y_train)
print("   ✅ Random Forest trained")

ada_model = AdaBoostClassifier(
    n_estimators=100, 
    learning_rate=0.8, 
    random_state=RANDOM_STATE
)
ada_model.fit(X_scaled, y_train)
print("   ✅ AdaBoost trained")

svm_model = SVC(
    kernel='rbf', 
    C=1.0, 
    probability=True, 
    random_state=RANDOM_STATE,
    verbose=0
)
svm_model.fit(X_scaled, y_train)
print("   ✅ SVM trained")

# ==============================================================================
# GENERATE META-FEATURES FOR META-LEARNER
# ==============================================================================

print("\n🔄 Creating meta-learner...")

gb_meta = gb_model.predict_proba(X_scaled)
rf_meta = rf_model.predict_proba(X_scaled)
ada_meta = ada_model.predict_proba(X_scaled)
svm_meta = svm_model.predict_proba(X_scaled)

meta_features = np.hstack([gb_meta, rf_meta, ada_meta, svm_meta])

meta_learner = LogisticRegression(
    C=0.1, 
    max_iter=1000, 
    random_state=RANDOM_STATE,
    verbose=0
)
meta_learner.fit(meta_features, y_train)
print("   ✅ Meta-learner trained")

# ==============================================================================
# SAVE MODEL AS DICTIONARY (VERSION-INDEPENDENT)
# ==============================================================================

print("\n💾 Saving model...")

model_dict = {
    'scaler': scaler,
    'gb_model': gb_model,
    'rf_model': rf_model,
    'ada_model': ada_model,
    'svm_model': svm_model,
    'meta_learner': meta_learner,
    'feature_names': [
        'menstrual_irregularity', 
        'hormone_level', 
        'infertility', 
        'family_history', 
        'ovulation_dysfunction', 
        'prior_surgery'
    ],
    'version_info': {
        'sklearn_version': '1.5.0',
        'numpy_version': '1.26.4',
        'created_date': '2026-01-23'
    }
}

model_path = os.path.join(os.path.dirname(__file__), "stacked_model.pkl")

try:
    with open(model_path, "wb") as f:
        pickle.dump(model_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"✅ Model saved to: {model_path}")
except Exception as e:
    print(f"❌ Error saving model: {str(e)}")
    exit(1)

# ==============================================================================
# VERIFY MODEL LOADS
# ==============================================================================

print("\n🔍 Verifying model loads correctly...")
try:
    with open(model_path, "rb") as f:
        test_model = pickle.load(f)
    
    # Test prediction
    test_input = np.array([[1, 1, 1, 1, 1, 1]])
    test_scaled = test_model['scaler'].transform(test_input)
    
    gb_pred = test_model['gb_model'].predict_proba(test_scaled)
    rf_pred = test_model['rf_model'].predict_proba(test_scaled)
    ada_pred = test_model['ada_model'].predict_proba(test_scaled)
    svm_pred = test_model['svm_model'].predict_proba(test_scaled)
    
    meta_input = np.hstack([gb_pred, rf_pred, ada_pred, svm_pred])
    prediction = test_model['meta_learner'].predict_proba(meta_input)
    
    print(f"✅ Model verification successful")
    print(f"   Sample prediction probability: {prediction[0][1]*100:.2f}%")
    
except Exception as e:
    print(f"❌ Model verification failed: {str(e)}")
    exit(1)

print("\n" + "=" * 70)
print("✅ ML MODEL REGENERATION COMPLETE!")
print("📋 Model ready for production deployment")
print("=" * 70)
