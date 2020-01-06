# The data set used in this example is from http://archive.ics.uci.edu/ml/datasets/Wine+Quality
# P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis.
# Modeling wine preferences by data mining from physicochemical properties. In Decision Support Systems, Elsevier, 47(4):547-553, 2009.

import os
import warnings
import sys

import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet

import mlflow
import mlflow.sklearn



def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual, pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2



if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    np.random.seed(40)

    # Read the wine-quality csv file (make sure you're running this from the root of MLflow!)
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml_log_processed.csv")
    data = pd.read_csv(log_path)
        
    mlflow.tracking.set_tracking_uri('http://mlflow-image:5500')
    # Split the data into training and test sets. (0.75, 0.25) split.
    train, test = train_test_split(data)

    # The predicted column is "fwd_returns"
    train_x = train.drop(["fwd_returns"], axis=1)
    test_x = test.drop(["fwd_returns"], axis=1)
    train_y = train[["fwd_returns"]]
    test_y = test[["fwd_returns"]]

    n_estimators=float(sys.argv[1]) if len(sys.argv) > 1 else 200
    max_depth=float(sys.argv[2]) if len(sys.argv) > 2 else 10

    lr = RandomForestRegressor(n_estimators=n_estimators,max_depth=max_depth)
    lr.fit(train_x, train_y)
    predicted_qualities = lr.predict(test_x)
    (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

    print("RandomForest Model (n_estimators=%f, max_depth=%f):" % (n_estimators, max_depth))
    print("  RMSE: %s" % rmse)
    print("  MAE: %s" % mae)
    print("  R2: %s" % r2)

    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("max_depth", max_depth)
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("r2", r2)
    mlflow.log_metric("mae", mae)
    mlflow.sklearn.log_model(lr, "model")
