document.addEventListener("DOMContentLoaded", function () {
	// Создадим карту с центром в Москве
	var map = L.map("map").setView([55.7558, 37.6176], 10);

	// Добавим тайлы OpenStreetMap в качестве фона карты
	L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
		attribution:
			'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	}).addTo(map);

	// Пример данных (заглушки для билбордов)
	var billboards = [
		{ lon: 37.618423, lat: 55.751244, azimuth: 0, label: "Билборд 1" },
		{ lon: 37.620393, lat: 55.753559, azimuth: 90, label: "Билборд 2" },
		{ lon: 37.622503, lat: 55.754764, azimuth: 180, label: "Билборд 3" },
	];

	// Добавим маркеры на карту для каждого билборда
	billboards.forEach(function (billboard) {
		L.marker([billboard.lat, billboard.lon])
			.addTo(map)
			.bindPopup(`${billboard.label}`)
			.openPopup();
	});

	const optimizeButton = document.getElementById("optimize-button");
	optimizeButton.addEventListener("click", optimize);

	function optimize() {
		// Очищаем предыдущие результаты перед обновлением
		clearResults();

		// Собираем параметры фильтров
		var gender = document.getElementById("gender").value;
		var ageMin = document.getElementById("age-min").value;
		var ageMax = document.getElementById("age-max").value;
		var income = document.getElementById("income").value;
		var budget = document.getElementById("budget").value;
		var selectedDistricts = Array.from(
			document.getElementById("districts").selectedOptions
		).map((option) => option.value);

		// Выводим параметры в консоль для демонстрации
		console.log("Gender:", gender);
		console.log("Age Range:", ageMin, "-", ageMax);
		console.log("Income:", income);
		console.log("Budget:", budget);
		console.log("Selected Districts:", selectedDistricts);

		// Оптимизация секторов (заглушка)
		var sectors = [
			{ id: 1, name: "Сектор 1", coverage: 0.65 },
			{ id: 2, name: "Сектор 2", coverage: 0.78 },
			{ id: 3, name: "Сектор 3", coverage: 0.52 },
		];

		// Выводим результаты оптимизации на страницу
		var sectorResults = document.getElementById("sector-results");
		sectors.forEach(function (sector) {
			var li = document.createElement("li");
			li.textContent = `${sector.name}: Охват ${Math.round(
				sector.coverage * 100
			)}%`;
			sectorResults.appendChild(li);
		});

		// Прогноз охвата по точкам (заглушка)
		var points = [
			{ lon: 37.618423, lat: 55.751244, coverage: 0.72 },
			{ lon: 37.620393, lat: 55.753559, coverage: 0.81 },
			{ lon: 37.622503, lat: 55.754764, coverage: 0.63 },
		];

		// Выводим результаты прогноза на страницу
		var pointResults = document.getElementById("point-results");
		points.forEach(function (point) {
			var li = document.createElement("li");
			li.textContent = `Точка (${point.lon}, ${point.lat}): Охват ${Math.round(
				point.coverage * 100
			)}%`;
			pointResults.appendChild(li);
		});
	}

	// Очистка результатов
	function clearResults() {
		var sectorResults = document.getElementById("sector-results");
		var pointResults = document.getElementById("point-results");
		sectorResults.innerHTML = "";
		pointResults.innerHTML = "";
	}

	// Добавим районы для выбора
	var districts = [
		"Академический",
		"Алексеевский",
		"Алтуфьевский",
		"Арбат",
		"Аэропорт",
		"Бабушкинский",
		"Басманный",
		"Беговой",
		"Бескудниковский",
		"Бибирево",
	];

	var districtsSelect = document.getElementById("districts");

	districts.forEach(function (district) {
		var option = document.createElement("option");
		option.value = district.toLowerCase();
		option.textContent = district;
		districtsSelect.appendChild(option);
	});
});
