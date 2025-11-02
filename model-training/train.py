#!/usr/bin/env python3
"""
Minimal training script placeholder.
Usage: python train.py --data data/train.csv --out artifacts/model.pkl
"""
import os
import argparse
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/train.csv")
    parser.add_argument("--out", default="artifacts/model.pkl")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    if not os.path.exists(args.data):
        print(f"Data file {args.data} not found — creating synthetic dataset for demo.")
        df = pd.DataFrame({
            "feat1": [1,2,3,4,5,6,7,8,9,10],
            "feat2": [2,1,2,1,2,1,2,1,2,1],
            "label": [0,1,0,1,0,1,0,1,0,1]
        })
    else:
        df = pd.read_csv(args.data)

    X = df.drop(columns=["label"], errors="ignore")
    y = df["label"] if "label" in df.columns else (X.sum(axis=1) % 2)

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    joblib.dump(model, args.out)
    print(f"Saved model to {args.out}")


if __name__ == "__main__":
    main()
