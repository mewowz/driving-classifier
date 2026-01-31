import pandas as pd
import numpy as np
from typing import List, Tuple
import sklearn

def run_kmeans_jobs(x_features: pd.DataFrame, *, min_clusters=4, max_clusters=8, **kwargs) -> List[Tuple[sklearn.cluster.KMeans, np.ndarray]]:
    """
    Train several kmeans jobs, each on the same set of data, incrementing in cluster sizes. 
    """
    if max_clusters < min_clusters:
        raise ValueError(f"Argument 'max_clusters' (got {max_clusters}) must be larger or equal to 'min_clusters' (got {min_clusters})")

    results = []
    for n in range(min_clusters, max_clusters + 1):
        kmeans = sklearn.cluster.KMeans(
                                    n_clusters=n,
                                    **kwargs
                                )
        labels = kmeans.fit_predict(x_features)
        results.append(tuple([kmeans, labels]))

    return results

def run_DBSCAN_jobs(x_features: pd.DataFrame, *, eps_min=1.0, eps_max=2.5, eps_step=0.1, eps_correction=10e-6, min_samples_min=5, min_samples_max=8, **kwargs):
    """
    Runs multiple DBSCAN jobs on a set of data. The return matrix can be quite large.
    """
    if eps_max <= 0:
        raise ValueError(
                f"Argument 'eps_max' (got {eps_max}) cannot be negative or 0!"
        )
    if eps_min <= 0:
        raise ValueError(
                f"Argument 'eps_min' (got {eps_min}) cannot be negative or 0!"
        )
    if eps_max <= eps_min:
        raise ValueError(
                f"Argument 'eps_max' (got {eps_max}) cannot be smaller than or equal to 'eps_min' (got {eps_min})"
        )
    if eps_step <= 0:
        raise ValueError(
                f"Argument 'eps_step' (got {eps_step}) cannot be negative or 0!"
        )
    if min_samples_min <= 0:
        raise ValueError(
                f"Argument 'min_samples_min' (got {min_samples_min}) cannot be negative or 0!"
        )
    if min_samples_max <= 0:
        raise ValueError(
                f"Argument 'min_samples_max' (got {min_samples_max}) cannot be negative or 0!"
        )
    if min_samples_max <= min_samples_min:
        raise ValueError(
                f"Argument 'min_samples_max' (got {min_samples_max}) cannot be smaller than or equal to 'min_samples_min' (got {min_samples_min})"
        )

    results = []
    n_eps = int((eps_max - eps_min) / eps_step) + 1
    for min_samples in range(min_samples_min, min_samples_max + 1):
        for eps in np.linspace(eps_min, eps_max, num=n_eps):
            db = sklearn.cluster.DBSCAN(eps=eps, min_samples=min_samples, **kwargs)
            labels = db.fit_predict(x_features)
            results.append(tuple([db, labels]))

    return results

