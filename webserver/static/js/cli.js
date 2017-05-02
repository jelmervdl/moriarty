/*
a = Socrates is mortal
b = assume He is a man
c = All men are mortal
x = assume b supports a
y = c supports x
*/

const {Graph} = require('./graph.js');

function parse(input)
{
    let lines = input.split(/\r?\n/);

    let graph = new Graph(container);

    let variables = {};

    let rules = [
        {
            pattern: /^\s*([a-z]+)\s*:\s*(assume\s+)?([a-z]+\s+)+(supports|attacks)\s+([a-z]+)$/,
            processor: match => {
                let sources = match[3].split(/\s+/).map(name => variables[name]);
                let target = variables[match[5]];
                let type = match[4].substr(0, -1); // support | attack
                let relation = graph.addRelation(sources, target, type, {assumption: match[2] == 'assume'});
                variables[match[1]] = relation;
            }
        },
        {
            pattern: /^\s*([a-z]+)\s*:\s*(assume\s+)?(.+?)\s*$/,
            processor: match => {
                variables[match[1]] = graph.addClaim(match[3], {assumption: match[2] == 'assume'});
            }
        }
    ];

    lines.forEach(line => {
        for (const rule of rules) {
            let match = line.match(rule.pattern);
            if (match) {
                rule.processor(match, line);
                break;
            }
        }
    });

    return graph;
}

module.exports = (input) => {
    let graph = parse(input);
    return graph;
};