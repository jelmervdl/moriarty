customElements.define('x-tab-panel', class extends HTMLElement {
	static get observedAttributes() {
		return ['selected-index'];
	}

	constructor() {
		super();

		this.shadow = this.attachShadow({mode: 'open'});

		let stylesheet = document.createElement('link');
		stylesheet.rel = 'stylesheet';
		stylesheet.href = '/static/css/tab-panel.css';
		this.shadow.appendChild(stylesheet);

		this.labelList = document.createElement('ol');
		this.labelList.classList.add('tab-list');
		this.shadow.appendChild(this.labelList);

		this.panelContainer = document.createElement('div');
		this.panelContainer.classList.add('panel-container');
		this.shadow.appendChild(this.panelContainer);

		this.labelList.addEventListener('focusin', e => {
			let index = Array.from(this.labelList.childNodes).findIndex((node => node == e.target));
			this.selectedTab = this.tabs[index];
		});

		this.tabs = [];
	}

	createTab(name) {
		let tab = {};

		tab.panel = document.createElement('div');

		tab.label = document.createElement('li');
		tab.label.tabIndex = 0;
		tab.label.textContent = name;

		this.appendTab(tab);

		return tab.panel;
	}

	appendTab(tab) {
		this.tabs.push(tab);
		this.labelList.appendChild(tab.label);
		this.panelContainer.appendChild(tab.panel);

		if (this.tabs.length === 1)
			this.selectedTab = tab;
	}

	removeTab(tab) {
		this.labelList.removeChild(tab.label);
		this.panelContainer.removeChild(tab.panel);
		this.tabs = this.tabs.filter(tab_ => tab_ !== tab);
	}

	set selectedTab(selected) {
		this.tabs.forEach(tab => {
			tab.label.setAttribute('selected', tab == selected);
			tab.panel.setAttribute('selected', tab == selected);
		});
	}

	get selectedTab() {
		return this.panelContainer.querySelector('[selected=true]');
	}

	clear() {
		this.tabs.forEach(tab => this.removeTab(tab));
	}

	attributeChangedCallback(attr, oldValue, newValue) {
		switch (attr) {
			case 'selected-index':
				this.setActiveTab(this.tabs[i]);
		}
	}
});