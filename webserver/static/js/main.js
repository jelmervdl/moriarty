jQuery(function($) {
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

    function stringifyStatement(parse) {
        return $('<li>')
            .addClass('predicate')
            .append($('<strong>').text(parse.adu))
            .append($('<ul>').addClass('supports').append($.map(parse.supports, stringifyStatement)))
            .append($('<ul>').addClass('attacks').append($.map(parse.attacks, stringifyStatement)))
            // .append($.map(parse.slice(1), stringifyStatement));
    }

    var globalIDCounter = 0;

    function networkifyParse(parse) {
        var $el = $('<div>').addClass('network');
        
        function extractADUs(adu)
        {
            if (!adu.id)
                adu.id = ++globalIDCounter;

            var node = [{data: {
                id: adu.id,
                label: adu.adu
            }}];

            var supportEdges = $.map(adu.supports, function(support) {
                return extractADUs(support)
                    .concat([{classes: 'support', data: {
                        source: support.id,
                        target: adu.id}}]);
            });

            var attackEdges = $.map(adu.attacks, function(attack) {
                return extractADUs(attack)
                    .concat([{classes: 'attack', data: {
                        source: attack.id,
                        target: adu.id}}]);
            });

            return node.concat(supportEdges, attackEdges);
        };

        console.log(extractADUs(parse));

        var network = cytoscape({
            userZoomingEnabled: false,
            userPanningEnabled: false,
            boxSelectionEnabled: false,
            container: $el,
            elements: extractADUs(parse),
            style: [ // the stylesheet for the graph
                {
                    selector: 'node',
                    style: {
                        'background-color': '#666',
                        'label': 'data(label)'
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
                    selector: '.support',
                    style: {
                        'target-arrow-color': 'green',
                        'target-arrow-shape': 'triangle'
                    }
                },

                {
                    selector: '.attack',
                    style: {
                        'target-arrow-color': 'red',
                        'target-arrow-shape': 'circle'
                    }
                }
            ],

            layout: {
                name: 'grid',
                rows: 1
            }
        });

        setTimeout(function() {
            network.resize();
            network.layout({name: 'grid'});
        }, 50);

        return $el;
    }

    function graphifyParse(parse) {
        var roots = [];
        var sent;
        for (var i = 0; i < parse.length; ++i) {
            switch (parse[i][0]) {
                case 'because':
                    var cause = sentence(parse[i][1]);
                    var effect = sentence(parse[i][2]);
                    roots.push(cause);
                    sent = cause.supportedBy(effect);
                    break;
                case 'rule':
                    if (sent) {
                        var rule = sentence(parse[i]);
                        sent = sent.supportedBy(rule);
                    }
                    break;
            }
        }
        return $.map(roots, function(sent) {
            var graph = sent.boundingBox().render();
            return $('<div>')
                .addClass('well')
                .css({'position': 'relative'})
                .width(parseInt(graph.style.width) * 2)
                .height(parseInt(graph.style.height) * 2)
                .append(graph);
        });
    }

    function parseSentence(sentence) {
        $.post($('#parse-sentence-form').attr('action'), {sentence: sentence}, 'json')
            .success(function(response) {
                $('<div>')
                    .appendTo('#parses')
                    .addClass('parse panel panel-default')
                    .append($('<div class="panel-heading">')
                        .append(closeButton())
                        .append(stringifyTokens(response.tokens))
                    )
                    .append($('<div class="panel-body">')
                        .append($('<ul>').append($.map(response.parses, stringifyParse)))
                        .append(networkifyParse(response.parses[response.parses.length - 1]))
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