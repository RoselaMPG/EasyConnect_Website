let globalWeatherData = null;

// Function to fetch sensor data from the API
async function fetchSensorData(sensorType) {
    try {
        const response = await fetch(`/api/${sensorType}`);
        if (!response.ok) {
            throw new Error('Failed to fetch sensor data');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching sensor data:', error);
        return [];
    }
}

// Add function to check for new data periodically (every 10 seconds)
function setupDataRefresh() {
    setInterval(loadSensorData, 1000);
}


// Load sensor data when the page loads
document.addEventListener('DOMContentLoaded', () => {
    loadSensorData();
    setupDataRefresh();

    // Modify tab switching to handle data loading
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab
            tab.classList.add('active');
            document.getElementById(`${tab.dataset.tab}-tab`).classList.add('active');

        });
    });


});