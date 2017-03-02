jQuery(function($) {
    "use strict"

    var grammars = $('#parse-sentence-form .grammar-dropdown input[name=grammar]').map(function() {
        return {
            name: $(this).val(),
            label: $.trim($(this).parent().text())
        };
    });

    function closeButton() {
        return $('<button type="button" class="close" aria-label="Close results" title="Close results"><span>&times;</span></button>');
    }

    function editButton(sentence) {
        return $('<button type="button" class="btn btn-hidden btn-xs edit-sentence" aria-label="Edit sentence" title="Edit sentence"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></button>').data('sentence', sentence);
    }

    function repeatButton(sentence, grammar) {
        return $('<div class="btn-group repeat-sentence">')
            .data('sentence', sentence)
            .append(
                $('<button type="button" class="btn btn-xs btn-hidden repeat-sentence-action" aria-label="Parse again" title="Parse again"><span class="glyphicon glyphicon-repeat" aria-hidden="true"></span></button>').data({'grammar': grammar}),
                $('<button type="button" class="btn btn-xs btn-hidden dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><span class="caret"></span><span class="sr-only">Toggle Dropdown</span></button>'),
                $('<ul class="dropdown-menu">').append(grammars.map(function() {
                    return $('<li>')
                        .append($('<a href="#" class="repeat-sentence-action">')
                            .text(this.label)
                            .data({'grammar': this.name}));
                }).toArray())
            );
    }

    $.fn.alert = function(message) {
        var $alert = $('<div>')
            .addClass('alert alert-danger alert-dismissible dismissible')
            .append(closeButton())
            .append($('<p>').css('white-space', 'pre-wrap').text(' ' + message).prepend($('<strong>Error!</strong>')));
        return $(this).prepend($alert);
    };

    function stringifyTokens(tokens) {
        return $('<div>').addClass('tokenized').append($.map(tokens, function(token, i) {
            return $('<span>').addClass('token').attr('data-pos', i + 1).text(token);
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
            .append($('<strong>').text(parse.repr).attr('title', parse.repr))
            .append($('<ul>').addClass('source').append($.map(parse.sources || [], stringifyStatement)))
            .append($('<ul>').addClass('supports').append($.map(parse.args.filter(isType('support')), stringifyStatement)))
            .append($('<ul>').addClass('attacks').append($.map(parse.args.filter(isType('attack')), stringifyStatement)));
    }

    var globalIDCounter = 0;

    function networkifyParse(parse) {
        var $el = $('<div>').addClass('network');
        
        var graph = new Graph($el.get(0));

        var claims = {}, relations = {};

        parse.claims.forEach(function(claim) {
            claims[claim.id] = graph.addClaim(claim.text, {assumption: claim.assumption});
        });

        // Make sure we first do all relations targeting claims, and only then
        // the ones targeting relations, so that the targets of the last group
        // already exists.
        parse.relations
            .sort(function(a, b) {
                var as = a.target.cls == 'claim' ? 0 : 1;
                var bs = b.target.cls == 'claim' ? 0 : 1;
                return as - bs;
            })
            .forEach(function(relation) {
                var sources = relation.sources.map(function(source) {
                    switch (source.cls) {
                        case 'claim':
                            return claims[source.id];
                        default:
                            throw new Error("Unknown type '" + source.cls + "'");
                    }
                });

                var target;

                switch (relation.target.cls) {
                    case 'claim':
                        target = claims[relation.target.id];
                        break;
                    case 'relation':
                        target = relations[relation.target.id];
                        break;
                    default:
                        throw new Error("Unknown type '" + relation.target.cls + "'");
                }

                relations[relation.id] = graph.addRelation(sources, target, relation.type);
            });

        graph.layout().apply();

        graph.fitVertically(10);

        graph.on('drop', function() {
            graph.fitVertically(10);
        });

        $el.data('graph', graph);

        return $el;
    }

    function parsePanel(sentence, response)
    {
        return $('<div>')
            .addClass('parse panel panel-default dismissible')
            .append($('<div class="panel-heading">')
                .append(closeButton())
                .append(editButton(sentence))
                .append(repeatButton(sentence, response.grammar || null))
                .append(stringifyTokens(response.tokens || [])));
    }

    function parseSentence(sentence, grammar) {
        $.get($('#parse-sentence-form').attr('action'), {sentence: sentence, grammar: grammar}, 'json')
            .always(function(response, status) {
                // No consistency :(
                if (status == 'error')
                    response = response.responseJSON || {};

                var panel = parsePanel(sentence, response);
                $('#parses').prepend(panel);
                
                switch (status) {
                    case 'success':
                        panel.append($('<div class="list-group">')
                            .append($.map(response.parses, function(parse) {
                                return $('<div>')
                                    .addClass('list-group-item')
                                    .append(networkifyParse(parse))
                                    // .append($('<ul>')
                                    //     .append(stringifyParse(parse)));
                            }))
                        );
                        break;

                    default:
                        try {
                            panel.append($('<div class="panel-body">').alert(response.error));
                            var match = response.error.match(/\(at position (\d+)\)/);
                            if (match)
                                panel.find('[data-pos=' + match[1] + '].token').addClass('bg-danger');
                        } catch (e) {
                           panel.append($('<div class="panel-body">').alert("Something went wrong on the server."));
                        }
                        break;
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

    $('body').on('click', '.repeat-sentence .repeat-sentence-action', function(e) {
        parseSentence($(this).closest('.repeat-sentence').data('sentence'), $(this).data('grammar'));
        e.preventDefault();
    });

    $('#parse-sentence-form').on('change', 'input[name=grammar]', function(e) {
        $('#parse-sentence-form .current-grammar').text($(this).val());
    });

    $('#parse-sentence-form').submit(function(e) {
        e.preventDefault();
        var sentence = $(this).find('input[name=sentence]').val();
        var grammar = $(this).find('input[name=grammar]:checked').val();
        parseSentence(sentence, grammar);
    });

    $('body').on('click', '.example-sentence', function(e) {
        e.preventDefault();
        var sentence = $(e.target).text();
        var grammar = $('#parse-sentence-form input[name=grammar]:checked').val();
        parseSentence(sentence, grammar);
    });

    var stream = new EventSource('/api/stream');
    stream.onmessage = function(e) {
        console.info('Python:', e.data);
    };
});