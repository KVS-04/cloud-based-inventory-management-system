/**
 * Dashboard Charts - Chart.js Integration
 * Uses fallback sample data when API is unavailable
 */

document.addEventListener('DOMContentLoaded', () => {
    initDashboardCharts();
});

/* --- Chart Color Palette --- */
const COLORS = {
    primary: '#4f46e5', primaryLight: '#6366f1', secondary: '#7c3aed',
    success: '#10b981', warning: '#f59e0b', danger: '#ef4444', info: '#3b82f6',
    palette: ['#4f46e5','#7c3aed','#10b981','#f59e0b','#ef4444','#3b82f6','#ec4899','#8b5cf6','#06b6d4','#84cc16']
};

/* --- Sample Fallback Data --- */
const SAMPLE = {
    months: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    inventoryTrends: {
        labels: ['Jan','Feb','Mar','Apr','May','Jun'],
        totalStock: [4500,4200,4800,5100,4900,5300],
        stockIn: [800,600,1200,900,700,1100],
        stockOut: [650,500,900,700,600,800]
    },
    salesOverview: {
        labels: ['Jan','Feb','Mar','Apr','May','Jun'],
        sales: [15000,18000,14000,22000,19500,25000],
        purchases: [12000,15000,11000,18000,16000,20000]
    },
    categories: {
        labels: ['Electronics','Clothing','Food','Home','Sports','Office'],
        data: [350,280,420,190,150,210]
    },
    topProducts: {
        labels: ['Laptop Pro','Wireless Mouse','USB Cable','Monitor 27"','Keyboard','Headphones','Webcam','Speaker','Tablet','Phone Case'],
        data: [450,380,350,320,290,270,250,230,210,190]
    }
};

function createGradient(ctx, color1, color2) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}

async function initDashboardCharts() {
    /* --- Inventory Trends Line Chart --- */
    const invCtx = document.getElementById('inventoryTrendsChart');
    if (invCtx) {
        let data = SAMPLE.inventoryTrends;
        try {
            const resp = await fetch('/api/dashboard/charts/inventory-trends');
            if (resp.ok) { const json = await resp.json(); if (json.data) data = json.data; }
        } catch(e) {}

        const ctx = invCtx.getContext('2d');
        new Chart(invCtx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Total Stock', data: data.totalStock,
                    borderColor: COLORS.primary, backgroundColor: 'rgba(79,70,229,0.1)',
                    tension: 0.4, fill: true, pointRadius: 4, pointHoverRadius: 6
                }, {
                    label: 'Stock In', data: data.stockIn,
                    borderColor: COLORS.success, backgroundColor: 'transparent',
                    tension: 0.4, borderDash: [5, 5], pointRadius: 3
                }, {
                    label: 'Stock Out', data: data.stockOut,
                    borderColor: COLORS.danger, backgroundColor: 'transparent',
                    tension: 0.4, borderDash: [5, 5], pointRadius: 3
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { usePointStyle: true, padding: 15, font: { family: 'Inter' } } } },
                scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' } }, x: { grid: { display: false } } }
            }
        });
    }

    /* --- Sales Overview Bar Chart --- */
    const salesCtx = document.getElementById('salesOverviewChart');
    if (salesCtx) {
        let data = SAMPLE.salesOverview;
        try {
            const resp = await fetch('/api/dashboard/charts/sales-trends');
            if (resp.ok) { const json = await resp.json(); if (json.data) data = json.data; }
        } catch(e) {}

        new Chart(salesCtx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Sales', data: data.sales,
                    backgroundColor: COLORS.primary, borderRadius: 8, barPercentage: 0.6
                }, {
                    label: 'Purchases', data: data.purchases,
                    backgroundColor: COLORS.secondary, borderRadius: 8, barPercentage: 0.6
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { usePointStyle: true, padding: 15, font: { family: 'Inter' } } } },
                scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { callback: v => '$' + (v/1000) + 'k' } }, x: { grid: { display: false } } }
            }
        });
    }

    /* --- Category Distribution Doughnut --- */
    const catCtx = document.getElementById('categoryChart');
    if (catCtx) {
        let data = SAMPLE.categories;
        try {
            const resp = await fetch('/api/dashboard/charts/category-distribution');
            if (resp.ok) { const json = await resp.json(); if (json.data) data = json.data; }
        } catch(e) {}

        new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.data,
                    backgroundColor: COLORS.palette.slice(0, data.labels.length),
                    borderWidth: 0, hoverOffset: 10
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '70%',
                plugins: { legend: { position: 'right', labels: { usePointStyle: true, padding: 12, font: { family: 'Inter', size: 12 } } } }
            }
        });
    }

    /* --- Top Products Horizontal Bar --- */
    const topCtx = document.getElementById('topProductsChart');
    if (topCtx) {
        let data = SAMPLE.topProducts;
        try {
            const resp = await fetch('/api/dashboard/charts/top-products');
            if (resp.ok) { const json = await resp.json(); if (json.data) data = json.data; }
        } catch(e) {}

        new Chart(topCtx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Units Sold', data: data.data,
                    backgroundColor: COLORS.palette, borderRadius: 6, barPercentage: 0.7
                }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, grid: { color: '#f1f5f9' } }, y: { grid: { display: false } } }
            }
        });
    }
}
