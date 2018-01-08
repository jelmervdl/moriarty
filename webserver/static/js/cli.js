#!/usr/bin/env node

/*
a = Socrates is mortal
b = assume He is a man
c = All men are mortal
x = assume b supports a
y = c supports x
*/

const fs = require('fs');
const readline = require('readline');
const Canvas = require('canvas');
const {Graph} = require('./graph.js');

// These add methods to prototypes. Quite ugly in this modular design...
require('./array.js');
require('./layout.js')(Graph);
require('./canvas.js')(Canvas.Context2d);

function main(input, output) {
    let canvas = new Canvas(200, 200, 'pdf');

    let graph = new Graph(canvas);

    const rl = readline.createInterface({
      input: input
    });

    rl.on('line', input => {
        graph.parse(input);
    });

    rl.on('close', () => {
        graph.layout().apply();
        graph.fit();
        graph.draw();

        // console.log(graph.relations);
    });

    graph.on('draw', () => {
        fs.writeFileSync(output, canvas.toBuffer());
    });
};

function usage(name) {
    console.log('Usage: haslgraph [-o <output>] <file>');
    process.exit(0);
}

let output = 'out.pdf';

let input = process.stdin;

for (var i = 2; i < process.argv.length; ++i) {
    switch (process.argv[i]) {
        case '-o':
        case '--output':
            if (process.argv.length > i + 1)
                output = process.argv[++i];
            else
                throw new Error('Missing output filename after ' + process.argv[i] + ' option');
            break;

        case '-Tpdf':
            break;

        case '-h':
        case '--help':
            usage(process.argv[0]);
            break;

        case '--':
            input = process.stdin;
            break;

        default:
            input = fs.createReadStream(process.argv[i], 'utf8');
            break;
    }
}

main(input, output);
