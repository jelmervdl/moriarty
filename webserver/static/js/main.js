jQuery(function($) {
    "use strict"

    function closeButton() {
        return $('<button type="button" class="close"><span>&times;</span></button>');
    }

    $.fn.alert = function(message) {
        $('<div>')
            .addClass('alert alert-danger alert-dismissible')
            .append(closeButton().data('dismiss', 'alert'))
            .append($('<p>').text(' ' + message).prepend($('<strong>Error!</strong>')))
            .appendTo(this);
    };

    function stringifyTokens(tokens) {
        return $('<div>').addClass('tokenized').append($.map(tokens, function(token) {
            return $('<span>').addClass('token').text(token);
        }));
    }

    function stringifyParse(parse) {
        return stringifyStatement(parse);
    }

    function isType(type) {
        return function(arg) {
            return arg.type == type;
        };
    }

    function stringifyStatement(parse) {
        return $('<li>')
            .addClass('predicate')
            .append($('<strong>').text(parse.text))
            .append($('<ul>').addClass('source').append(parse.source ? stringifyStatement(parse.source) : null))
            .append($('<ul>').addClass('supports').append($.map(parse.args.filter(isType('support')), stringifyStatement)))
            .append($('<ul>').addClass('attacks').append($.map(parse.args.filter(isType('attack')), stringifyStatement)));
    }

    var globalIDCounter = 0;

    function networkifyParse(parse) {
        var $el = $('<div>').addClass('network');
        
        function extractADUs(adu, depth)
        {
            if (!adu.id)
                adu.id = ++globalIDCounter;

            var node = [{
                classes: adu.type,
                data: {
                    id: adu.id,
                    text: adu.text,
                    type: adu.type
                }
            }];

            var supports = adu.args.filter(isType('support')),
                attacks = adu.args.filter(isType('attack')),
                sources = adu.source ? [adu.source] : [];

            var supportEdges = $.map(supports, function(support) {
                return extractADUs(support, depth + 1)
                    .concat([{classes: 'support', data: {
                        source: support.id,
                        target: adu.id}}]);
            });

            var attackEdges = $.map(attacks, function(attack) {
                return extractADUs(attack, depth + 1)
                    .concat([{classes: 'attack', data: {
                        source: attack.id,
                        target: adu.id}}]);
            });

            var sourceEdges = $.map(sources, function(source) {
                return extractADUs(source, depth + 1)
                    .concat([{classes: 'source', data: {
                        source: source.id,
                        target: adu.id}}]);
            });

            return node.concat(supportEdges, attackEdges, sourceEdges);
        };

        var network = cytoscape({
            userZoomingEnabled: false,
            userPanningEnabled: false,
            boxSelectionEnabled: true,
            container: $el,
            elements: extractADUs(parse, 0),
            style: [ // the stylesheet for the graph
                {
                    selector: 'node',
                    style: {
                        'background-color': '#666',
                        'label': 'data(text)'
                    }
                },

                {
                    selector: 'node.support, node.attack',
                    style: {
                        'width': 3,
                        'height': 3,
                        'background-color': '#eee',
                        'label': '' // 'data(type)'
                    }
                },

                {
                    selector: 'edge',
                    style: {
                        'width': 3,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle'
                    }
                },

                {
                    selector: 'edge.support',
                    style: {
                        'target-arrow-color': 'green',
                        'target-arrow-shape': 'triangle'
                    }
                },

                {
                    selector: 'edge.attack',
                    style: {
                        'target-arrow-color': 'red',
                        'target-arrow-shape': 'circle'
                    }
                },

                {
                    selector: 'edge.source',
                    style: {
                        'target-arrow-shape': 'none'
                    }
                }
            ],

            layout: {
                name: 'cose',
            }
        });

        setTimeout(function() {
            network.resize();
            network.layout();
        }, 50);

        return $el;
    }

    function parseSentence(sentence) {
        $.get($('#parse-sentence-form').attr('action'), {sentence: sentence}, 'json')
            .success(function(response) {
                $('<div>')
                    .appendTo('#parses')
                    .addClass('parse panel panel-default')
                    .append($('<div class="panel-heading">')
                        .append(closeButton())
                        .append(stringifyTokens(response.tokens))
                    )
                    .append($('<div class="panel-body">')
                        .append($('<ul>').append($.map(response.parses, function(parse) {
                            return stringifyParse(parse).append(networkifyParse(parse));
                        })))
                    );
            })
            .error(function(response) {
                try {
                    $('body > .container').alert(response.responseJSON.error);
                } catch (e) {
                    $('body > .container').alert("Something went wrong on the server.");
                }
            });
    }

    $('#parses').on('click', 'button.close', function(e) {
        e.preventDefault();
        $(this).closest('.parse').remove();
    });

    $('#parse-sentence-form').submit(function(e) {
        e.preventDefault();
        var sentence = $(this).find('input[name=sentence]').val();
        parseSentence(sentence);
    });

    $('#example-sentences').on('click', 'li', function(e) {
        e.preventDefault();
        var sentence = $(e.target).text();
        parseSentence(sentence);
    });
});