import time
import os
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
import xgboost as xgb
import itertools
import glob
import sys

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.linear_model import Ridge, Lasso

from sklearn.model_selection import GridSearchCV


orig_stdout = sys.stdout
f = open('results/out.txt', 'w')
sys.stdout = f


# plot confusion matrix
def plot_confusion_matrix(cnf_matrix, numbers_type='normalized', class_names=[], title='Confusion matrix', cmap=plt.cm.Blues, file_name='confusionmatrix.png'):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    combined = True
    cnf_matrix_normalized = cnf_matrix.astype('float') / cnf_matrix.sum(axis=1)[:, np.newaxis]
    if numbers_type == 'normalized':
        cnf_matrix_normalized = cnf_matrix.astype('float') / cnf_matrix.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    # print(cnf_matrix)
    plt.figure()
    plt.figure(figsize=(5,5))
    plt.imshow(cnf_matrix, interpolation='nearest', cmap=cmap)
    plt.title(title, fontsize=18)
    plt.colorbar(plt.imshow(cnf_matrix, interpolation='nearest', cmap=cmap),shrink=0.80)
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)
    

    thresh = 0.8*cnf_matrix.max() / 1.
    for i, j in itertools.product(range(cnf_matrix.shape[0]), range(cnf_matrix.shape[1])):
        if numbers_type == 'numbers_and_percentage':
            st1 = '{:.2f}%'.format(100 * cnf_matrix_normalized[i, j])
            st2 = '({:2d})'.format(cnf_matrix[i, j])
            plt.text(j, i, st1+st2,
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black", fontsize=18)

        elif numbers_type == 'percentage':
            fmt = '.2f'
            plt.text(j, i, format(cnf_matrix_normalized[i, j], fmt),
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black",fontsize=18)
        else:
            fmt = 'd'
            plt.text(j, i, format(cnf_matrix[i, j], fmt),
                     horizontalalignment="center", verticalalignment='bottom',
                     color="white" if cnf_matrix[i, j] > thresh else "black",fontsize=18)

    plt.tight_layout()
    plt.ylabel('True label',fontsize=18)
    plt.xlabel('Predicted label',fontsize=18)
    #fig = plt.gcf()
    plt.savefig(f'results/{file_name}')

    return

col_names = ['syll1_s_freq','syll2_s_freq','syll3_s_freq','syll4_s_freq','syll5_s_freq','syll6_s_freq','syll7_s_freq','syll8_s_freq','syll9_s_freq','syll10_s_freq',
            'syll1_e_freq','syll2_e_freq','syll3_e_freq','syll4_e_freq','syll5_e_freq','syll6_e_freq','syll7_e_freq','syll8_e_freq','syll9_e_freq','syll10_e_freq',
            'syll1_dist','syll2_dist','syll3_dist','syll4_dist','syll5_dist','syll6_dist','syll7_dist','syll8_dist','syll9_dist','syll10_dist',
            'syll1_dur','syll2_dur','syll3_dur','syll4_dur','syll5_dur','syll6_dur','syll7_dur','syll8_dur','syll9_dur','syll10_dur',
            'mother_gen',
            'pup_sex',
            'avg_ISI_time','pup_age','session','pup_strain',
            'pup_gen',
            'mouse_idx'
]

dataset = pd.read_csv("outputs/all_data.csv", header=None, names=col_names)
# dataset = pd.read_csv("/content/drive/MyDrive/final_project/final_classification/ALL_DATA/processed_data_for_final_classification_REDUCTION_BY_RECORDING_ALLDATA.csv", header=None, names=col_names)
# dataset.info()
X = dataset.iloc[:,:-2]
y = dataset.iloc[:,-2]
groupsM = dataset.iloc[:,-1]



seed = 100

# split the clean_X into train and test sets

X_train1, X_test, y_train1, y_test = train_test_split(X, y, test_size=0.2, random_state=seed, shuffle=True)

X_train, X_val, y_train, y_val = train_test_split(X_train1, y_train1, test_size=0.25, random_state=seed, shuffle=True)


import time
from xgboost import XGBClassifier
from sklearn.utils.class_weight import compute_sample_weight
# create an XGBoost classifier

# model = XGBClassifier(n_estimators=50, random_state=seed, learning_rate=1, max_depth=10, objective='binary:logistic', booster='gbtree', feval='rmsle',
#                      subsample= 0.8, reg_lambda = 0.1, reg_alpha = 0.1, min_child_weight = 0.1, scale_pos_weight = 1/2.08, colsample_bytree = 0.6, tree_method = 'exact')

# ARCHIVE: 88% accuracy was reached with: 
model = XGBClassifier(n_estimators=50, random_state=seed, learning_rate=0.1, max_depth=5, objective='binary:logistic', booster='gbtree', feval='rmsle',
                      reg_lambda = 1.5, reg_alpha = 0.05, min_child_weight = 0.1, scale_pos_weight = 0.8, colsample_bytree = 0.6)


    
# define the eval set and metric
eval_set = [(X_train, y_train), (X_val, y_val)]
eval_metric = ["auc","error"]

# fit the model
sample_weights = compute_sample_weight(class_weight='balanced', y=y_train)
model.fit(X_train, y_train, sample_weight=sample_weights, eval_metric=eval_metric, eval_set=eval_set, verbose=False)



from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
# model assessment
pred_train = model.predict(X_train)
print('Train Accuracy: ', accuracy_score(y_train, pred_train))

pred_test = model.predict(X_test)
print('Test Accuracy: ', accuracy_score(y_test, pred_test))

print('Classification Report:')
print(classification_report(y_test,pred_test,zero_division=0))



# CHECK ACCURACY MANUALLY TO BE SURE AND LOOK AT SOME RESULTS:
# print('calculate accuracy manually:', '\n')
# print('accuracy vec: ', accuracy_vec, 'true labels: ', y_test)
# train_accuracy_vec = pred_train == y_train
# test_accuracy_vec = pred_test == y_test
# print('train test accuracy is:', np.round(train_accuracy_vec.sum()/len(train_accuracy_vec), 3))
# print('manual test accuracy is:', np.round(test_accuracy_vec.sum()/len(test_accuracy_vec), 3))



# retrieve performance metrics and plot AUC-ROC and classification error
results = model.evals_result()
epochs = len(results['validation_0']['error'])
x_axis = range(0, epochs)
fig, ax = plt.subplots(1, 2, figsize=(16,6))
# plot auc
ax[0].plot(x_axis, results['validation_0']['auc'], label='Train', linewidth=3)
ax[0].plot(x_axis, results['validation_1']['auc'], label='Validation',linewidth=3)
ax[0].legend()
ax[0].set_title('XGBoost AUC-ROC', fontsize=20)
ax[0].set_ylabel('AUC-ROC', fontsize=20)
ax[0].set_xlabel('N estimators', fontsize=20)
ax[0].tick_params(axis='both', which='major', labelsize=16)
ax[0].legend(fontsize=16) 
# plot classification error
ax[1].plot(x_axis, results['validation_0']['error'], label='Train',linewidth=3)
ax[1].plot(x_axis, results['validation_1']['error'], label='Validation',linewidth=3)
ax[1].legend()
ax[1].set_title('XGBoost Classification Error', fontsize=20)
ax[1].set_ylabel('Classification Error', fontsize=20)
ax[1].set_xlabel('N estimators', fontsize=20)
ax[1].tick_params(axis='both', which='major', labelsize=16)
ax[1].legend(fontsize=16) 
plt.savefig('results/AUC_error.png', dpi=200)
plt.show()

plt.tight_layout()


# show confusion matrix
from sklearn.metrics import confusion_matrix
print('\n Confusion Matrix:')
# print(confusion_matrix(y_test,pred_test))
plot_confusion_matrix(confusion_matrix(y_test,pred_test), numbers_type='numbers_and_percentage')



# plot specific trees
plt.rcParams['figure.figsize'] = [15, 10]
#xgb.plot_tree(model,num_trees=0, rankdir='LR')
#xgb.plot_tree(model,num_trees=1, rankdir='LR')
#xgb.plot_tree(model,num_trees=31, rankdir='LR')


# SAVE MODEL TO FILE
import pickle
# save
pickle.dump(model, open("results/XGBmodel_051221.pkl", "wb"))

#result acording strain:
##########################
strain1 = np.where(X_test['pup_strain'] == 1)
strain2 = np.where(X_test['pup_strain'] == 2)
y_test_A = np.array(y_test)

from sklearn.metrics import confusion_matrix
print('\n Confusion Matrix - New pup:')
# print(confusion_matrix(y_test,pred_test))
plot_confusion_matrix(confusion_matrix(y_test_A[strain1[0]],pred_test[strain1[0]]), numbers_type='numbers_and_percentage_new_pup')
print('\n Confusion Matrix - Old pup:')
plot_confusion_matrix(confusion_matrix(y_test_A[strain2[0]],pred_test[strain2[0]]), numbers_type='numbers_and_percentage_old_pup')


from sklearn.metrics import confusion_matrix
import seaborn as sns
cf_matrix = confusion_matrix(y_test,pred_test)
print(cf_matrix)
fig, ax = plt.subplots(figsize=(6, 5))
sns.set(font_scale=1.6)
ax = sns.heatmap(cf_matrix/cf_matrix.sum(axis=1)[:, np.newaxis], annot=True, fmt='.2%', cmap='Blues')

ax.set_title('Confusion matrix', fontsize=20);
ax.set_xlabel('Predicted label', fontsize=18);
ax.set_ylabel('True label', fontsize=18);


## Ticket labels - List must be in alphabetical order
ax.xaxis.set_ticklabels(['0','1'])
ax.yaxis.set_ticklabels(['0','1'])
ax.tick_params(axis='both', which='major', labelsize=16)

## Display the visualization of the Confusion Matrix.
plt.savefig('results/conf_matrix.png', dpi=300)
plt.show()


# PLOT FEATURE IMPORTANCE - MANUALLY
print(model.feature_importances_)

import matplotlib.pyplot as plt
# plot
plt.bar(range(len(model.feature_importances_)), model.feature_importances_)
plt.xticks(range(len(model.feature_importances_)), col_names[:-2], rotation=45, ha="right")
plt.savefig('results/feature_importances_0.png', dpi=300)
# plt.show()

# PLOT FEATURE IMPORTANCE:

fig, ax = plt.subplots(1, 3, figsize=(30,15))
# plot importances with feature weight

xgb.plot_importance(
    booster=model, 
    importance_type='weight',
    title='Feature Weight',
    show_values=False,
    height=0.5,
    ax=ax[0]
)
ax[0].set_ylabel('Feateres', fontsize=20)
ax[0].set_xlabel('F score', fontsize=20)
ax[0].set_title('Feature Weight', fontsize=24)
ax[0].tick_params(axis='both', which='major', labelsize=16)

# plot importances with split mean gain
xgb.plot_importance(
    booster=model,
    importance_type='gain',
    title='Split Mean Gain',
    show_values=False,
    height=0.5,
    ax=ax[1]
)
ax[1].set_ylabel('Feateres', fontsize=20)
ax[1].set_xlabel('F score', fontsize=20)
ax[1].set_title('Split Mean Gain', fontsize=24)
ax[1].tick_params(axis='both', which='major', labelsize=16)
# plot importances with sample coverage
xgb.plot_importance(
    model,
    importance_type='cover',
    title='Sample Coverage',
    show_values=False,
    height=0.5,
    ax=ax[2]
)
ax[2].set_ylabel('Feateres', fontsize=20)
ax[2].set_xlabel('F score', fontsize=20)
ax[2].set_title('Sample Coverage', fontsize=24)
ax[2].tick_params(axis='both', which='major', labelsize=16)
plt.tight_layout()
plt.savefig('results/feature_importance_1.png', dpi=300)
plt.show()