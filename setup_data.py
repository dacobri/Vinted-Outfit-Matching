import pandas as pd
import random

# Read CSV with error handling
df = pd.read_csv('data/styles.csv', on_bad_lines='skip')

df['seller'] = [f"User{random.randint(1000, 9999)}" for _ in range(len(df))]
df['price'] = [random.randint(5, 150) for _ in range(len(df))]
df['condition'] = [random.choice(['New', 'Like new', 'Good', 'Fair']) for _ in range(len(df))]

df.to_csv('data/vinted_catalog.csv', index=False)
print(f"Created vinted_catalog.csv with {len(df)} items!")
