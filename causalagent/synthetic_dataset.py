import pandas as pd
import numpy as np
import random

# Set seed for reproducibility
np.random.seed(42)

# Define possible values
currencies = ["USD", "SGD", "HKD"]
amount_buckets = ["Less_than_10m_USD", "Between_10m_and_50m_USD", "More_than_50m_USD"]
margin_utilisation_categories = ["Low", "Medium", "High"]

# Tenor buckets with days range
tenor_buckets = {
    "0m": (0, 28),
    "1m": (29, 37),
    "3m": (84, 100),
    "6m": (171, 190),
    "1yr": (351, 375),
    "Other Tenors": (38, 83),  # We'll use this to include values not in the defined buckets
}

# Function to randomly assign a tenor bucket
def get_random_tenor_and_bucket():
    bucket = random.choice(list(tenor_buckets.keys()))
    tenor_range = tenor_buckets[bucket]
    tenor = np.random.randint(tenor_range[0], tenor_range[1] + 1)
    return tenor, bucket

# Function to assign margin based on category
def get_margin_from_category(category):
    if category == "Low":
        return round(np.random.uniform(0.0, 0.49), 2)
    elif category == "Medium":
        return round(np.random.uniform(0.5, 0.74), 2)
    else:
        return round(np.random.uniform(0.75, 1.0), 2)

# Generate synthetic dataset
num_rows = 1000
data = []

for _ in range(num_rows):
    currency = random.choice(currencies)
    amount_bucket = random.choice(amount_buckets)
    tenor, tenor_bucket = get_random_tenor_and_bucket()
    margin_category = random.choice(margin_utilisation_categories)
    margin_value = get_margin_from_category(margin_category)
    
    data.append({
        "Currency": currency,
        "Tenor": tenor,
        "Tenor Bucket": tenor_bucket,
        "Amount Bucket": amount_bucket,
        "Margin Utilisation Category": margin_category,
        "Margin Value": margin_value
    })

df = pd.DataFrame(data)

print(df.drop(["Margin Value", "Tenor"], axis=1, inplace=True))

df.to_csv("synthetic_dataset.csv", index=False)

