from sys import platform
import pandas as pd
import numpy as np
from numpy import log, exp, arange
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LinearRegression, LassoCV
from sklearn.model_selection import train_test_split, RepeatedKFold, GridSearchCV
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn import tree
from dtreeviz.trees import dtreeviz # will be used for tree visualization


# dataset is from Kaggle
# https://www.kaggle.com/austinreese/craigslist-carstrucks-data

file = '/vehicles.csv'

# data load
data = pd.read_csv(file)
data = data.drop(data.columns.values[0], 1)

# data summarization
print(data.iloc[:, 1:].describe())

# variable list
print(data.columns)
print(data.iloc[0])

# count unique values
unique_val = data.nunique(axis=0).sort_values()

# count na
count_na = data.isnull().sum().sort_values(ascending=False)
percent_na = count_na/data.shape[0]

# title uniques
print(data['title_status'].unique())
print(data['model'].unique())

# select variables
select_var = ['price', 'year', 'odometer', 'manufacturer', 'condition', 'cylinders', 'fuel',
              'title_status',  'transmission', 'drive', 'type', 'paint_color', 'state']

# remove any missing values
new_data = data[select_var].dropna(how='any')

# remove outliers (price > 1000 or price < 1000000 or odometer > 10000000)
new_data = new_data[(new_data['price']>1e+3) & (new_data['price']<1e+6)]
new_data = new_data[(new_data['odometer']<1e+7)]

# log transformation of price and odometer to remedy skewness of the distributions
new_data['odometer'] = log(new_data['odometer'] + 1e-2)
new_data['price'] = log(new_data['price'])

# plot the original and log-transformed price andodometer
fig, ax = plt.subplots(1, 2)
exp(new_data['price']).hist(ax=ax[0], bins=70)
new_data['price'].hist(ax=ax[1], bins=70)
# ax[0].set_title('Price (original)')
ax[0].set_xlabel('Price ($)')
# ax[1].set_title('Price (log-transformed)')
ax[1].set_xlabel('log(Price)')
ax[0].set_ylabel('Frequency')

fig, ax = plt.subplots(1, 2)
exp(new_data['odometer']).hist(ax=ax[0], bins=70)
new_data['odometer'].hist(ax=ax[1], bins=70)
# ax[0].set_title('Odometer')
# ax[1].set_title('Odometer (log-transformed)')
ax[0].set_xlabel('Odometer')
ax[1].set_xlabel('log(Odometer)')
ax[0].set_ylabel('Frequency')

# linear regression
lm_data = new_data.copy()
lab_var = ['manufacturer', 'condition', 'cylinders', 'fuel', 'title_status', 'transmission', 'drive', 'type', 'paint_color', 'state']
lm_data = pd.concat([lm_data.iloc[:, :3], pd.get_dummies(lm_data[lab_var], drop_first=True)], axis=1)

lm_predictors = lm_data.iloc[:, 1:]
lm_price = lm_data.iloc[:, 0]

# test and train split
X_lm_train, X_lm_test, y_lm_train, y_lm_test = train_test_split(lm_predictors, lm_price, test_size=.2)

lm = LinearRegression()

# fit the linear regression model
lm.fit(X_lm_train, y_lm_train)

# calculate R square for training and test data
lm.score(X_lm_train, y_lm_train)
lm.score(X_lm_test, y_lm_test)

# calculate the predicted price
y_pred_lm = lm.predict(X_lm_test)

# calculate RMSE
mean_squared_error(y_lm_test, y_pred_lm, squared=False)


## LassoCV
cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=1)
# define model
ls = LassoCV(alphas=arange(0.01, 1, 0.01), cv=cv, n_jobs=-1)
# fit model
ls.fit(X_lm_train, y_lm_train)

# R squared for training and test data
ls.score(X_lm_train, y_lm_train)
ls.score(X_lm_test, y_lm_test)
y_pred_ls = ls.predict(X_lm_test)

# RMSE
mean_squared_error(y_lm_test, y_pred_ls, squared=False)
mean_squared_error(exp(y_lm_test), exp(y_pred_ls), squared=False)

# random forest
rf_data = new_data.copy()
lab_var = ['manufacturer', 'condition', 'cylinders', 'fuel', 'title_status', 'transmission', 'drive', 'type', 'paint_color', 'state']

# label encoding for random forest categorical variables
rf_data[lab_var] = rf_data[lab_var].apply(LabelEncoder().fit_transform)
rf_predictors = rf_data.iloc[:, 1:]
rf_price = rf_data.iloc[:, 0]
X_rf_train, X_rf_test, y_rf_train, y_rf_test = train_test_split(rf_predictors, rf_price, test_size=.2)

rf = RandomForestRegressor(n_estimators=100, max_depth=16, n_jobs=-1)
rf.fit(X_rf_train, y_rf_train)

important_feature = pd.DataFrame({'Variable':rf_predictors.columns,
              'Importance':rf.feature_importances_}).sort_values('Importance', ascending=False)
print(important_feature)

ax = plt.bar(list(range(important_feature.shape[0])), important_feature['Importance'])
plt.xticks(list(range(important_feature.shape[0])), important_feature['Variable'], rotation='vertical')


y_pred_rf = rf.predict(X_rf_test)

print(rf.score(X_rf_train, y_rf_train))
print(rf.score(X_rf_test, y_rf_test))

mean_squared_error(y_rf_test, y_pred_rf, squared=False)
mean_squared_error(exp(y_rf_test), exp(y_pred_rf), squared=False)

# plot the absolute deviation error
ax = (np.abs(exp(y_pred_rf) - exp(y_rf_test))).hist(bins=1000)
ax.set_title("Absolute Deviation Error")
ax.set_xlim(0, 10000)
ax.set_xlabel("Price")
ax.set_ylabel("Frequency")

ax = (exp(y_pred_rf) - exp(y_rf_test)).hist(bins=1000)
ax.set_title("Deviation Error")
ax.set_xlim(-10000, 10000)
ax.set_xlabel("Price")
ax.set_ylabel("Frequency")


# Grid CV for random forest
param_grid = {
    'bootstrap': [True],
    'max_depth': [4, 6, 10, 14, 16],
    'min_samples_leaf': [3, 4, 5],
    'min_samples_split': [8, 10, 12]
}
grid_search = GridSearchCV(estimator = rf, param_grid = param_grid,
                          cv = 3, n_jobs = -1, verbose = 2)

grid_search.fit(X_rf_train, y_rf_train)

grid_search.score(X_rf_train, y_rf_train)
grid_search.score(X_rf_test, y_rf_test)
grid_search.best_params_
grid_search.best_index_

# best CV result showed 16 depth again

# plot random forest
plt.figure(figsize=(20,20))
_ = tree.plot_tree(rf.estimators_[0], feature_names=rf_data.columns, filled=True)

viz = dtreeviz(rf.estimators_[0], X_rf_train, y_rf_train,
               feature_names=X_rf_train.columns, target_name="Target")
viz



# Import tools needed for visualization
from sklearn.tree import export_graphviz
import pydot

# Pull out one tree from the forest
tree = rf.estimators_[0]

# Export the image to a dot file
export_graphviz(tree, out_file = 'tree.dot', feature_names = X_rf_train.columns, rounded = True, precision = 1)

# Use dot file to create a graph
(graph, ) = pydot.graph_from_dot_file('./tree.dot')

# Write graph to a pdf file
graph.write_pdf('./tree.pdf')
