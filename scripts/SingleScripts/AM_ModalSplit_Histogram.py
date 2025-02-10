import plotly.graph_objects as go

# Define data
modes = ["Car", "Car Passenger", "Public Transport", "Bike", "Walk"]
microcensus = [48.8, 7.5, 6.2, 11.1, 26.3]
synthetic = [44.7, 9.8, 8.4, 4.1, 32.9]
simulation1 = [34.1, 8.9, 12.1, 5.3, 39.6]
simulation2 = [47, 10, 7.6, 11.4, 24]

# Format numbers with one decimal place for consistency
microcensus = [f"{x:.1f}" for x in microcensus]
synthetic = [f"{x:.1f}" for x in synthetic]
simulation1 = [f"{x:.1f}" for x in simulation1]
simulation2 = [f"{x:.1f}" for x in simulation2]

# Define professional colors
colors = ["#d62728", "#7f7f7f", "#72bcd4", "#0b3d91"]  # Red, Gray, Light Blue, Dark Blue

# Create a figure
fig = go.Figure()

# Add bars for each dataset
fig.add_trace(go.Bar(
    x=modes, y=[float(x) for x in synthetic],
    name="Synthetic",
    marker_color=colors[1],
    text=synthetic, textposition="outside"
))

fig.add_trace(go.Bar(
    x=modes, y=[float(x) for x in simulation1],
    name="Baseline Simulation 0",
    marker_color=colors[2],
    text=simulation1, textposition="outside"
))

fig.add_trace(go.Bar(
    x=modes, y=[float(x) for x in simulation2],
    name="Baseline Simulation 59",
    marker_color=colors[3],
    text=simulation2, textposition="outside"
))

fig.add_trace(go.Bar(
    x=modes, y=[float(x) for x in microcensus],
    name="Microcensus",
    marker_color=colors[0],
    text=microcensus, textposition="outside"
))

# Customize layout
fig.update_layout(
    title="Mode Share by Number of Trips Inside Thurgau - Calibration",
    xaxis_title="Mode of Transportation",
    yaxis_title="Percentage (%)",
    barmode="group",
    width=900,
    height=500,
    legend_title="Dataset"
)

# **Make text much smaller**
fig.update_traces(textfont=dict(size=8, family="Arial"))  # Reduce size significantly

# **Save the figure as an image**
fig.write_image("ModalSplitCalib.jpg", scale=3)  # High-resolution image

# Show the plot
fig.show()
