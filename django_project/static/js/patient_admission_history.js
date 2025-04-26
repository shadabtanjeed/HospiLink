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

    // Main containers for admission details
    const admissionContainer = document.getElementById('admission-container');
    const previousAdmissionsContainer = document.getElementById('previous-admissions-container');

    // Format date for display
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Calculate stay duration
    function calculateDuration(checkInDate, checkOutDate) {
        if (!checkInDate || !checkOutDate) return 'N/A';

        const start = new Date(checkInDate);
        const end = new Date(checkOutDate);
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        return `${diffDays} day${diffDays !== 1 ? 's' : ''}`;
    }

    // Fetch all admissions for the patient
    async function fetchAdmissions() {
        try {
            const response = await fetch('/patient/api/get_admissions/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const admissions = await response.json();

            // Separate current and previous admissions
            const currentAdmission = admissions.find(a => a.check_out_date === null);
            const previousAdmissions = admissions.filter(a => a.check_out_date !== null);

            // Display both sections
            displayCurrentAdmission(currentAdmission);
            displayPreviousAdmissions(previousAdmissions);
        } catch (error) {
            console.error('Error fetching admissions:', error);
            admissionContainer.innerHTML =
                '<div class="alert alert-danger">Failed to load admission data. Please try again later.</div>';
        }
    }

    // Display the current admission details
    function displayCurrentAdmission(data) {
        if (!data) {
            admissionContainer.innerHTML = `
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

        // Display the admission details
        admissionContainer.innerHTML = `
            <div class="admission-card">
                <div class="card-header">
                    <h3>Current Hospital Admission</h3>
                    <span class="admission-badge">Active</span>
                </div>
                <div class="card-body">
                    <div class="admission-details">
                        <div class="detail-row">
                            <span class="detail-label">Patient Name:</span>
                            <span class="detail-value">${data.patient_name || 'Not provided'}</span>
                        </div>
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
                            <span class="detail-value">${data.doctor_name || data.doctor_username || 'Not assigned'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Nurse:</span>
                            <span class="detail-value">${data.nurse_username || 'Not assigned'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Check-in Date:</span>
                            <span class="detail-value">${formatDate(data.check_in_date)}</span>
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
        attachButtonListeners();
    }

    // Display previous admissions
    function displayPreviousAdmissions(admissions) {
        if (!admissions || admissions.length === 0) {
            previousAdmissionsContainer.innerHTML = `
                <div class="no-admission-container">
                    <div class="no-admission-card">
                        <h4>No Previous Admissions</h4>
                        <p>You don't have any previous hospital admissions on record.</p>
                    </div>
                </div>
            `;
            return;
        }

        // Create header
        let html = `
            <h3 class="section-title">Previous Admissions</h3>
            <div class="previous-admissions-grid">
        `;

        // Create a card for each previous admission
        admissions.forEach(admission => {
            html += `
                <div class="previous-admission-card">
                    <!-- Section 1: Admission number and status -->
                    <div class="admission-id-section">
                        <h4>Admission #${admission.admission_id}</h4>
                        <span class="admission-badge completed">Completed</span>
                    </div>
                    
                    <!-- Section 2: Location info (bed and ward) -->
                    <div class="location-section">
                        <div class="info-row">
                            <span class="info-label">Ward:</span>
                            <span class="info-value">${admission.ward_name || 'N/A'} (${admission.ward_type || 'N/A'})</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Bed ID:</span>
                            <span class="info-value">${admission.bed_id || 'N/A'}</span>
                        </div>
                    </div>
                    
                    <!-- Section 3: People info (patient and doctor) -->
                    <div class="people-section">
                        <div class="info-row">
                            <span class="info-label">Patient:</span>
                            <span class="info-value">${admission.patient_name || 'Not provided'}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Doctor:</span>
                            <span class="info-value">${admission.doctor_name || admission.doctor_username || 'Not assigned'}</span>
                        </div>
                    </div>
                    
                    <!-- Section 4: Dates and duration -->
                    <div class="dates-section">
                        <div class="info-row">
                            <span class="info-label">Check-in:</span>
                            <span class="info-value">${formatDate(admission.check_in_date)}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Check-out:</span>
                            <span class="info-value">${formatDate(admission.check_out_date)}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Duration:</span>
                            <span class="info-value">${calculateDuration(admission.check_in_date, admission.check_out_date)}</span>
                        </div>
                    </div>
                    
                    <!-- Section 5: Buttons -->
                    <div class="actions-section">
                        <button class="btn-view-notes" data-admission-id="${admission.admission_id}">
                            <i class="bx bx-note"></i> View Doctor Notes
                        </button>
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        previousAdmissionsContainer.innerHTML = html;

        // Add event listeners to the View Notes buttons in previous admissions
        document.querySelectorAll('.previous-admission-card .btn-view-notes').forEach(button => {
            button.addEventListener('click', function () {
                const admissionId = this.getAttribute('data-admission-id');
                alert('View doctor notes feature for previous admissions will be implemented later.');
                // This will be implemented later as per requirements
            });
        });
    }

    // Attach event listeners to buttons
    function attachButtonListeners() {
        const viewNotesBtn = document.getElementById('view-notes-btn');
        const addNotesBtn = document.getElementById('add-notes-btn');
        const dischargeBtn = document.getElementById('discharge-btn');

        if (viewNotesBtn) {
            viewNotesBtn.addEventListener('click', viewDoctorNotes);
        }
        if (addNotesBtn) {
            addNotesBtn.addEventListener('click', addPatientNotes);
        }
        if (dischargeBtn) {
            dischargeBtn.addEventListener('click', requestDischarge);
        }
    }

    // Button handler functions
    function viewDoctorNotes() {
        // Open doctor notes modal
        $('#doctorNotesModal').modal('show');

        // Fetch doctor notes
        fetch('/patient/api/doctor_notes/')
            .then(response => response.json())
            .then(data => {
                document.getElementById('doctor-notes-content').innerText =
                    data.notes || 'No notes available from your doctor.';
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('doctor-notes-content').innerText =
                    'Failed to load doctor notes. Please try again later.';
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
                        fetchAdmissions();
                    } else {
                        alert(`Failed to submit discharge request: ${data.message || 'Unknown error'}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while requesting discharge. Please try again.');
                });
        }
    }

    // Handle patient notes form submission
    const patientNotesForm = document.getElementById('patient-notes-form');
    if (patientNotesForm) {
        patientNotesForm.addEventListener('submit', function (e) {
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
                        alert(`Failed to add notes: ${data.message || 'Unknown error'}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while adding notes. Please try again.');
                });
        });
    }

    // Initialize page
    fetchAdmissions();
});