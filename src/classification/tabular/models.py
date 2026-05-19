"""Model registry for the ASD classifier.

Each factory function returns an sklearn-compatible estimator that supports
`fit(X, y)` and `predict(X)`.  The registry dict maps CLI model names to
their factory functions.
"""

from xgboost import XGBClassifier


def create_xgboost(seed, scale_pos_weight=1.0):
    """XGBoost binary classifier. HT=1 is the positive class (scale_pos_weight target)."""
    return XGBClassifier(
        n_estimators=50, random_state=seed, learning_rate=0.1, max_depth=5,
        objective='binary:logistic', booster='gbtree',
        reg_lambda=1.5, reg_alpha=0.05, min_child_weight=0.1,
        scale_pos_weight=scale_pos_weight, colsample_bytree=0.6,
        eval_metric=["auc", "error"],
    )


def create_xgboost_tuned_dependent(seed, scale_pos_weight=1.0):
    """Tuned for subject-dependent baseline (rank 5 of 200-trial random search).

    CV balanced acc 0.819 / held-out test acc 0.78, HT recall 0.87, WT recall 0.75.
    See outputs/reports/xgboost_tuning/xgboost_tuning_summary.md.
    """
    return XGBClassifier(
        n_estimators=96, random_state=seed, learning_rate=0.08, max_depth=8,
        objective='binary:logistic', booster='gbtree',
        reg_lambda=3.0, reg_alpha=1.0, gamma=0.0, min_child_weight=2,
        subsample=0.6, colsample_bytree=0.7,
        scale_pos_weight=scale_pos_weight,
        eval_metric=["auc", "error"],
    )


def create_xgboost_tuned_independent(seed, scale_pos_weight=1.0):
    """Tuned for subject-independent baseline (rank 3 of 200-trial random search).

    CV balanced acc 0.785 / held-out test acc 0.71, HT recall 0.99, WT recall 0.60.
    Shallow, heavily-regularised — the independent split is data-limited.
    See outputs/reports/xgboost_tuning/xgboost_tuning_summary.md.
    """
    return XGBClassifier(
        n_estimators=20, random_state=seed, learning_rate=0.10, max_depth=3,
        objective='binary:logistic', booster='gbtree',
        reg_lambda=3.0, reg_alpha=0.05, gamma=0.0, min_child_weight=20,
        subsample=0.6, colsample_bytree=0.6,
        scale_pos_weight=scale_pos_weight,
        eval_metric=["auc", "error"],
    )


def create_tabpfn(seed):
    from tabpfn import TabPFNClassifier
    return TabPFNClassifier(seed=seed)


MODEL_REGISTRY = {
    "xgboost": create_xgboost,
    "xgboost_tuned_dependent": create_xgboost_tuned_dependent,
    "xgboost_tuned_independent": create_xgboost_tuned_independent,
    "tabpfn": create_tabpfn,
}

# Models that share the XGBoost capability surface (eval_set, feature importance,
# training curves) and the same scale_pos_weight wiring at fit time.
XGBOOST_FAMILY = {"xgboost", "xgboost_tuned_dependent", "xgboost_tuned_independent"}

# Capabilities per model -- used to gate training and evaluation features
# that only certain estimators support.
_SUPPORTS_EVAL_SET = set(XGBOOST_FAMILY)
# sample_weight=balanced is only applied under --legacy (double-weighting reproduction);
# the corrected default and the tuned models use scale_pos_weight only.
_SUPPORTS_SAMPLE_WEIGHT = set(XGBOOST_FAMILY)
_HAS_FEATURE_IMPORTANCE = set(XGBOOST_FAMILY)
_HAS_TRAINING_CURVES = set(XGBOOST_FAMILY)

# Extra keyword arguments passed to fit() per model.
_EXTRA_FIT_KWARGS = {
    "tabpfn": {"overwrite_warning": True},
}


def supports_eval_set(model_name):
    return model_name in _SUPPORTS_EVAL_SET


def supports_sample_weight(model_name):
    return model_name in _SUPPORTS_SAMPLE_WEIGHT


def has_feature_importance(model_name):
    return model_name in _HAS_FEATURE_IMPORTANCE


def has_training_curves(model_name):
    return model_name in _HAS_TRAINING_CURVES


def extra_fit_kwargs(model_name):
    return dict(_EXTRA_FIT_KWARGS.get(model_name, {}))
