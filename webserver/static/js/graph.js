function Node(text) {
    this.text = text;
    this.edges = [];
}

function Edge(from, to) {
    if (from.constructor !== Node)
        throw new Error("Edges are always coming from nodes");

    if (to.constructor !== Node && to.constructor !== Edge)
        throw new Error("Edges should point to either nodes or other edges");

    this.from = from;
    this.to = to;
    this.edges = [];
}

function Rectangle(width, height, left, top, data) {
    this.width = width;
    this.height = height;
    this.left = left || 0;
    this.top = top || 0;
    this.data = data;
}

Rectangle.horizontal = function(boxes) {
    var box = new Rectangle(0, 0, 0, 0, []);
    for (var i = 0; i < boxes.length; ++i) {
        box.data.push(boxes[i].translate(box.width, 0));
        box.width += boxes[i].width;
        box.height = Math.max(box.height, boxes[i].height);
    }
    for (var i = 0; i < box.data.length; ++i) {
        if (box.data[i].data.constructor === Array)
            box.data[i].top = (box.height - box.data[i].data[0].height) / 2;
        else
            box.data[i].top = (box.height - box.data[i].height) / 2;
    }
    return box;
};

Rectangle.vertical = function(boxes) {
    var box = new Rectangle(0, 0, 0, 0, []);
    for (var i = 0; i < boxes.length; ++i) {
        box.data.push(boxes[i].translate(0, boxes[i].height));
        box.width  = Math.max(box.width, boxes[i].width);
        box.height += boxes[i].height;
    }
    for (var i = 0; i < box.data.length; ++i) {
        if (box.data[i].data.constructor === Array)
            box.data[i].left = (box.width - box.data[i].data[0].width) / 2;
        else
            box.data[i].left = (box.width - box.data[i].width) / 2;
    }
    return box;
};

Rectangle.prototype.translate = function(left, top) {
    var rect = new Rectangle(
        this.width, this.height,
        this.left + left, this.top + top,
        this.data);
    return rect;
};

Node.prototype.supportedBy = function(sent) {
    if (sent.constructor !== Node)
        throw new Error("Nodes can only be supported by other nodes");
    var edge = new Edge(sent, this);
    this.edges.push(edge);
    return edge;
};

Node.prototype.size = function() {
    return new Rectangle(200, 50, 0, 0, this);
};

Node.prototype.boundingBox = function() {
    var size = this.size();
    if (this.edges.length) {
        var bbox = this.edges[0].boundingBox();
        if (this.edges[0].orientation() == 'horizontal') {
            size = Rectangle.horizontal([size, bbox]);
        } else {
            size = Rectangle.vertical([size, bbox]);
        }
    }
    return size;
};

Edge.prototype.supportedBy = function(sent) {
    var edge = new Edge(sent, this);
    this.edges.push(edge);
    return edge;
};

Edge.prototype.orientation = function() {
    return this.to.constructor === Edge ? 'horizontal' : 'vertical';
};

Edge.prototype.size = function() {
    return this.orientation() == 'horizontal'
        ? new Rectangle(100, 20, 0, 0, this)
        : new Rectangle(20, 100, 0, 0, this);
};

Edge.prototype.boundingBox = function() {
    var size = this.size();

    size.source = this;

    if (this.edges.length) {
        var bboxEdge = this.edges[0].boundingBox();
        //var bboxNode = this.edges[0].from.boundingBox();

        if (this.orientation() == 'vertical') {
            // Edges are always coming in from the right if we are vertical,
            size = Rectangle.horizontal([size, bboxEdge]);
        } else {
            // or from the bottom if we are horizontal.
            size = Rectangle.vertical([size, bboxEdge]);
        }
    }

    var bboxNode = this.from.boundingBox();
    if (this.orientation() == 'vertical')
        size = Rectangle.vertical([size, bboxNode]);
    else
        size = Rectangle.horizontal([size, bboxNode]);

    return size;
};

Rectangle.prototype.render = function() {
    var div = document.createElement('div');
    div.style.position = 'absolute';
    div.style.width = this.width + 'px';
    div.style.height = this.height + 'px';
    div.style.top = this.top + 'px';
    div.style.left = this.left + 'px';

    if (this.data && this.data.constructor === Array) {
        for (var i = 0; i < this.data.length; ++i) {
            if ('render' in this.data[i]) {
                div.appendChild(this.data[i].render());
            }
        }
    } else if (this.data && 'render' in this.data) {
        div.appendChild(this.data.render());
    }

    return div;
};

Node.prototype.render = function() {
    var span = document.createElement('span');
    span.className = 'arg-node';
    span.appendChild(document.createTextNode(this.text));
    return span;
};

Edge.prototype.render = function() {
    var arrow = document.createElement('span');
    arrow.className = 'arg-arrow';
    arrow.appendChild(document.createTextNode('o'));

    if (this.orientation() == 'horizontal') {
        arrow.appendChild(document.createTextNode('–––––––––––––'));
    } else {
        for (var i = 0; i < 4; ++i) {
            arrow.appendChild(document.createElement('br'));
            arrow.appendChild(document.createTextNode('|'));
        }
    }

    return arrow;
};

function sentence(text) {
    return new Node(text);
}

/*
var jelmer_is_dief = sentence("Jelmer is een dief");
var jelmer_steelt = sentence("Jelmer heeft iets gestolen");
var stelers_zijn_dieven = sentence("Mensen die stelen zijn een dief");
var support = jelmer_is_dief.supportedBy(jelmer_steelt);
support.supportedBy(stelers_zijn_dieven);

console.log(jelmer_is_dief.boundingBox());

var div = document.createElement('div');
div.className = 'bounding-box';
div.style.position = 'relative';
div.appendChild(jelmer_is_dief.boundingBox().render());
document.body.appendChild(div);
*/