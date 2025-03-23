import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Data
fleet_sizes = [4, 5, 6, 7, 8, 10, 12]
waiting_times = [524, 503, 469, 421, 359, 282, 241]
threshold = 480

# Determine adaptive grid spacing
x_step = max(1, (max(fleet_sizes) - min(fleet_sizes)) // len(fleet_sizes))
y_range = max(waiting_times) - min(waiting_times)
y_step = max(10, y_range // 10)  # Ensure a reasonable number of grid lines

# Set style
sns.set_style("whitegrid")
plt.figure(figsize=(10, 6))

# Plot
plt.plot(fleet_sizes, waiting_times, marker='o', linestyle='-', color='#FF5733', markersize=8, linewidth=2, label='Average Waiting Time')

# Annotate points
for i, txt in enumerate(waiting_times):
    plt.annotate(f"{txt}", (fleet_sizes[i], waiting_times[i]), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=12, fontweight='bold', color='black')

# Add threshold line
plt.axhline(y=threshold, color='darkred', linestyle='--', linewidth=2, label='8 Minutes Threshold')
plt.text(max(fleet_sizes) - 1, threshold + 5, "8 Minutes Threshold", color='darkred', fontsize=12, fontweight='bold')

# Labels and title
plt.xlabel("Fleet Size", fontsize=14, fontweight='bold', color='#1F618D')
plt.ylabel("Average Waiting Time (s)", fontsize=14, fontweight='bold', color='#1F618D')
plt.title("Impact of Fleet Size on Waiting Time - 01_Affeltrangen", fontsize=16, fontweight='bold', color='#34495E')
plt.legend()

# Adaptive grid settings
plt.xticks(np.arange(min(fleet_sizes), max(fleet_sizes) + x_step, x_step))
plt.yticks(np.arange(min(waiting_times) - y_step, max(waiting_times) + y_step, y_step))

plt.grid(True, linestyle='--', linewidth=0.7)

# Save the figure
plt.savefig("FleetSizeZone01.jpg")
plt.show()
