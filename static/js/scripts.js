(function () {
    'use strict';

    // ── Dashboard Charts ───────────────────────────
    window.initDashboardCharts = function() {
        const emergencyCtx = document.getElementById('emergencyChart');
        if (!emergencyCtx) return;

        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: true }
            },
            scales: {
                x: { display: true, grid: { display: false } },
                y: { display: true, beginAtZero: true, max: 100 }
            }
        };

        function createGradient(ctx) {
            let gradient = ctx.createLinearGradient(0, 0, 0, 120);
            gradient.addColorStop(0, 'rgba(49, 68, 155, 0.5)');
            gradient.addColorStop(1, 'rgba(49, 68, 155, 0.0)');
            return gradient;
        }

        // Chart 1: Emergency Supply
        new Chart(emergencyCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                datasets: [{
                    data: [10, 10, 40, 35, 70, 75, 85],
                    fill: true,
                    backgroundColor: createGradient(emergencyCtx.getContext('2d')),
                    borderColor: '#31449b',
                    tension: 0.4
                }]
            },
            options: commonOptions
        });

        // Chart 2: Medical Supply
        const medicalCtx = document.getElementById('medicalChart');
        if (medicalCtx) {
            new Chart(medicalCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                    datasets: [{
                        data: [15, 20, 10, 50, 40, 60, 70],
                        fill: true,
                        backgroundColor: createGradient(medicalCtx.getContext('2d')),
                        borderColor: '#31449b',
                        tension: 0.4
                    }]
                },
                options: commonOptions
            });
        }

        // Chart 3: Veterinary Supply
        const veterinaryCtx = document.getElementById('veterinaryChart');
        if (veterinaryCtx) {
            new Chart(veterinaryCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
                    datasets: [{
                        data: [40, 20, 60, 50, 40, 70, 80],
                        fill: true,
                        backgroundColor: createGradient(veterinaryCtx.getContext('2d')),
                        borderColor: '#31449b',
                        tension: 0.4
                    }]
                },
                options: commonOptions
            });
        }
    };

    // ── Initialization ─────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
        // Any global init logic goes here
    });

})();