jQuery(function($) {
    "use strict"

    function closeButton() {
        return $('<button type="button" class="close" aria-label="Close results" title="Close results"><span>&times;</span></button>');
    }

    function editButton(sentence) {
        return $('<button type="button" class="edit-sentence" aria-label="Edit sentence" title="Edit sentence"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></button>').data('sentence', sentence);
    }

    function repeatButton(sentence) {
        return $('<button type="button" class="repeat-sentence" aria-label="Repeat sentence" title="Repeat sentence"><span class="glyphicon glyphicon-repeat" aria-hidden="true"></span></button>').data('sentence', sentence);
    }

    $.fn.alert = function(message) {
        var $alert = $('<div>')
            .addClass('alert alert-danger alert-dismissible dismissible')
            .append(closeButton())
            .append($('<p>').text(' ' + message).prepend($('<strong>Error!</strong>')));
        $(this).prepend($alert);
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
            .append($('<ul>').addClass('source').append($.map(parse.sources || [], stringifyStatement)))
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
                sources = adu.sources || [];

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
                    selector: 'node.support, node.attack, node.compound',
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
        }, 100);

        return $el;
    }

    function parseSentence(sentence) {
        $.get($('#parse-sentence-form').attr('action'), {sentence: sentence}, 'json')
            .success(function(response) {
                $('#parses').prepend(
                    $('<div>')
                        .addClass('parse panel panel-default dismissible')
                        .append($('<div class="panel-heading">')
                            .append(closeButton())
                            .append(editButton(sentence))
                            .append(repeatButton(sentence))
                            .append(stringifyTokens(response.tokens))
                        )
                        .append($('<div class="panel-body">')
                            .append($('<ul>').append($.map(response.parses, function(parse) {
                                return stringifyParse(parse).append(networkifyParse(parse));
                            })))
                        )
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

    $('body').on('click', '.dismissible button.close', function(e) {
        e.preventDefault();
        $(this).closest('.dismissible').remove();
    });

    $('body').on('click', '.edit-sentence', function(e) {
        $('#parse-sentence-form input[name=sentence]').val($(this).data('sentence')).get(0).focus();
    });

    $('body').on('click', '.repeat-sentence',function(e) {
        parseSentence($(this).data('sentence'))
    })

    $('#parse-sentence-form').submit(function(e) {
        e.preventDefault();
        var sentence = $(this).find('input[name=sentence]').val();
        parseSentence(sentence);
    });

    $('body').on('click', '.example-sentence', function(e) {
        e.preventDefault();
        var sentence = $(e.target).text();
        parseSentence(sentence);
    });

    var stream = new EventSource('/api/stream');
    stream.onmessage = function(e) {
        console.info('Python:', e.data);
    };
});