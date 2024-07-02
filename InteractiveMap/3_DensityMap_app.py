from flask import Flask, render_template_string
import webbrowser
import threading

app = Flask(__name__)

@app.route('/')
def index():
    # Render the map HTML
    with open('population_density_map.html') as f:
        map_html = f.read()
    return render_template_string(map_html)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Start the browser in a separate thread
    threading.Timer(1, open_browser).start()
    # Run the Flask app without reloader
    app.run(debug=True, use_reloader=False)
