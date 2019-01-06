from flask import Flask, render_template, request, url_for, jsonify, send_file
import json
import time
import io

app = Flask(__name__, static_url_path='/static')

@app.route('/')
@app.route('/index')
def index():
    return app.send_static_file('index.html')

@app.route('/style')
def style():
    return app.send_static_file('style.css')

@app.route('/script')
def script():
    return app.send_static_file('func.js')

@app.route('/favicon.ico')
def favicon():
    with open("static/favicon.jpg", 'rb') as bites:
        return send_file(
                     io.BytesIO(bites.read()),
                     attachment_filename='favicon.jpeg',
                     mimetype='image/jpg'
               )

@app.route('/find', methods = ['POST'])
def find_path():
	if request.method == 'POST':
		data = json.loads(request.data.decode('ascii'))

		start = data['viewparams']['start']
		end = data['viewparams']['end']

		##############################################################
		####### TUTAJ WYSZUKIWANIE SCIEZKI I ZWROCENIE WYNIKU ########
		##############################################################
		# testowe ponizej
		# print("start: {}, end: {}".format(start, end))
		time.sleep(3)

		path = []
		# path.append({'x':17.023,'y':51.52})
		path.append({'x':start['x'],'y':start['y']})
		path.append({'x':end['x'],'y':end['y']})
		# path.append({'x':18.48,'y':52.92})
		##############################################################

		return jsonify(path)

app.run(port=5000, debug=True)
