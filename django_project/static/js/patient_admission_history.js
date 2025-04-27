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
            <div class="admission-card" data-admission-id="${data.admission_id}">
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

        // Add event listeners to all View Doctor Notes buttons in previous admissions
        document.querySelectorAll('.previous-admission-card .btn-view-notes').forEach(button => {
            button.addEventListener('click', function () {
                const admissionId = this.getAttribute('data-admission-id');
                viewPreviousAdmissionNotes(admissionId);
            });
        });
    }

    // Helper function to display doctor notes for any admission
    function displayDoctorNotes(admissionId) {
        // Open doctor notes modal
        $('#doctorNotesModal').modal('show');

        // Reset content and show loading state
        document.getElementById('doctor-notes-content').innerHTML = `
            <div class="text-center my-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">Loading notes...</span>
                </div>
            </div>
        `;

        // Fetch doctor notes using the API endpoint
        fetch(`/patient/api/doctor_notes/${admissionId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.notes && data.notes.length > 0) {
                    let notesHtml = '<div class="notes-container">';

                    notesHtml += `
                        <div class="note-section doctor-notes">
                            <h5 class="section-title"><i class="bx bx-user-voice mr-2"></i>Doctor Notes</h5>
                            <div class="note-items">
                    `;

                    data.notes.forEach(note => {
                        notesHtml += `
                            <div class="note-item">
                                <div class="note-time">${formatDate(note.timestamp)}</div>
                                <div class="note-text">${note.text}</div>
                            </div>
                        `;
                    });

                    notesHtml += '</div></div></div>';
                    document.getElementById('doctor-notes-content').innerHTML = notesHtml;

                    // Add custom CSS for the notes
                    const style = document.createElement('style');
                    style.innerHTML = `
                        .notes-container {
                            max-height: 400px;
                            overflow-y: auto;
                        }
                        .section-title {
                            color: #3c4858;
                            font-weight: 600;
                            margin-bottom: 10px;
                            display: flex;
                            align-items: center;
                        }
                        .note-items {
                            padding-left: 10px;
                        }
                        .note-item {
                            background: #f8f9fa;
                            border-left: 3px solid #007bff;
                            padding: 12px 15px;
                            margin-bottom: 10px;
                            border-radius: 4px;
                        }
                        .note-time {
                            font-size: 0.8rem;
                            color: #6c757d;
                            margin-bottom: 5px;
                        }
                        .note-text {
                            white-space: pre-line;
                        }
                    `;
                    document.head.appendChild(style);
                } else {
                    document.getElementById('doctor-notes-content').innerHTML =
                        '<div class="alert alert-info">No notes available from your doctor for this admission.</div>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('doctor-notes-content').innerHTML =
                    '<div class="alert alert-danger">Failed to load notes. Please try again.</div>';
            });
    }

    // Function to view notes for previous admissions
    function viewPreviousAdmissionNotes(admissionId) {
        displayDoctorNotes(admissionId);
    }

    // Attach event listeners to buttons
    function attachButtonListeners() {
        const viewNotesBtn = document.getElementById('view-notes-btn');
        const addNotesBtn = document.getElementById('add-notes-btn');
        const dischargeBtn = document.getElementById('discharge-btn');

        if (viewNotesBtn) {
            viewNotesBtn.addEventListener('click', function () {
                const admissionId = document.querySelector('.admission-card').getAttribute('data-admission-id');
                if (!admissionId) {
                    alert('Could not find admission ID. Please try again.');
                    return;
                }
                displayDoctorNotes(admissionId);
            });
        }
        if (addNotesBtn) {
            addNotesBtn.addEventListener('click', addPatientNotes);
        }
        if (dischargeBtn) {
            dischargeBtn.addEventListener('click', requestDischarge);
        }
    }

    // Update the viewDoctorNotes function to use the shared display function
    function viewDoctorNotes() {
        const admissionId = document.querySelector('.admission-card').getAttribute('data-admission-id');
        if (!admissionId) {
            alert('Could not find admission ID. Please try again.');
            return;
        }
        displayDoctorNotes(admissionId);
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
                body: JSON.stringify({ note: notes })
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