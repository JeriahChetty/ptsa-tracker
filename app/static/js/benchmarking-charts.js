// Company Benchmarking History Charts
// This file handles the chart initialization for the benchmarking history page

document.addEventListener('DOMContentLoaded', function() {
    // Get chart containers
    const yearChartElement = document.getElementById('yearDistributionChart');
    const entryChartElement = document.getElementById('entrySourceChart');
    
    if (!yearChartElement || !entryChartElement) {
        console.warn('Chart elements not found');
        return;
    }

    // Year Distribution Chart
    const yearCtx = yearChartElement.getContext('2d');
    
    // Get data from data attributes
    const yearLabels = JSON.parse(yearChartElement.dataset.yearLabels || '[]');
    const yearData = JSON.parse(yearChartElement.dataset.yearData || '[]');
    
    new Chart(yearCtx, {
        type: 'bar',
        data: {
            labels: yearLabels,
            datasets: [{
                label: 'Records',
                data: yearData,
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Entry Source Chart
    const entryCtx = entryChartElement.getContext('2d');
    
    // Get data from data attributes
    const adminCount = parseInt(entryChartElement.dataset.adminCount || '0');
    const companyCount = parseInt(entryChartElement.dataset.companyCount || '0');
    
    // Only create chart if we have data
    if (adminCount > 0 || companyCount > 0) {
        new Chart(entryCtx, {
            type: 'doughnut',
            data: {
                labels: ['Admin Entered', 'Company Entered'],
                datasets: [{
                    data: [adminCount, companyCount],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(23, 162, 184, 0.8)'
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(23, 162, 184, 1)'
                    ],
                    borderWidth: 2
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
    } else {
        // Show message if no data
        const container = entryChartElement.parentElement;
        container.innerHTML = '<div class="text-center text-muted py-4"><i class="fas fa-chart-pie fa-2x mb-2"></i><br>No data available</div>';
    }
});