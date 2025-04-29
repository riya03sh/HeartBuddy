document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts on the page
    initRiskTrendChart();
    initRiskDistributionChart();
    initFeatureImportanceChart();
});

function initRiskTrendChart() {
    const ctx = document.getElementById('riskTrendChart');
    if (!ctx) return;

    // Assuming the labels and values are passed from Flask and available in the template
    const labels = JSON.parse(ctx.dataset.labels || '[]');
    const values = JSON.parse(ctx.dataset.values || '[]');

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Percentage',
                data: values,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function initRiskDistributionChart() {
    const ctx = document.getElementById('riskDistributionChart');
    if (!ctx) return;
    
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low', 'Medium', 'High'],
            datasets: [{
                data: [35, 45, 20],
                backgroundColor: [
                    '#28a745',
                    '#ffc107',
                    '#dc3545'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function initFeatureImportanceChart() {
    const ctx = document.getElementById('featureImportanceChart');
    if (!ctx) return;
    
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: JSON.parse(ctx.dataset.labels || '[]'),
            datasets: [{
                label: 'Feature Importance',
                data: JSON.parse(ctx.dataset.values || '[]'),
                backgroundColor: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Importance Score'
                    }
                }
            }
        }
    });
}