console.log("Charts JS loaded");

fetch('/chart-data')
.then(response => response.json())
.then(data => {
    // ---- Round-wise Chart ----
    new Chart(document.getElementById('roundChart').getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.round_counts.ROUND,
            datasets: [{
                label: 'Number of Students',
                data: data.round_counts.STUDENTID,
                backgroundColor: 'rgba(75, 192, 192, 0.6)'
            }]
        },
        options: { responsive: true }
    });

    // ---- Year-wise Chart ----
    new Chart(document.getElementById('yearChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: data.year_counts.YEAR,
            datasets: [{
                label: 'Number of Students',
                data: data.year_counts.STUDENTID,
                borderColor: 'rgba(255, 99, 132, 0.7)',
                fill: false
            }]
        },
        options: { responsive: true }
    });

    // ---- Top 10 Colleges ----
    new Chart(document.getElementById('collegeChart').getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.top_colleges.COLLENAME,
            datasets: [{
                label: 'Allotted Students',
                data: data.top_colleges.STUDENTID,
                backgroundColor: 'rgba(153, 102, 255, 0.6)'
            }]
        },
        options: { indexAxis: 'y', responsive: true }
    });

    // ---- Community Distribution ----
    new Chart(document.getElementById('communityChart').getContext('2d'), {
        type: 'pie',
        data: {
            labels: data.community_dist.COMMUNITY,
            datasets: [{
                label: 'Students',
                data: data.community_dist.STUDENTID,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                ]
            }]
        },
        options: { responsive: true }
    });

    // ---- College Type Distribution ----
    new Chart(document.getElementById('collegeTypeChart').getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: data.college_type_dist.COLLEGETYPE,
            datasets: [{
                label: 'Students',
                data: data.college_type_dist.STUDENTID,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'
                ]
            }]
        },
        options: { responsive: true }
    });
});
