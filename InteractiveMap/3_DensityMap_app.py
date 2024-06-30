from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    # Render the map HTML
    with open('population_density_map.html') as f:
        map_html = f.read()
    return render_template_string(map_html)

if __name__ == '__main__':
    app.run(debug=True)
