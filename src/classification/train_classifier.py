import argparse
import itertools
import os
import pickle
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xgboost as xgb
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from report import generate_comparison

ALL_DATA_CSV = os.path.join("outputs", "aggregated", "all_data.csv")

COL_NAMES = [
    'syll1_s_freq', 'syll2_s_freq', 'syll3_s_freq', 'syll4_s_freq', 'syll5_s_freq',
    'syll6_s_freq', 'syll7_s_freq', 'syll8_s_freq', 'syll9_s_freq', 'syll10_s_freq',
    'syll1_e_freq', 'syll2_e_freq', 'syll3_e_freq', 'syll4_e_freq', 'syll5_e_freq',
    'syll6_e_freq', 'syll7_e_freq', 'syll8_e_freq', 'syll9_e_freq', 'syll10_e_freq',
    'syll1_dist', 'syll2_dist', 'syll3_dist', 'syll4_dist', 'syll5_dist',
    'syll6_dist', 'syll7_dist', 'syll8_dist', 'syll9_dist', 'syll10_dist',
    'syll1_dur', 'syll2_dur', 'syll3_dur', 'syll4_dur', 'syll5_dur',
    'syll6_dur', 'syll7_dur', 'syll8_dur', 'syll9_dur', 'syll10_dur',
    'mother_gen',
    'pup_sex',
    'avg_ISI_time', 'pup_age', 'session', 'pup_strain',
    'pup_gen',
    'mouse_idx',
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train XGBoost classifier for Mouse USV ASD detection",
    )
    parser.add_argument(
        '--group-split',
        action='store_true',
        help='Use group-aware train/val/test split based on mouse identity. '
             'Prevents data leakage by ensuring no mouse appears in more than one set.',
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default=None,
        help='Directory for results. Defaults to "results" (baseline) or '
             '"results_group_split" when --group-split is active.',
    )
    return parser.parse_args()


def plot_confusion_matrix(cnf_matrix, plots_dir, numbers_type='normalized',
                          class_names=[], title='Confusion matrix',
                          cmap=plt.cm.Blues, file_name='confusionmatrix.png'):
    """Plot and save a confusion matrix figure.
    Normalization can be applied by setting `normalize=True`.
    """
    cnf_matrix_normalized = cnf_matrix.astype('float') / cnf_matrix.sum(axis=1)[:, np.newaxis]
    if numbers_type == 'normalized':
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    plt.figure()
    plt.figure(figsize=(5, 5))
    plt.imshow(cnf_matrix, interpolation='nearest', cmap=cmap)
    plt.title(title, fontsize=18)
    plt.colorbar(plt.imshow(cnf_matrix, interpolation='nearest', cmap=cmap), shrink=0.80)
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)

    thresh = 0.8 * cnf_matrix.max() / 1.
    for i, j in itertools.product(range(cnf_matrix.shape[0]), range(cnf_matrix.shape[1])):
        if numbers_type == 'numbers_and_percentage':
            st1 = '{:.2f}%'.format(100 * cnf_matrix_normalized[i, j])
            st2 = '({:2d})'.format(cnf_matrix[i, j])
            plt.text(j, i, st1 + st2,
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black", fontsize=18)
        elif numbers_type == 'percentage':
            plt.text(j, i, format(cnf_matrix_normalized[i, j], '.2f'),
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black", fontsize=18)
        else:
            plt.text(j, i, format(cnf_matrix[i, j], 'd'),
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black", fontsize=18)

    plt.tight_layout()
    plt.ylabel('True label', fontsize=18)
    plt.xlabel('Predicted label', fontsize=18)
    plt.savefig(os.path.join(plots_dir, file_name))


def random_split(X, y, seed):
    """Default random row-level split (baseline behavior)."""
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, shuffle=True,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, random_state=seed, shuffle=True,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def group_aware_split(X, y, groups, seed):
    """Split by mouse identity so no mouse appears in more than one set.

    Splits at the mouse level with stratification on pup_gen, then maps
    back to rows.  Asserts that the three sets are fully disjoint.
    """
    mouse_labels = (
        pd.DataFrame({'mouse_idx': groups.values, 'label': y.values})
        .groupby('mouse_idx')['label']
        .first()
    )
    mice = mouse_labels.index.values
    labels = mouse_labels.values

    mice_trainval, mice_test = train_test_split(
        mice, test_size=0.2, random_state=seed, stratify=labels,
    )
    mice_trainval_labels = mouse_labels.loc[mice_trainval].values
    mice_train, mice_val = train_test_split(
        mice_trainval, test_size=0.25, random_state=seed, stratify=mice_trainval_labels,
    )

    train_mask = groups.isin(mice_train)
    val_mask = groups.isin(mice_val)
    test_mask = groups.isin(mice_test)

    train_set = set(groups[train_mask])
    val_set = set(groups[val_mask])
    test_set = set(groups[test_mask])
    assert train_set.isdisjoint(val_set), "Data leakage: mice shared between train and val"
    assert train_set.isdisjoint(test_set), "Data leakage: mice shared between train and test"
    assert val_set.isdisjoint(test_set), "Data leakage: mice shared between val and test"

    return (
        X[train_mask], X[val_mask], X[test_mask],
        y[train_mask], y[val_mask], y[test_mask],
    )


def log_split_info(X_train, y_train, X_val, y_val, X_test, y_test,
                   groups, is_group_split):
    """Print split diagnostics to the log."""
    print('\n=== Split Info ===')
    strategy = "group-aware (by mouse_idx)" if is_group_split else "random (row-level)"
    print(f'Strategy: {strategy}')
    print(f'Train: {len(X_train)} rows | Val: {len(X_val)} rows | Test: {len(X_test)} rows')

    train_mice = set(groups[X_train.index])
    val_mice = set(groups[X_val.index])
    test_mice = set(groups[X_test.index])

    if is_group_split:
        print(f'Train mice ({len(train_mice)}): {sorted(train_mice)}')
        print(f'Val mice   ({len(val_mice)}): {sorted(val_mice)}')
        print(f'Test mice  ({len(test_mice)}): {sorted(test_mice)}')
    else:
        shared_tv = len(train_mice & val_mice)
        shared_tt = len(train_mice & test_mice)
        shared_vt = len(val_mice & test_mice)
        if shared_tv or shared_tt or shared_vt:
            print(f'WARNING: mouse overlap -- train/val: {shared_tv}, '
                  f'train/test: {shared_tt}, val/test: {shared_vt} shared mice')

    for name, y_sub in [('Train', y_train), ('Val', y_val), ('Test', y_test)]:
        counts = y_sub.value_counts().sort_index()
        total = len(y_sub)
        parts = [f'class {int(lbl)}={cnt} ({100*cnt/total:.1f}%)' for lbl, cnt in counts.items()]
        print(f'  {name} labels: {", ".join(parts)}')

    print('==================\n')


def main():
    args = parse_args()

    # --- results directory ---------------------------------------------------
    if args.results_dir:
        results_dir = args.results_dir
    elif args.group_split:
        results_dir = 'results_group_split'
    else:
        results_dir = 'results'

    plots_dir = os.path.join(results_dir, 'plots')
    model_dir = os.path.join(results_dir, 'model')
    logs_dir = os.path.join(results_dir, 'logs')
    for d in [plots_dir, model_dir, logs_dir]:
        os.makedirs(d, exist_ok=True)

    # --- redirect stdout to log ----------------------------------------------
    orig_stdout = sys.stdout
    log_file = open(os.path.join(logs_dir, 'out.txt'), 'w')
    sys.stdout = log_file

    active_flags = []
    if args.group_split:
        active_flags.append('--group-split')
    print(f'Active flags: {active_flags if active_flags else "none (baseline)"}')
    print(f'Results directory: {results_dir}')

    # --- load data -----------------------------------------------------------
    dataset = pd.read_csv(ALL_DATA_CSV, header=None, names=COL_NAMES)
    X = dataset.iloc[:, :-2]
    y = dataset.iloc[:, -2]
    groups = dataset.iloc[:, -1]

    seed = 100

    # --- train / val / test split --------------------------------------------
    if args.group_split:
        X_train, X_val, X_test, y_train, y_val, y_test = group_aware_split(
            X, y, groups, seed,
        )
    else:
        X_train, X_val, X_test, y_train, y_val, y_test = random_split(X, y, seed)

    log_split_info(X_train, y_train, X_val, y_val, X_test, y_test,
                   groups, args.group_split)

    # --- train ---------------------------------------------------------------
    model = XGBClassifier(
        n_estimators=50, random_state=seed, learning_rate=0.1, max_depth=5,
        objective='binary:logistic', booster='gbtree',
        reg_lambda=1.5, reg_alpha=0.05, min_child_weight=0.1,
        scale_pos_weight=0.8, colsample_bytree=0.6,
        eval_metric=["auc", "error"],
    )

    eval_set = [(X_train, y_train), (X_val, y_val)]
    sample_weights = compute_sample_weight(class_weight='balanced', y=y_train)
    model.fit(X_train, y_train, sample_weight=sample_weights,
              eval_set=eval_set, verbose=False)

    # --- evaluate ------------------------------------------------------------
    pred_train = model.predict(X_train)
    train_acc = accuracy_score(y_train, pred_train)
    print('Train Accuracy: ', train_acc)

    pred_test = model.predict(X_test)
    test_acc = accuracy_score(y_test, pred_test)
    print('Test Accuracy: ', test_acc)

    print('Classification Report:')
    print(classification_report(y_test, pred_test, zero_division=0))
    report_dict = classification_report(y_test, pred_test, zero_division=0,
                                        output_dict=True)

    # --- AUC / error curves --------------------------------------------------
    eval_results = model.evals_result()
    epochs = len(eval_results['validation_0']['error'])
    x_axis = range(0, epochs)

    fig, ax = plt.subplots(1, 2, figsize=(16, 6))
    ax[0].plot(x_axis, eval_results['validation_0']['auc'], label='Train', linewidth=3)
    ax[0].plot(x_axis, eval_results['validation_1']['auc'], label='Validation', linewidth=3)
    ax[0].set_title('XGBoost AUC-ROC', fontsize=20)
    ax[0].set_ylabel('AUC-ROC', fontsize=20)
    ax[0].set_xlabel('N estimators', fontsize=20)
    ax[0].tick_params(axis='both', which='major', labelsize=16)
    ax[0].legend(fontsize=16)

    ax[1].plot(x_axis, eval_results['validation_0']['error'], label='Train', linewidth=3)
    ax[1].plot(x_axis, eval_results['validation_1']['error'], label='Validation', linewidth=3)
    ax[1].set_title('XGBoost Classification Error', fontsize=20)
    ax[1].set_ylabel('Classification Error', fontsize=20)
    ax[1].set_xlabel('N estimators', fontsize=20)
    ax[1].tick_params(axis='both', which='major', labelsize=16)
    ax[1].legend(fontsize=16)

    plt.savefig(os.path.join(plots_dir, 'AUC_error.png'), dpi=200)
    plt.show()
    plt.tight_layout()

    # --- confusion matrices --------------------------------------------------
    print('\n Confusion Matrix:')
    plot_confusion_matrix(confusion_matrix(y_test, pred_test), plots_dir,
                          numbers_type='numbers_and_percentage')

    plt.rcParams['figure.figsize'] = [15, 10]

    # --- save model ----------------------------------------------------------
    with open(os.path.join(model_dir, "XGBmodel.pkl"), "wb") as fp:
        pickle.dump(model, fp)

    # --- per-strain evaluation -----------------------------------------------
    strain1 = np.where(X_test['pup_strain'] == 1)
    strain2 = np.where(X_test['pup_strain'] == 2)
    y_test_arr = np.array(y_test)

    print('\n Confusion Matrix - New pup:')
    if len(strain1[0]) > 0:
        plot_confusion_matrix(
            confusion_matrix(y_test_arr[strain1[0]], pred_test[strain1[0]]),
            plots_dir, numbers_type='numbers_and_percentage',
            file_name='confusionmatrix_strain1.png',
        )
    else:
        print('No strain 1 data in test set, skipping.')

    print('\n Confusion Matrix - Old pup:')
    if len(strain2[0]) > 0:
        plot_confusion_matrix(
            confusion_matrix(y_test_arr[strain2[0]], pred_test[strain2[0]]),
            plots_dir, numbers_type='numbers_and_percentage',
            file_name='confusionmatrix_strain2.png',
        )
    else:
        print('No strain 2 data in test set, skipping.')

    # --- confusion matrix heatmap --------------------------------------------
    cf_matrix = confusion_matrix(y_test, pred_test)
    print(cf_matrix)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.set(font_scale=1.6)
    ax = sns.heatmap(cf_matrix / cf_matrix.sum(axis=1)[:, np.newaxis],
                     annot=True, fmt='.2%', cmap='Blues')
    ax.set_title('Confusion matrix', fontsize=20)
    ax.set_xlabel('Predicted label', fontsize=18)
    ax.set_ylabel('True label', fontsize=18)
    ax.xaxis.set_ticklabels(['0', '1'])
    ax.yaxis.set_ticklabels(['0', '1'])
    ax.tick_params(axis='both', which='major', labelsize=16)
    plt.savefig(os.path.join(plots_dir, 'conf_matrix.png'), dpi=300)
    plt.show()

    # --- feature importance --------------------------------------------------
    print(model.feature_importances_)

    plt.figure()
    plt.bar(range(len(model.feature_importances_)), model.feature_importances_)
    plt.xticks(range(len(model.feature_importances_)), COL_NAMES[:-2],
               rotation=45, ha="right")
    plt.savefig(os.path.join(plots_dir, 'feature_importances_0.png'), dpi=300)

    fig, ax = plt.subplots(1, 3, figsize=(30, 15))

    xgb.plot_importance(booster=model, importance_type='weight', title='Feature Weight',
                        show_values=False, height=0.5, ax=ax[0])
    ax[0].set_ylabel('Features', fontsize=20)
    ax[0].set_xlabel('F score', fontsize=20)
    ax[0].set_title('Feature Weight', fontsize=24)
    ax[0].tick_params(axis='both', which='major', labelsize=16)

    xgb.plot_importance(booster=model, importance_type='gain', title='Split Mean Gain',
                        show_values=False, height=0.5, ax=ax[1])
    ax[1].set_ylabel('Features', fontsize=20)
    ax[1].set_xlabel('F score', fontsize=20)
    ax[1].set_title('Split Mean Gain', fontsize=24)
    ax[1].tick_params(axis='both', which='major', labelsize=16)

    xgb.plot_importance(model, importance_type='cover', title='Sample Coverage',
                        show_values=False, height=0.5, ax=ax[2])
    ax[2].set_ylabel('Features', fontsize=20)
    ax[2].set_xlabel('F score', fontsize=20)
    ax[2].set_title('Sample Coverage', fontsize=24)
    ax[2].tick_params(axis='both', which='major', labelsize=16)

    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, 'feature_importance_1.png'), dpi=300)
    plt.show()

    # --- comparison vs baseline ----------------------------------------------
    generate_comparison(results_dir, test_acc, train_acc, report_dict, active_flags)

    # --- restore stdout ------------------------------------------------------
    sys.stdout = orig_stdout
    log_file.close()
    print(f'Done. Results saved to {results_dir}/')


if __name__ == '__main__':
    main()
