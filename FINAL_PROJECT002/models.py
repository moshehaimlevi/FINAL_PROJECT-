import pickle, os, re

os.makedirs("models", exist_ok=True)

def sanitize(name: str):
    return re.sub(r"[^a-zA-Z0-9_-]", "", name)

def save_model(name, model, meta):
    name = sanitize(name)
    with open(f"models/{name}.pkl", "wb") as f:
        pickle.dump({"model": model, "meta": meta}, f)

def load_model(name):
    name = sanitize(name)
    with open(f"models/{name}.pkl", "rb") as f:
        obj = pickle.load(f)
    return obj["model"], obj["meta"]




