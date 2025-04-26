document.addEventListener('DOMContentLoaded', function () {
    // Navigation sidebar toggle
    const navBar = document.querySelector("nav");
    const menuBtns = document.querySelectorAll(".menu-icon");
    const overlay = document.querySelector(".overlay");

    menuBtns.forEach((menuBtn) => {
        menuBtn.addEventListener("click", () => {
            navBar.classList.toggle("open");
        });
    });

    overlay.addEventListener("click", () => {
        navBar.classList.remove("open");
    });

    // Form submission handling
    const bedSearchForm = document.getElementById('bed-search-form');
    const resultsContainer = document.getElementById('results-container');
    const noResults = document.getElementById('no-results');
    const hasResults = document.getElementById('has-results');
    const bedCount = document.getElementById('bed-count');
    const bedsTableBody = document.getElementById('beds-table-body');

    // Modal elements
    const reserveModal = document.getElementById('reserveModal');
    const reserveForm = document.getElementById('reserveForm');
    const patientNameInput = document.getElementById('patientNameInput');
    let selectedBedId = null;

    // Get CSRF token for POST requests
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    bedSearchForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const wardType = document.getElementById('ward-type').value;
        const bedType = document.getElementById('bed-type').value;

        if (!wardType) {
            alert('Please select a ward type');
            return;
        }

        // Show loading state
        resultsContainer.classList.remove('d-none');
        noResults.classList.add('d-none');
        hasResults.classList.add('d-none');
        bedsTableBody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';

        // Make API request to the correct endpoint
        fetch(`/patient/api/search_beds/?ward_type=${encodeURIComponent(wardType)}&bed_type=${encodeURIComponent(bedType)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(beds => {
                // Handle response - beds should be an array directly now
                if (!beds || beds.length === 0) {
                    noResults.classList.remove('d-none');
                    hasResults.classList.add('d-none');
                } else {
                    noResults.classList.add('d-none');
                    hasResults.classList.remove('d-none');
                    bedCount.textContent = beds.length;

                    // Clear previous results
                    bedsTableBody.innerHTML = '';

                    // Populate table with the beds array
                    beds.forEach(bed => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${bed.bed_no}</td>
                            <td>${bed.ward_no}</td>
                            <td>${bed.ward_name}</td>
                            <td>${bed.bed_type}</td>
                            <td>Tk. ${bed.cost_per_day} / day</td>
                            <td><button class="btn btn-sm btn-reserve" data-bed-id="${bed.bed_id}" 
                                data-ward-no="${bed.ward_no}" data-bed-no="${bed.bed_no}">Reserve</button></td>
                        `;
                        bedsTableBody.appendChild(row);
                    });

                    // Add event listeners to reserve buttons
                    document.querySelectorAll('.btn-reserve').forEach(button => {
                        button.addEventListener('click', function () {
                            selectedBedId = this.getAttribute('data-bed-id');
                            // Show the modal (Bootstrap 4)
                            $('#reserveModal').modal('show');
                        });
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                bedsTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error: ${error.message}</td></tr>`;
            });
    });

    // Handle the modal form submission
    if (reserveForm) {
        reserveForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const patientName = patientNameInput.value.trim();
            if (!patientName) {
                alert('Please enter the patient name.');
                return;
            }
            // Send reservation request with patient name
            fetch('/patient/reserve_bed/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    bed_id: selectedBedId,
                    patient_name: patientName
                })
            })
                .then(response => response.json())
                .then(data => {
                    $('#reserveModal').modal('hide');
                    if (data.success) {
                        alert('Bed reserved successfully!');
                        // Refresh the search results
                        bedSearchForm.dispatchEvent(new Event('submit'));
                    } else {
                        alert(data.message || 'Failed to reserve bed. Please try again.');
                    }
                })
                .catch(error => {
                    $('#reserveModal').modal('hide');
                    console.error('Error:', error);
                    alert('An error occurred while reserving the bed. Please try again.');
                });
        });
    }
});