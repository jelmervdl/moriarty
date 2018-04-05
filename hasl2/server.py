import traceback
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, send_from_directory

from hasl2 import parse, reverse
from nlpg_diagram import Diagram


def text_to_diagrams(text):
	for arguments in parse(text):
		yield Diagram.from_arguments(arguments).to_object()


def diagram_to_texts(diagram):
	for tree in Diagram.from_object(diagram).to_arguments():
		for realisation in reverse(tree):
			yield realisation


app = Flask(__name__, static_folder='webserver/static')
app.secret_key = 'notrelevant'
app.debug = True

def handle_exceptions(fn):
	@wraps(fn)
	def wrapper(*args, **kwargs):
		try:
			return fn(*args, **kwargs)
		except Exception as error:
			traceback.print_exc()
			response = jsonify(error=str(error))
			response.status_code = 400
			return response
	return wrapper

@app.route('/')
def app_index():
	with open('nlpg.html') as template:
		return render_template_string(template.read())

@app.route('/api/diagram', methods=['POST'])
@handle_exceptions
def app_text_to_diagram():
	diagrams = list(text_to_diagrams(request.json['text']))
	return jsonify(diagrams=diagrams)

@app.route('/api/text', methods=['POST'])
@handle_exceptions
def app_diagram_to_text():
	texts = list(diagram_to_texts(request.json['diagram']))
	return jsonify(texts=texts)

if __name__ == '__main__':
	app.run(port=5001)
