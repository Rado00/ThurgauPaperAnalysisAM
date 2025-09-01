import pandas as pd
import numpy as np
from collections import Counter

# Your data
df1_data = {
    'person': [1000102, 1000102, 1000102, 1000102, 1000269, 1000269, 1000297, 1000297, 1000691, 1000701],
    'mode': ['car', 'car', 'car', 'car', 'walk', 'car_passenger', 'pt', 'walk', 'bike', 'pt']
}
df2_data = {
    'person': [1000102, 1000102, 1000102, 1000102, 1000269, 1000269, 1000269, 1000297, 1000297, 1000919],
    'mode': ['bike', 'pt', 'walk', 'walk', 'car', 'pt', 'car_passenger', 'pt', 'walk', 'car_passenger']
}

df1 = pd.DataFrame(df1_data)
df2 = pd.DataFrame(df2_data)

print("=" * 60)
print("TRANSPORT MODE CHANGE ANALYSIS REPORT")
print("=" * 60)

# 1. Basic Statistics
print("\n1. BASIC STATISTICS")
print("-" * 30)
print(f"Month Ago - Total trips: {len(df1)}, Unique people: {df1['person'].nunique()}")
print(f"Current   - Total trips: {len(df2)}, Unique people: {df2['person'].nunique()}")

# 2. Mode Distribution Comparison
print("\n2. MODE DISTRIBUTION COMPARISON")
print("-" * 40)

# Count trips by mode for each period
mode_counts_old = df1['mode'].value_counts().sort_index()
mode_counts_new = df2['mode'].value_counts().sort_index()

# Create comparison dataframe
all_modes = sorted(set(df1['mode'].unique()) | set(df2['mode'].unique()))
comparison_df = pd.DataFrame({
    'Month_Ago': [mode_counts_old.get(mode, 0) for mode in all_modes],
    'Current': [mode_counts_new.get(mode, 0) for mode in all_modes],
}, index=all_modes)

comparison_df['Change'] = comparison_df['Current'] - comparison_df['Month_Ago']
comparison_df['Change_Pct'] = ((comparison_df['Current'] - comparison_df['Month_Ago']) /
                               comparison_df['Month_Ago'].replace(0, np.inf) * 100).round(1)

print(comparison_df)

# 3. Individual Person Analysis
print("\n3. INDIVIDUAL PERSON CHANGES")
print("-" * 35)

# Get people present in both periods
common_people = set(df1['person']) & set(df2['person'])
print(f"People tracked in both periods: {len(common_people)}")

for person in sorted(common_people):
    old_modes = df1[df1['person'] == person]['mode'].tolist()
    new_modes = df2[df2['person'] == person]['mode'].tolist()

    print(f"\nPerson {person}:")
    print(f"  Month ago: {old_modes} (Total: {len(old_modes)} trips)")
    print(f"  Current:   {new_modes} (Total: {len(new_modes)} trips)")

    # Mode frequency comparison for this person
    old_freq = Counter(old_modes)
    new_freq = Counter(new_modes)

    all_person_modes = set(old_modes) | set(new_modes)
    changes = []
    for mode in sorted(all_person_modes):
        old_count = old_freq.get(mode, 0)
        new_count = new_freq.get(mode, 0)
        if old_count != new_count:
            changes.append(f"{mode}: {old_count}→{new_count}")

    if changes:
        print(f"  Changes: {', '.join(changes)}")
    else:
        print("  Changes: No change in mode frequencies")

# 4. People who left/joined
print("\n4. PEOPLE WHO LEFT/JOINED")
print("-" * 32)

only_old = set(df1['person']) - set(df2['person'])
only_new = set(df2['person']) - set(df1['person'])

if only_old:
    print("People who left (present month ago, not current):")
    for person in sorted(only_old):
        modes = df1[df1['person'] == person]['mode'].tolist()
        print(f"  Person {person}: {modes}")

if only_new:
    print("People who joined (not present month ago, present now):")
    for person in sorted(only_new):
        modes = df2[df2['person'] == person]['mode'].tolist()
        print(f"  Person {person}: {modes}")

# 5. Mode Transition Matrix (for people in both periods)
print("\n5. MODE TRANSITION PATTERNS")
print("-" * 35)

transitions = []
for person in common_people:
    old_modes = df1[df1['person'] == person]['mode'].tolist()
    new_modes = df2[df2['person'] == person]['mode'].tolist()

    # Simple approach: compare most frequent mode
    old_primary = Counter(old_modes).most_common(1)[0][0]
    new_primary = Counter(new_modes).most_common(1)[0][0]
    transitions.append((old_primary, new_primary))

transition_counts = Counter(transitions)
print("Primary mode transitions (most frequent mode per person):")
for (old_mode, new_mode), count in transition_counts.most_common():
    if old_mode != new_mode:
        print(f"  {old_mode} → {new_mode}: {count} person(s)")

stable_count = sum(1 for (old, new) in transitions if old == new)
print(f"  Stable (no primary mode change): {stable_count} person(s)")

# 6. Summary Statistics
print("\n6. SUMMARY")
print("-" * 15)
print(
    f"• Most growing mode: {comparison_df.loc[comparison_df['Change'].idxmax()].name} (+{comparison_df['Change'].max()} trips)")
print(
    f"• Most declining mode: {comparison_df.loc[comparison_df['Change'].idxmin()].name} ({comparison_df['Change'].min()} trips)")
print(f"• Total trip change: {comparison_df['Change'].sum()} trips")
print(
    f"• People retention rate: {len(common_people)}/{df1['person'].nunique()} = {len(common_people) / df1['person'].nunique() * 100:.1f}%")