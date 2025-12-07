import pickle
import os

MODELS_DIR = "../models"

def save_model(name, model, meta):
    """Save a model and its metadata."""
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    with open(os.path.join(MODELS_DIR, f"{name}.pkl"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(MODELS_DIR, f"{name}_meta.pkl"), "wb") as f:
        pickle.dump(meta, f)

def load_model(name):
    """Load a model and its metadata."""
    with open(os.path.join(MODELS_DIR, f"{name}.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, f"{name}_meta.pkl"), "rb") as f:
        meta = pickle.load(f)
    return model, meta



