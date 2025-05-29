import xml.etree.ElementTree as ET
import gzip
import matplotlib.pyplot as plt

# === Change this to your local path ===
network_file_path = "01_network_wDRT.xml.gz"
output_image_path = "drt_network_visualization.png"

# Containers
nodes = {}
links_with_drt = []
links_without_drt = []

# Parse the gzipped XML
with gzip.open(network_file_path, 'rt', encoding='utf-8') as f:
    tree = ET.parse(f)
root = tree.getroot()

# Extract node coordinates
for node in root.findall(".//node"):
    node_id = node.attrib["id"]
    x = float(node.attrib["x"])
    y = float(node.attrib["y"])
    nodes[node_id] = (x, y)

# Classify links based on modes (comma-separated)
for link in root.findall(".//link"):
    from_id = link.attrib["from"]
    to_id = link.attrib["to"]
    modes = link.attrib.get("modes", "").lower()
    mode_list = [m.strip() for m in modes.split(',') if m.strip()]
    if from_id in nodes and to_id in nodes:
        x = [nodes[from_id][0], nodes[to_id][0]]
        y = [nodes[from_id][1], nodes[to_id][1]]
        if "drt" in mode_list:
            links_with_drt.append((x, y))
        else:
            links_without_drt.append((x, y))

# Plotting
plt.figure(figsize=(20, 20), dpi=300)  # High-definition figure
for x, y in links_without_drt:
    plt.plot(x, y, color='lightgray', linewidth=0.5)
for x, y in links_with_drt:
    plt.plot(x, y, color='red', linewidth=0.7)

plt.title("DRT-enabled Links in Network (Red)", fontsize=16)
plt.xlabel("X Coordinate", fontsize=12)
plt.ylabel("Y Coordinate", fontsize=12)
plt.axis("equal")
plt.grid(True)
plt.tight_layout()

# Save to PNG with high resolution
plt.savefig(output_image_path, format='png', dpi=300)
plt.close()

print(f"Network visualization saved as '{output_image_path}'")
