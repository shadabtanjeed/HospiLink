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

    // Fetch current admission details
    async function fetchCurrentAdmission() {
        try {
            const response = await fetch('/patient/api/current_admission/');
            const data = await response.json();

            displayCurrentAdmission(data);
        } catch (error) {
            console.error('Error fetching current admission:', error);
            document.getElementById('admission-container').innerHTML =
                '<div class="alert alert-danger">Failed to load admission data. Please try again later.</div>';
        }
    }

    // Display the current admission details
    function displayCurrentAdmission(data) {
        const container = document.getElementById('admission-container');

        if (!data.has_active_admission) {
            container.innerHTML = `
                <div class="no-admission-container">
                    <div class="no-admission-card">
                        <h3>No Active Admissions</h3>
                        <p>You don't have any active hospital admissions at this time.</p>
                        <a href="/patient/bed_admission/" class="btn btn-primary">Request Admission</a>
                    </div>
                </div>
            `;
            return;
        }

        // Format date for display
        const checkInDate = new Date(data.check_in_date);
        const formattedDate = checkInDate.toLocaleString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Get doctor and nurse names (would be better to have this in the API response)
        fetchStaffNames(data.doctor_username, data.nurse_username)
            .then(names => {
                container.innerHTML = `
                    <div class="admission-card">
                        <div class="card-header">
                            <h3>Current Hospital Admission</h3>
                            <span class="admission-badge">Active</span>
                        </div>
                        <div class="card-body">
                            <div class="admission-details">
                                <div class="detail-row">
                                    <span class="detail-label">Admission ID:</span>
                                    <span class="detail-value">${data.admission_id}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Ward:</span>
                                    <span class="detail-value">${data.ward_name} (${data.ward_type})</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Ward No:</span>
                                    <span class="detail-value">${data.ward_no}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Bed ID:</span>
                                    <span class="detail-value">${data.bed_id}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Doctor:</span>
                                    <span class="detail-value">${names.doctor}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Nurse:</span>
                                    <span class="detail-value">${names.nurse}</span>
                                </div>
                                <div class="detail-row">
                                    <span class="detail-label">Check-in Date:</span>
                                    <span class="detail-value">${formattedDate}</span>
                                </div>
                            </div>
                        </div>
                        <div class="card-footer">
                            <button class="btn btn-view-notes" id="view-notes-btn">
                                <i class="bx bx-note"></i> View Doctor Notes
                            </button>
                            <button class="btn btn-add-notes" id="add-notes-btn">
                                <i class="bx bx-plus"></i> Add Notes
                            </button>
                            <button class="btn btn-discharge" id="discharge-btn">
                                <i class="bx bx-exit"></i> Request Discharge
                            </button>
                        </div>
                    </div>
                `;

                // Add event listeners for the buttons
                document.getElementById('view-notes-btn').addEventListener('click', viewDoctorNotes);
                document.getElementById('add-notes-btn').addEventListener('click', addPatientNotes);
                document.getElementById('discharge-btn').addEventListener('click', requestDischarge);
            });
    }

    // Helper function to fetch staff names
    async function fetchStaffNames(doctorUsername, nurseUsername) {
        // This would ideally be an API call to get names, but for now we'll use placeholder
        return {
            doctor: doctorUsername ? `Dr. ${doctorUsername}` : 'Not assigned',
            nurse: nurseUsername || 'Not assigned'
        };
    }

    // Button handler functions
    function viewDoctorNotes() {
        // Open doctor notes modal
        $('#doctorNotesModal').modal('show');

        // Fetch doctor notes - would need an API endpoint
        fetch('/patient/api/doctor_notes/')
            .then(response => response.json())
            .then(data => {
                document.getElementById('doctor-notes-content').innerText =
                    data.notes || 'No notes available';
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('doctor-notes-content').innerText =
                    'Failed to load doctor notes.';
            });
    }

    function addPatientNotes() {
        // Open patient notes modal
        $('#patientNotesModal').modal('show');
    }

    function requestDischarge() {
        if (confirm('Are you sure you want to request a discharge?')) {
            // Send discharge request to backend
            fetch('/patient/api/request_discharge/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({})
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Discharge request submitted successfully!');
                        // Refresh the admission data
                        fetchCurrentAdmission();
                    } else {
                        alert(`Failed to submit discharge request: ${data.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while requesting discharge. Please try again.');
                });
        }
    }

    // Submit patient notes
    document.getElementById('patient-notes-form').addEventListener('submit', function (e) {
        e.preventDefault();

        const notes = document.getElementById('patient-notes-input').value;

        fetch('/patient/api/add_patient_notes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ notes: notes })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Notes added successfully!');
                    $('#patientNotesModal').modal('hide');
                    document.getElementById('patient-notes-input').value = '';
                } else {
                    alert(`Failed to add notes: ${data.message}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while adding notes. Please try again.');
            });
    });

    // Call the function when the page loads
    fetchCurrentAdmission();
});