jQuery(function($) {
    $.fn.alert = function(message) {
        $('<div>')
            .addClass('alert alert-danger alert-dismissible')
            .append($('<button type="button" class="close" data-dismiss="alert"><span>&times;</span></button>'))
            .append($('<p>').text(' ' + message).prepend($('<strong>Error!</strong>')))
            .appendTo(this);
    };

    function stringifyTokens(tokens) {
        return $('<li>').append($.map(tokens, function(token) {
            return $('<span>').addClass('token').text(token);
        }));
    }

    function stringifyParse(parse) {
        return $('<ol>').append($.map(parse, function(arg) {
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

    window.stringifyParse = stringifyParse;

    $('#parse-sentence-form').submit(function(e) {
        e.preventDefault();
        var sentence = $(this).find('input[name=sentence]').val();
        $.post($(this).attr('action'), {sentence: sentence}, 'json')
            .success(function(response) {
                $('#parses')
                    .append(stringifyTokens(response.tokens))
                    .append($.map(response.parses, stringifyParse));
            })
            .error(function(response) {
                try {
                    $('body > .container').alert(response.responseJSON.error);
                } catch (e) {
                    $('body > .container').alert("Something went wrong on the server.");
                }
            });
    });
});