"""Compare classifier results against the baseline metrics."""

import os

BASELINE_METRICS = {
    'test_accuracy': 0.829,
    'train_accuracy': 0.880,
    'weighted_f1': 0.83,
    'het_precision': 0.73,
    'het_recall': 0.90,
    'het_f1': 0.81,
    'wt_precision': 0.92,
    'wt_recall': 0.78,
    'wt_f1': 0.84,
}


def _lookup(d, *keys):
    """Return the first matching value from dict d for the given keys."""
    for k in keys:
        if k in d:
            return d[k]
    return {}


def generate_comparison(results_dir, test_acc, train_acc, report_dict, active_flags):
    """Write a comparison-vs-baseline summary file."""
    lines = [
        '=' * 60,
        'COMPARISON VS BASELINE',
        '=' * 60,
        'Active flags: {}'.format(', '.join(active_flags) if active_flags else 'none (baseline)'),
        '',
    ]

    def fmt(new_val, baseline_key):
        old = BASELINE_METRICS[baseline_key]
        delta = new_val - old
        sign = '+' if delta >= 0 else ''
        return '{:.3f}  (baseline: {:.3f}, delta: {}{:.3f})'.format(
            new_val, old, sign, delta,
        )

    lines.append('Test Accuracy:   {}'.format(fmt(test_acc, 'test_accuracy')))
    lines.append('Train Accuracy:  {}'.format(fmt(train_acc, 'train_accuracy')))

    w_avg = _lookup(report_dict, 'weighted avg')
    het = _lookup(report_dict, '0.0', '0', 0.0, 0)
    wt = _lookup(report_dict, '1.0', '1', 1.0, 1)

    lines.append('Weighted F1:     {}'.format(fmt(w_avg.get('f1-score', 0), 'weighted_f1')))
    lines.append('')
    lines.append('--- HET (class 0) ---')
    lines.append('  Precision: {}'.format(fmt(het.get('precision', 0), 'het_precision')))
    lines.append('  Recall:    {}'.format(fmt(het.get('recall', 0), 'het_recall')))
    lines.append('  F1:        {}'.format(fmt(het.get('f1-score', 0), 'het_f1')))
    lines.append('')
    lines.append('--- WT (class 1) ---')
    lines.append('  Precision: {}'.format(fmt(wt.get('precision', 0), 'wt_precision')))
    lines.append('  Recall:    {}'.format(fmt(wt.get('recall', 0), 'wt_recall')))
    lines.append('  F1:        {}'.format(fmt(wt.get('f1-score', 0), 'wt_f1')))
    lines.append('')
    lines.append('=' * 60)

    path = os.path.join(results_dir, 'comparison_vs_baseline.txt')
    with open(path, 'w') as fout:
        fout.write('\n'.join(lines) + '\n')
    return path
