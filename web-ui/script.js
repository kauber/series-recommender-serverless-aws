document.addEventListener('DOMContentLoaded', function () {
    fetch('/config.json')
        .then(response => response.json())
        .then(config => {
            const apiUrl = config.apiUrl; // Dynamically set API URL

            document.getElementById('search-form').addEventListener('submit', function (event) {
                event.preventDefault();

                const genre = document.getElementById('genre').value;
                const fromYear = document.getElementById('from-year').value;
                const toYear = document.getElementById('to-year').value;
                const country = document.getElementById('country').value;
                const seasons = document.getElementById('seasons').value;

                const queryParams = `?genre=${genre}&fromYear=${fromYear}&toYear=${toYear}&country=${country}&seasons=${seasons}`;
                const fullUrl = apiUrl + queryParams;

                const output = document.getElementById('output');
                output.innerHTML = "<p>Searching...</p>";

                fetch(fullUrl)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        output.innerHTML = '';
                        displayResults(data.results);
                    })
                    .catch(error => {
                        console.error("Error fetching data:", error);
                        output.innerHTML = "<p>An error occurred. Please try again.</p>";
                    });
            });

            function displayResults(results) {
                const output = document.getElementById('output');
                output.innerHTML = '';

                if (!results || results.length === 0) {
                    output.innerHTML = "<p>No results found.</p>";
                    return;
                }

                results.forEach(series => {
                    const seriesCard = document.createElement('div');
                    seriesCard.classList.add('series-card');

                    const poster = series['Poster Path']
                        ? `<img src="${series['Poster Path']}" alt="${series.Title}" class="poster">`
                        : `<div class="placeholder-poster">No Image</div>`;

                    seriesCard.innerHTML = `
                        ${poster}
                        <h3>${series.Title}</h3>
                        <p><strong>Year:</strong> ${series.Year}</p>
                        <p><strong>Country:</strong> ${series.Country}</p>
                        <p><strong>Description:</strong> ${series.Description}</p>
                        <p><strong>Vote Average:</strong> ${series['Vote Average']}</p>
                    `;
                    output.appendChild(seriesCard);
                });
            }
        })
        .catch(error => {
            console.error("Error loading configuration:", error);
            alert("Failed to load configuration. Please try again later.");
        });
});
