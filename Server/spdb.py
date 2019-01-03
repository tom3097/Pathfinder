from flask import Flask, render_template, request, url_for
app = Flask(__name__, static_url_path='/static')

@app.route('/')
@app.route('/index')
def index():
    return app.send_static_file('index.html')

@app.route('/target', methods=['POST'])
def define_target():
    if request.method == 'POST':
        address = get_address(
            request.form['inputlon'],
            request.form['inputlat']
        )
	
app.run(port=5000, debug=True)