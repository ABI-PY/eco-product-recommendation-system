// chart.js
// This script is used to render charts on result.html

function renderChart(carbon, recycle, material) {
    const ctx = document.getElementById('myChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Carbon', 'Recycle', 'Material'],
            datasets: [{
                label: 'Sustainability Score',
                data: [carbon, recycle, material],
                backgroundColor: ['#4caf50', '#ff9800', '#2196f3']
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10
                }
            }
        }
    });
}
