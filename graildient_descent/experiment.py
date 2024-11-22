import logging
import os

import numpy as np

import wandb
from graildient_descent.model import Model
from graildient_descent.utils import load_data, set_random_seed, unflatten


# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def run_experiment(
    entity: str = "kirill-rubashevskiy",
    project: str = "graildient-descent",
    tags: list = None,
    wbsync: bool = True,
    save_model: bool = False,
    **config,
) -> None:
    """
    Train and evaluate a model on the Grailed dataset.

    Parameters:
        entity: The Weights & Biases (wandb) entity (username or team name) under which the run will be logged.
        project: The name of the wandb project where the run will be stored.
        tags: List of tags for the wandb run.
        wbsync: Whether to sync the run with wandb (online/offline mode).
        save_model: Whether to save the trained model to 'models/tmp/'.
        config: Additional configuration parameters to pass to the model.
    """
    # Determine wandb mode (online or disabled)
    mode = "online" if wbsync else "offline"

    # Initialize the wandb run
    run = wandb.init(
        entity=entity,
        project=project,
        mode=mode,
        tags=tags,
    )

    # Set a random seed for reproducibility and log it
    seed = set_random_seed()
    logging.info(f"Random seed set to {seed}")
    run.config.update({"random_seed": seed}, allow_val_change=True)

    # Update wandb config with the configuration parameters passed via CLI
    wandb.config.update(config, allow_val_change=True)

    # Unflatten the wandb config to handle nested configuration parameters
    config = unflatten(wandb.config)

    # Load train dataset
    train = load_data(config.get("train_dataset"))
    X_train = train.drop(columns=["sold_price", "id", "parsing_date"])
    y_train = train["sold_price"]

    # Load eval dataset
    eval = load_data(config.get("eval_dataset"))
    X_eval = eval.drop(columns=["sold_price", "id", "parsing_date"])
    y_eval = eval["sold_price"]

    # Log-transform train target
    y_train_log = np.log1p(y_train)

    # Extract model-specific configurations
    model_configs = {
        "model_name": run.name,  # Use the wandb run name as the model name
        "estimator_class": config.get("estimator_class"),
        "use_tab_features": config.get("use_tab_features"),
        "use_text_features": config.get("use_text_features"),
        "estimator_params": config.get("estimator_params", {}),
        "transformer_params": config.get("transformer_params", {}),
        "extractor_params": config.get("extractor_params", {}),
    }

    # Initialize the model with the extracted configurations
    model = Model(**model_configs)

    # Train the model on the training set
    model.fit(X_train, y_train_log)

    # Evaluate the model on the training set
    train_metrics = model.evaluate(X_train, y_train)
    rmsle_train = train_metrics.get("rmsle")
    wape_train = train_metrics.get("wape")

    # Log training metrics locally if wandb syncing is disabled
    if not wbsync:
        logging.info(f"RMSLE on Train Set: {rmsle_train:.3f}")
        logging.info(f"WAPE on Train Set: {wape_train:.2f}")

    # Log training metrics to wandb
    run.log({"rmsle_train": rmsle_train, "wape_train": wape_train})

    # Evaluate the model on the validation set
    eval_metrics = model.evaluate(X_eval, y_eval)
    rmsle_eval = eval_metrics.get("rmsle")
    wape_eval = eval_metrics.get("wape")
    # Log evaluation metrics locally if wandb syncing is disabled
    if not wbsync:
        logging.info(f"RMSLE on Eval Set: {rmsle_eval:.3f}")
        logging.info(f"WAPE on Eval Set: {wape_eval:.2f}")

    # Log evaluation set metrics to wandb
    run.log({"rmsle_eval": rmsle_eval, "wape_eval": wape_eval})

    # Optionally save the trained model to disk
    if save_model:
        # Create the directory for saving models if it doesn't exist
        os.makedirs("models/tmp/", exist_ok=True)
        save_path = os.path.join("models", "tmp")
        model.save_model(save_path)
        logging.info(f"Model saved to 'models/tmp/{run.name}.pkl'")

    # Finish the wandb run
    run.finish()


if __name__ == "__main__":
    run_experiment()
