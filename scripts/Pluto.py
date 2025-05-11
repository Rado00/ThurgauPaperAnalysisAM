import plotly.express as px

fig = px.bar(x=["A", "B", "C"], y=[10, 20, 30])
fig.write_image("test_plot.png")  # This should work without freezing