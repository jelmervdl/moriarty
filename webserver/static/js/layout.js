Graph.prototype.layout = function()
{
	var graph = this;

	function layoutClaim(claim) {
		let incoming = graph.findRelations({target: claim});

		let layout = new Layout(Layout.VERTICAL);

		layout.add(claim);

		if (incoming.length > 0) {
			let relationLayout = new Layout(Layout.HORIZONTAL);
			layout.add(relationLayout);

			relationLayout.addAll(incoming.map(layoutRelation));
		}

		return layout;
	}

	function layoutRelation(relation) {
		var layout = new Layout(Layout.VERTICAL);

		let incoming = graph.findRelations({target: relation});

		if (incoming.length > 0) {
			let vl = new Layout(Layout.VERTICAL);
			vl.addAll(incoming.map(layoutRelation));

			let hl = new Layout(Layout.HORIZONTAL);
			hl.add(new Spacer(200, 20));
			hl.add(vl);

			layout.add(hl);
		} else {
			layout.add(new Spacer(20, 50));
		}

		layout.add(layoutClaim(relation.claim));

		return layout;
	}
	
	// Find all claims that have no outgoing relations, and that thus wouldn't be found
	// by iterating all relations as done by layoutClaim.
	var roots = this.findRootClaims();
	
	var layout = new Layout(Layout.HORIZONTAL);

	// Make sure the claims themselves know how large they are. Could be done after these
	// steps, layout is lazy and only needs to know the dimensions once Layout.apply is called.
	this.updateClaimSizes();

	roots.map(layoutClaim).forEach(layout.add, layout);

	return layout;
}

function Spacer(width, height) {
	this.x = null;
	this.y = null;
	this.width = width;
	this.height = height;
}

Spacer.prototype.setPosition = function(x, y) {
	// no-op

	// ... but setting these anyway for the debug drawing
	this.x = x;
	this.y = y;
};

function Layout(direction)
{
	this.direction = direction;
	this.elements = [];
	this.parent = null;
}

Layout.HORIZONTAL = 1;
Layout.VERTICAL = 2;

Layout.spacing = {
	horizontal: 10,
	vertical: 10
};

Layout.prototype = {
	add(box) {
		if (box instanceof Layout)
			box.parent = this;

		this.elements.push(box);
	},

	addAll(boxes) {
		boxes.forEach(this.add, this);
	},

	apply() {
		this.setPosition(20, 20);
	},

	setPosition(x, y) {
		// save x & y for rendering
		this.x = x;
		this.y = y;

		var spacing = Layout.spacing;

		// Then the left to right sweep
		switch (this.direction) {
			case Layout.HORIZONTAL:
				let dx = 0;
				let height = this.height;
				this.elements.forEach(function(el) {
					// Align horizontally, so centre vertically
					el.setPosition(x + dx, y + (height - el.height) / 2);
					dx += el.width + spacing.horizontal;
				});
				break;

			case Layout.VERTICAL:
				let dy = 0;
				let width = this.width;
				this.elements.forEach(function(el) {
					// Same, but now centre horizontally
					el.setPosition(x + (width - el.width) / 2, y + dy);
					dy += el.height + spacing.vertical;
				});
				break;
		}
	},
	
	drawOutline(graph, depth) {
		var ctx = graph.context,
		    scale = graph.style.scale;

		if (depth === undefined)
			depth = 0;

		ctx.lineWidth = 1 * scale;
		ctx.strokeStyle = this.direction === Layout.HORIZONTAL ? 'red' : 'green';
		
		// Draw an extra outline for the selected claims
		ctx.strokeRect(
			scale * (this.x + 2 * depth),
			scale * (this.y + 2 * depth),
			scale * (this.width - 4 * depth),
			scale * (this.height - 4 * depth));

		this.elements.forEach(function(el) {
			if ('drawOutline' in el)
				el.drawOutline(graph, depth + 1);
		});
	},

	get width() {
		let widths = this.elements.map((el) => el.width);

		switch (this.direction) {
			case Layout.HORIZONTAL:
				// total width of all boxes plus spacing in between
				return widths.sum() + Math.max(this.elements.length - 1, 0) * Layout.spacing.horizontal;

			case Layout.VERTICAL:
				return widths.max();
		}
	},

	get height() {
		let heights = this.elements.map((el) => el.height);

		switch (this.direction) {
			case Layout.HORIZONTAL:
				return heights.max();

			case Layout.VERTICAL:
				// total heights of all the boxes plus spacing in between
				return heights.sum() + Math.max(this.elements.length - 1, 0) * Layout.spacing.vertical;
		}
	},

	get descendants() {
		// assert that any element only occurs once in the whole tree
		function extract(layout) {
			return layout.elements.map((el) => (el instanceof Layout) ? extract(el) : [el]).flatten();
		}

		return extract(this);
	}
}

function OutlinePainter(color) {
	return function(graph, depth) {
		var ctx = graph.context,
		    scale = graph.style.scale;

		if (depth === undefined)
			depth = 0;

		ctx.fillStyle = color;
		
		ctx.fillRect(
			scale * this.x,
			scale * this.y,
			scale * this.width,
			scale * this.height);
	};
}

// Add a few more outline drawing functions for easyness
Spacer.prototype.drawOutline = OutlinePainter('rgba(255, 0, 255, 0.5)');

Claim.prototype.drawOutline = OutlinePainter('rgba(255, 255, 0, 0.5)');