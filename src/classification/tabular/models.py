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


def create_tabpfn(seed):
    from tabpfn import TabPFNClassifier
    return TabPFNClassifier(seed=seed)


MODEL_REGISTRY = {
    "xgboost": create_xgboost,
    "tabpfn": create_tabpfn,
}

# Capabilities per model -- used to gate training and evaluation features
# that only certain estimators support.
_SUPPORTS_EVAL_SET = {"xgboost"}
_SUPPORTS_SAMPLE_WEIGHT = {"xgboost"}
_HAS_FEATURE_IMPORTANCE = {"xgboost"}
_HAS_TRAINING_CURVES = {"xgboost"}

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
