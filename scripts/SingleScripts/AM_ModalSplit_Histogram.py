import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Define data
modes = ["Car", "Car Passenger", "Public Transport", "Bike", "Walk"]
microcensus = [48.8, 7.5, 6.2, 11.1, 26.3]  # Example values for Microcensus
synthetic = [44.7, 9.8, 8.4, 4.1, 32.9]  # Example values for Synthetic
simulation1 = [34.1, 8.9, 12.1, 5.3, 39.6]  # Example values for Simulation
simulation2 = [47, 10, 7.6, 11.4, 24]  # Example values for Simulation


# Define professional colors
colors = [ "#d62728", "#7f7f7f", "#72bcd4", "#0b3d91" ]  # Red, Gray, Light Blue, Dark Blue

# Create a figure
fig = go.Figure()

# Add bars for each dataset
fig.add_trace(go.Bar(
    x=modes, y=synthetic,
    name="Synthetic",
    marker_color=colors[1],
    text=synthetic, textposition="outside"
))

fig.add_trace(go.Bar(
    x=modes, y=simulation1,
    name="Baseline Simulation 0",
    marker_color=colors[2],
    text=simulation1, textposition="outside"
))

fig.add_trace(go.Bar(
    x=modes, y=simulation2,
    name="Baseline Simulation 59",
    marker_color=colors[3],
    text=simulation2, textposition="outside"
))
fig.add_trace(go.Bar(
    x=modes, y=microcensus,
    name="Microcensus",
    marker_color=colors[0],
    text=microcensus, textposition="outside"
))
# Customize layout
fig.update_layout(
    title="Mode Share by number of trips inside Thurgau - Calibration",
    xaxis_title="Mode of Transportation",
    yaxis_title="Percentage (%)",
    barmode="group",
    width=900,
    height=500,
    legend_title="Dataset"
)

# Show the plot
plt.savefig("ModalSplitCalib.jpg")
fig.show()
