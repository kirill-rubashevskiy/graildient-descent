from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from graildient_descent.experiment import run_experiment


# Create mock DataFrames
mock_train_data = pd.DataFrame(
    {
        "sold_price": [100, 200, 300],
        "id": [1, 2, 3],
        "parsing_date": ["2024-01-01"] * 3,
        "feature1": [1, 2, 3],
        "feature2": ["a", "b", "c"],
    }
)

mock_eval_data = pd.DataFrame(
    {
        "sold_price": [150, 250, 350],
        "id": [4, 5, 6],
        "parsing_date": ["2024-01-01"] * 3,
        "feature1": [4, 5, 6],
        "feature2": ["d", "e", "f"],
    }
)

# Mock evaluation metrics
mock_train_metrics = {"rmsle": 0.1, "wape": 0.2}
mock_eval_metrics = {"rmsle": 0.3, "wape": 0.4}

# Mock Model methods
mock_model = MagicMock()
mock_model.evaluate.side_effect = [mock_train_metrics, mock_eval_metrics]


@patch("graildient_descent.experiment.wandb")
@patch("graildient_descent.experiment.load_data")
@patch("graildient_descent.experiment.Model")
@patch("os.makedirs")
def test_run_experiment(mock_makedirs, mock_Model, mock_load_data, mock_wandb):
    # Setup the mocks
    mock_load_data.side_effect = [mock_train_data, mock_eval_data]
    mock_Model.return_value = mock_model
    mock_run = MagicMock()
    mock_wandb.init.return_value = mock_run

    # Define test parameters
    entity = "test_entity"
    project = "test_project"
    tags = ["test"]
    wbsync = False
    save_model = True
    config = {
        "train_dataset": "train.csv",
        "eval_dataset": "eval.csv",
        "estimator_class": "TestEstimator",
        "use_tab_features": True,
        "use_text_features": True,
        "estimator_params": {"param1": "value1"},
        "transformer_params": {"param2": "value2"},
        "extractor_params": {"param3": "value3"},
    }

    # Call the function under test
    run_experiment(
        entity=entity,
        project=project,
        tags=tags,
        wbsync=wbsync,
        save_model=save_model,
        **config,
    )

    # Verify wandb initialization
    mock_wandb.init.assert_called_once()

    # Verify data loading
    assert mock_load_data.call_count == 2

    # Verify model initialization
    mock_Model.assert_called_once()

    # Verify model training
    # Get the actual call arguments
    fit_call_args = mock_model.fit.call_args[0]
    X_train, y_train_log = fit_call_args

    # Check that X_train is the correct DataFrame (excluding specified columns)
    pd.testing.assert_frame_equal(
        X_train, mock_train_data.drop(columns=["sold_price", "id", "parsing_date"])
    )

    # Check that y_train_log is the log-transformed target
    np.testing.assert_array_almost_equal(
        y_train_log, np.log1p(mock_train_data["sold_price"].values)
    )

    # Verify model evaluation calls
    assert mock_model.evaluate.call_count == 2

    # Verify model saving
    mock_makedirs.assert_called_once_with("models/tmp/", exist_ok=True)
    mock_model.save_model.assert_called_once()

    # Verify wandb run completion
    mock_run.finish.assert_called_once()
