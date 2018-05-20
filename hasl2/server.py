import os
import traceback
from functools import wraps
from collections import OrderedDict
from flask import Flask, render_template_string, request, jsonify, send_from_directory

from hasl2.grammar import parse, reverse
from hasl2.diagram import Diagram
from parser import read_sentences

def text_to_diagrams(text):
	for arguments in parse(text):
		yield Diagram.from_arguments(arguments).to_object()


def diagram_to_texts(diagram):
	for tree in Diagram.from_object(diagram).to_arguments():
		for realisation in reverse(tree):
			yield realisation


app = Flask(__name__, static_folder='../hasl1/static')
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
	with open('hasl2/hasl2.html', 'rb') as template:
		return render_template_string(template.read().decode('utf-8'))

@app.route('/sentences')
def app_sentences():
	sentence_files = [os.path.join(os.path.dirname(__file__), '../evaluation.txt')]
	sentences = OrderedDict()
	for sentence_file in sentence_files:
	    with open(sentence_file, 'r') as fh:
	        sentences.update(read_sentences(fh))
	return jsonify(sentences);

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


def run():
	app.run(port=5001)


if __name__ == '__main__':
	run()	
