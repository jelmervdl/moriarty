from flask import Flask, render_template_string, request, jsonify, send_from_directory

from nlpg_grammar import parse, reverse
from nlpg_diagram import Diagram
from pprint import pprint

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

@app.route('/')
def app_index():
	with open('nlpg.html') as template:
		return render_template_string(template.read())

@app.route('/api/diagram', methods=['POST'])
def app_text_to_diagram():
	diagrams = list(text_to_diagrams(request.json['text']))
	return jsonify(diagrams=diagrams)

@app.route('/api/text', methods=['POST'])
def app_diagram_to_text():
	texts = list(diagram_to_texts(request.json['diagram']))
	return jsonify(texts=texts)

if __name__ == '__main__':
	app.run()