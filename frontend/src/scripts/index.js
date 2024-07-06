var map = L.map("map").setView([55.7558, 37.6176], 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
	attribution:
		'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	maxZoom: 18,
}).addTo(map);

var marker = L.marker([55.7558, 37.6176])
	.addTo(map)
	.bindPopup("Пример билборда")
	.openPopup();
