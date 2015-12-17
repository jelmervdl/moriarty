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

function Rectangle(width, height, left, top) {
    this.width = width;
    this.height = height;
    this.left = left || 0;
    this.top = top || 0;
    this.children = [];
}

Rectangle.prototype.translate = function(left, top) {
    this.left += left;
    this.top += top;
};

function BoundingBox(source, width, height, left, top) {
    Rectangle.call(this, width, height, left, top);
    this.source = source;
}

BoundingBox.prototype = new Rectangle();

Node.prototype.supportedBy = function(sent) {
    if (sent.constructor !== Node)
        throw new Error("Nodes can only be supported by other nodes");
    var edge = new Edge(sent, this);
    this.edges.push(edge);
    return edge;
};

Node.prototype.size = function() {
    return new BoundingBox(this, 50, 20);
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
        ? new BoundingBox(this, 100, 20)
        : new BoundingBox(this, 20, 100);
};

Edge.prototype.boundingBox = function() {
    var size = this.size();

    size.source = this;

    if (this.edges.length) {
        var bbox = boundingBox(this.edges[0].from);
        if (this.orientation() == 'vertical') {
            // Edges are always coming in from the right if we are vertical,
            bbox.left += size.width;
            size.width += bbox.width;
            size.height = Math.max(size.height, bbox.height);
        } else {
            // or from the bottom if we are horizontal.
            bbox.top += size.height;
            size.width = Math.max(size.width, bbox.width);
            size.height += bbox.height;
        }
        size.children.push(bbox);
    }

    return size;
};

function boundingBox(node)
{
    var size = node.size();

    if (node.edges.length) {
        //var bbox = boundingBox(node.edges[0].from);
        var bbox = node.edges[0].boundingBox();
        if (node.edges[0].orientation() == 'horizontal') {
            size.width += bbox.width;
            size.height = Math.max(size.height, bbox.height);
        } else {
            size.width = Math.max(size.width, bbox.width);
            size.height += bbox.height;
        }
        size.children.push(bbox);
    }

    return size;
}

function sentence(text) {
    return new Node(text);
}

var jelmer_is_dief = sentence("Jelmer is een dief");
var jelmer_steelt = sentence("Jelmer heeft iets gestolen");
var stelers_zijn_dieven = sentence("Mensen die stelen zijn een dief");
var support = jelmer_is_dief.supportedBy(jelmer_steelt);
support.supportedBy(stelers_zijn_dieven);

console.log(boundingBox(jelmer_is_dief));