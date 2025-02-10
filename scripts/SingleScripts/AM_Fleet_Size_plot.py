import matplotlib.pyplot as plt
import seaborn as sns

# Data
fleet_sizes = [4, 5, 6, 7, 8, 10, 12]
waiting_times = [555, 518, 469, 435, 398, 323, 283]
threshold = 480

# Set style
sns.set_style("whitegrid")
plt.figure(figsize=(10, 6))


# Plot
plt.plot(fleet_sizes, waiting_times, marker='o', linestyle='-', color='#FF5733', markersize=8, linewidth=2, label='Average Waiting Time')

# Annotate points
for i, txt in enumerate(waiting_times):
    plt.annotate(f"{txt}", (fleet_sizes[i], waiting_times[i]), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=12, fontweight='bold', color='black')

# Add threshold line
plt.axhline(y=threshold, color='darkred', linestyle='--', linewidth=2, label='5 Minutes Threshold')
plt.text(1250, threshold + 5, "5 Minutes Threshold", color='darkred', fontsize=12, fontweight='bold')

# Labels and title
plt.xlabel("Fleet Size", fontsize=14, fontweight='bold', color='#1F618D')
plt.ylabel("Average Waiting Time (s)", fontsize=14, fontweight='bold', color='#1F618D')
plt.title("Impact of Fleet Size on Waiting Time", fontsize=16, fontweight='bold', color='#34495E')
plt.legend()

plt.xlim(900, max(fleet_sizes) + 100)

plt.savefig("FleetSizeZone01.jpg")