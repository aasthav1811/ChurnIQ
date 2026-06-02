import joblib
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

from src.pipeline.load_data import load_raw
from src.pipeline.feature_engineering import engineer_features, build_preprocessor
from src.config import MODEL_PATH, PREPROCESSOR_PATH, TARGET_COL, RANDOM_STATE


def train():
    print("Loading data...")
    df = engineer_features(load_raw())

    y = df[TARGET_COL]
    X = df.drop(columns=[TARGET_COL, "customerID"])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    print("Preprocessing...")
    pre = build_preprocessor()
    X_train_t = pre.fit_transform(X_train)
    X_test_t = pre.transform(X_test)

    # Fix sparse matrix for SMOTE
    try:
        X_train_dense = X_train_t.toarray()
        X_test_dense = X_test_t.toarray()
    except AttributeError:
        X_train_dense = X_train_t
        X_test_dense = X_test_t

    print("Applying SMOTE for class balance...")
    sm = SMOTE(random_state=RANDOM_STATE)
    X_train_res, y_train_res = sm.fit_resample(X_train_dense, y_train)

    print("Training XGBoost model...")
    model = XGBClassifier(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="auc",
        random_state=RANDOM_STATE,
        verbosity=0,
    )
    model.fit(X_train_res, y_train_res)

    proba = model.predict_proba(X_test_dense)[:, 1]
    pred = (proba > 0.5).astype(int)

    print(f"\n{'='*40}")
    print(f"ROC-AUC : {roc_auc_score(y_test, proba):.4f}")
    print(classification_report(y_test, pred, target_names=["Stayed", "Churned"]))
    print("Confusion matrix:\n", confusion_matrix(y_test, pred))
    print(f"{'='*40}\n")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(pre, PREPROCESSOR_PATH)
    print(f"✅ Model saved → {MODEL_PATH}")
    print(f"✅ Preprocessor saved → {PREPROCESSOR_PATH}")
    return model, pre


if __name__ == "__main__":
    train()
