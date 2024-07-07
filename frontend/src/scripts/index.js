document.addEventListener("DOMContentLoaded", () => {
	const map = L.map("map").setView([55.7558, 37.6176], 12);

	L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
		attribution:
			'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
		maxZoom: 18,
	}).addTo(map);

	const priceListInput = document.getElementById("price-list");
	const targetForm = document.getElementById("target-form");

	priceListInput.addEventListener("change", handleFileSelect, false);
	targetForm.addEventListener("submit", handleFormSubmit, false);

	loadDistricts();

	function loadDistricts() {
		fetch("https://optimum-media-mock-5ec6b6b53ced.herokuapp.com/districts")
			.then((response) => response.json())
			.then((data) => {
				const districtsSelect = document.getElementById("districts");

				data.forEach((district) => {
					const option = document.createElement("option");
					option.value = district.id;
					option.textContent = district.name;
					districtsSelect.appendChild(option);
				});
			})
			.catch((error) => console.error("Ошибка загрузки районов:", error));
	}

	function handleFileSelect(event) {
		const file = event.target.files[0];
		if (file) {
			const formData = new FormData();
			formData.append("file", file);

			fetch(
				"https://optimum-media-mock-5ec6b6b53ced.herokuapp.com/load_prices",
				{
					method: "POST",
					body: formData,
				}
			)
				.then((response) => response.json())
				.then((data) => {
					const fileId = data.file_id;
					optimizeByFile(fileId);
				})
				.catch((error) => console.error("Ошибка загрузки файла:", error));
		}
	}

	function handleFormSubmit(event) {
		event.preventDefault();

		const formData = new FormData(targetForm);
		const gender = formData.get("gender");
		const ageMin = formData.get("age-min");
		const ageMax = formData.get("age-max");
		const income = formData.get("income");
		const budget = formData.get("budget");
		const districts = formData.getAll("districts");

		const params = {
			gender,
			age_from: ageMin,
			age_to: ageMax,
			campaign_budget: budget,
			districts: districts.join(","),
		};

		fetch(
			`https://optimum-media-mock-5ec6b6b53ced.herokuapp.com/optimize?${new URLSearchParams(
				params
			)}`,
			{
				method: "GET",
			}
		)
			.then((response) => response.json())
			.then((data) => {
				displayOptimizationResults(data);
			})
			.catch((error) =>
				console.error("Ошибка оптимизации по фильтрам:", error)
			);
	}

	function optimizeByFile(fileId) {
		fetch(
			`https://optimum-media-mock-5ec6b6b53ced.herokuapp.com/optimize_file?file_id=${fileId}`,
			{
				method: "GET",
			}
		)
			.then((response) => response.json())
			.then((data) => {
				displayOptimizationResults(data);
			})
			.catch((error) => console.error("Ошибка оптимизации по файлу:", error));
	}

	function displayOptimizationResults(data) {
		const points = data.points;
		const sectorResults = document.getElementById("sector-results");
		const pointResults = document.getElementById("point-results");

		sectorResults.innerHTML = "";
		pointResults.innerHTML = "";

		points.forEach((point, index) => {
			L.marker([point.lat, point.lon])
				.addTo(map)
				.bindPopup(
					`Оптимальная точка ${index + 1}: ${point.lat}, ${
						point.lon
					} - Азимут: ${point.azimuth}`
				);

			const pointItem = document.createElement("li");
			pointItem.textContent = `Оптимальная точка ${index + 1}: ${point.lat}, ${
				point.lon
			} - Азимут: ${point.azimuth}`;
			pointResults.appendChild(pointItem);
		});

		const sectors = data.sectors;
		sectors.forEach((sector, index) => {
			const sectorItem = document.createElement("li");
			sectorItem.textContent = `Сектор ${index + 1}: ${
				sector.name
			} - Оценка охвата: ${sector.coverage}`;
			sectorResults.appendChild(sectorItem);
		});
	}
});
