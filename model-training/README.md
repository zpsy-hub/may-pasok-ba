# Model Training

This folder contains a minimal training script and Dockerfile to build and run training locally.

Quick start (local):

1. Create a virtual environment and install requirements:

   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt

2. Run training (will create a synthetic dataset if none exists):

   python train.py --out artifacts/model.pkl
3. Run in CI / deployment:

   This project uses GitHub Actions and Supabase for deployments and automation instead of Docker. Add your dataset to `model-training/data/train.csv` or update your CI to provide data as an artifact or from a database.

TODO: Replace synthetic data with your dataset at `model-training/data/train.csv`.
