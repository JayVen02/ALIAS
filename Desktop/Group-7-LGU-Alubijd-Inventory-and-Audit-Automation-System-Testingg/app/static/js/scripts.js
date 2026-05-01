// Script for ALIAS Dashboard Charts
document.addEventListener('DOMContentLoaded', function () {

    // Default Chart
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                enabled: false
            }
        },
        scales: {
            x: {
                display: false
            },
            y: {
                display: false,
                beginAtZero: true,
                max: 100
            }
        },
        elements: {
            point: {
                radius: 0
            },
            line: {
                tension: 0.4,
                borderWidth: 2,
                borderColor: '#31449b'
            }
        },
        layout: {
            padding: 0
        }
    };

    // gradient
    function createGradient(ctx) {
        let gradient = ctx.createLinearGradient(0, 0, 0, 120);
        gradient.addColorStop(0, 'rgba(49, 68, 155, 0.5)'); // Deep blue transparent
        gradient.addColorStop(1, 'rgba(49, 68, 155, 0.0)'); // Fades to transparent
        return gradient;
    }

    // Chart 1: Emergency Supply
    const ctx1 = document.getElementById('emergencyChart').getContext('2d');
    new Chart(ctx1, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
            datasets: [{
                data: [10, 10, 40, 35, 70, 75, 85],
                fill: true,
                backgroundColor: createGradient(ctx1)
            }]
        },
        options: commonOptions
    });

    // Chart 2: Medical Supply
    const ctx2 = document.getElementById('medicalChart').getContext('2d');
    new Chart(ctx2, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
            datasets: [{
                data: [15, 20, 10, 50, 40, 60, 70],
                fill: true,
                backgroundColor: createGradient(ctx2)
            }]
        },
        options: commonOptions
    });

    // Chart 3: Veterinary Supply
    const ctx3 = document.getElementById('veterinaryChart').getContext('2d');
    new Chart(ctx3, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
            datasets: [{
                data: [40, 20, 60, 50, 40, 70, 80],
                fill: true,
                backgroundColor: createGradient(ctx3)
            }]
        },
        options: commonOptions
    });
});