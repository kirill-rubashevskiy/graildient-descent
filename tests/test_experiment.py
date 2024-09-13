import os
from unittest.mock import MagicMock, patch

from graildient_descent.experiment import run_experiment


# Mock data to be returned by load_data
mock_train_data = MagicMock()
mock_eval_data = MagicMock()
mock_train_data.drop.return_value = "X_train"
mock_train_data.__getitem__.return_value = "y_train"
mock_eval_data.drop.return_value = "X_eval"
mock_eval_data.__getitem__.return_value = "y_eval"

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

    # Assertions to ensure that external dependencies are called correctly

    # Check that wandb.init was called with the correct parameters
    mock_wandb.init.assert_called_once_with(
        entity=entity,
        project=project,
        config=config,
        mode="disabled",
        tags=tags,
    )

    # Check that load_data was called for both train and eval datasets
    assert mock_load_data.call_count == 2

    # Check that the Model was initialized
    mock_Model.assert_called_once()

    # Check that model.fit was called with correct arguments
    mock_model.fit.assert_called_once_with("X_train", "y_train")

    # Check that model.evaluate was called twice (train and eval)
    assert mock_model.evaluate.call_count == 2
    mock_model.evaluate.assert_any_call("X_train", "y_train")
    mock_model.evaluate.assert_any_call("X_eval", "y_eval")

    # Check that os.makedirs was called to create the directory for saving the model
    mock_makedirs.assert_called_once_with("models/tmp/", exist_ok=True)

    # Check that model.save_model was called with the correct path
    mock_model.save_model.assert_called_once()
    save_path = os.path.join("models", "tmp")
    mock_model.save_model.assert_called_with(save_path)

    # Check that wandb.run.finish was called
    mock_run.finish.assert_called_once()
