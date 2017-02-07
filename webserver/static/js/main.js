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
            .append($('<p>').css('white-space', 'pre-wrap').text(' ' + message).prepend($('<strong>Error!</strong>')));
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
            claims[claim.id] = graph.addClaim(claim.text);
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

    function parseSentence(sentence) {
        $.get($('#parse-sentence-form').attr('action'), {sentence: sentence}, 'json')
            .success(function(response) {
                console.log(response);
                $('#parses').prepend(
                    $('<div>')
                        .addClass('parse panel panel-default dismissible')
                        .append($('<div class="panel-heading">')
                            .append(closeButton())
                            .append(editButton(sentence))
                            .append(repeatButton(sentence))
                            .append(stringifyTokens(response.tokens))
                        )
                        .append($('<div class="list-group">')
                            .append($.map(response.parses, function(parse) {
                                return $('<div>')
                                    .addClass('list-group-item')
                                    .append(networkifyParse(parse))
                                    // .append($('<ul>')
                                    //     .append(stringifyParse(parse)));
                            }))
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