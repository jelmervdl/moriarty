jQuery(function($) {
    function closeButton() {
        return $('<button type="button" class="close"><span>&times;</span></button>');
    }

    $.fn.alert = function(message) {
        $('<div>')
            .addClass('alert alert-danger alert-dismissible')
            .append(closeButton.data('dismiss', 'alert'))
            .append($('<p>').text(' ' + message).prepend($('<strong>Error!</strong>')))
            .appendTo(this);
    };

    function stringifyTokens(tokens) {
        return $('<div>').addClass('tokenized').append($.map(tokens, function(token) {
            return $('<span>').addClass('token').text(token);
        }));
    }

    function stringifyParse(parse) {
        return $('<ol>').addClass('parsed').append($.map(parse, function(arg) {
            return $('<li>').append(stringifyStatement(arg));
        }));
    }

    function stringifyStatement(parse) {
        console.log($.isArray(parse), parse);
        if ($.isArray(parse)) {
            return $('<span>')
                .addClass('predicate')
                .append($('<strong>').text(parse[0]))
                .append($.map(parse.slice(1), stringifyStatement));
        } else {
            return $('<span>').addClass('literal').text(parse);
        }
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
                    .append($('<div class="panel-body">').append($.map(response.parses, stringifyParse)));
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