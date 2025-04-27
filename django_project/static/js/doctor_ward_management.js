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

    // DOM elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const noBedsMessage = document.getElementById('no-beds-message');
    const bedsTableContainer = document.getElementById('beds-table-container');
    const bedsTableBody = document.getElementById('beds-table-body');

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

    async function fetchAssignedBeds() {
        try {
            // Before fetching, run the function to update maintenance beds
            await fetch('/doctor/api/update_maintenance/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                }
            });

            const response = await fetch('/doctor/api/assigned_beds/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const beds = await response.json();

            // Hide loading indicator
            loadingIndicator.classList.add('d-none');

            if (beds.length === 0) {
                // Show no beds message
                noBedsMessage.classList.remove('d-none');
            } else {
                // Show table and populate it
                bedsTableContainer.classList.remove('d-none');
                displayBeds(beds);

                // Check if any beds are in maintenance status
                const maintenanceBeds = beds.filter(bed => bed.status === 'Maintenance');
                if (maintenanceBeds.length > 0) {
                    // If there are beds in maintenance, poll again in 5 seconds
                    setTimeout(fetchAssignedBeds, 5000);
                }
            }
        } catch (error) {
            console.error('Error fetching assigned beds:', error);
            loadingIndicator.classList.add('d-none');
            bedsTableContainer.insertAdjacentHTML('beforebegin',
                `<div class="alert alert-danger">Failed to load bed data. Please try again later.</div>`);
        }
    }

    // Update the displayBeds function to handle maintenance status
    function displayBeds(beds) {
        bedsTableBody.innerHTML = '';

        beds.forEach(bed => {
            const row = document.createElement('tr');

            // Determine status class
            let statusClass = '';
            if (bed.status === 'Occupied') {
                statusClass = 'text-danger';
            } else if (bed.status === 'Vacant') {
                statusClass = 'text-success';
            } else if (bed.status === 'Maintenance') {
                statusClass = 'text-warning';  // Yellow for maintenance
            }

            row.innerHTML = `
            <td>${bed.ward_name} (${bed.ward_type})</td>
            <td>${bed.bed_no}</td>
            <td class="${statusClass}">${bed.status}</td>
            <td>${bed.bed_type}</td>
            <td>${bed.patient_name || 'N/A'}</td>
            <td>${formatDate(bed.check_in_date)}</td>
            <td>${bed.nurse_name || 'Not assigned'}</td>
            <td class="action-buttons">
                <button class="btn btn-sm btn-primary add-note-btn" 
                    data-admission-id="${bed.admission_id}" 
                    ${!bed.admission_id ? 'disabled' : ''}>
                    <i class="bx bx-plus"></i> Add Note
                </button>
                
                <button class="btn btn-sm btn-info view-notes-btn" 
                    data-admission-id="${bed.admission_id}" 
                    ${!bed.admission_id ? 'disabled' : ''}>
                    <i class="bx bx-note"></i> View Patient Notes
                </button>
                <button class="btn btn-sm btn-danger discharge-btn" 
                    data-admission-id="${bed.admission_id}" 
                    ${(!bed.admission_id || bed.status === 'Maintenance') ? 'disabled' : ''}>
                    <i class="bx bx-exit"></i> Discharge
                </button>
            </td>
        `;

            bedsTableBody.appendChild(row);
        });

        // Add event listeners to buttons
        attachButtonListeners();
    }

    // Attach event listeners to action buttons
    function attachButtonListeners() {
        // Add Note buttons
        document.querySelectorAll('.add-note-btn').forEach(button => {
            button.addEventListener('click', function () {
                const admissionId = this.getAttribute('data-admission-id');
                document.getElementById('admission-id-input').value = admissionId;
                $('#addNoteModal').modal('show');
            });
        });

        // View Notes buttons
        document.querySelectorAll('.view-notes-btn').forEach(button => {
            button.addEventListener('click', function () {
                const admissionId = this.getAttribute('data-admission-id');
                viewPatientNotes(admissionId);
            });
        });

        // Discharge buttons
        document.querySelectorAll('.discharge-btn').forEach(button => {
            button.addEventListener('click', function () {
                const admissionId = this.getAttribute('data-admission-id');
                // Store admission ID for the discharge confirmation
                document.getElementById('confirm-discharge-btn').setAttribute('data-admission-id', admissionId);
                $('#dischargeModal').modal('show');
            });
        });
    }

    // Function to view patient notes
    function viewPatientNotes(admissionId) {
        $('#viewNotesModal').modal('show');

        // Reset content and show loading state
        document.getElementById('patient-notes-content').innerHTML = `
        <div class="text-center my-4">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Loading notes...</span>
            </div>
        </div>
    `;

        // Fetch patient notes using the API endpoint
        fetch(`/doctor/api/patient_notes/${admissionId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.notes && data.notes.length > 0) {
                    let notesHtml = '<div class="notes-container">';

                    // Group notes by author type (patient or doctor)
                    const doctorNotes = data.notes.filter(note => note.author_type === 'doctor');
                    const patientNotes = data.notes.filter(note => note.author_type === 'patient');

                    // Display doctor notes first
                    if (doctorNotes.length > 0) {
                        notesHtml += `
                        <div class="note-section doctor-notes mb-4">
                            <h5 class="section-title"><i class="bx bx-user-voice mr-2"></i>Doctor Notes</h5>
                            <div class="note-items">
                    `;

                        doctorNotes.forEach(note => {
                            notesHtml += `
                            <div class="note-item">
                                <div class="note-time">${formatDate(note.timestamp)}</div>
                                <div class="note-text">${note.text}</div>
                            </div>
                        `;
                        });

                        notesHtml += '</div></div>';
                    }

                    // Then display patient notes
                    if (patientNotes.length > 0) {
                        notesHtml += `
                        <div class="note-section patient-notes">
                            <h5 class="section-title"><i class="bx bx-user mr-2"></i>Patient Notes</h5>
                            <div class="note-items">
                    `;

                        patientNotes.forEach(note => {
                            notesHtml += `
                            <div class="note-item">
                                <div class="note-time">${formatDate(note.timestamp)}</div>
                                <div class="note-text">${note.text}</div>
                            </div>
                        `;
                        });

                        notesHtml += '</div></div>';
                    }

                    notesHtml += '</div>';
                    document.getElementById('patient-notes-content').innerHTML = notesHtml;

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
                        border-left: 3px solid #dd636e;
                        padding: 12px 15px;
                        margin-bottom: 10px;
                        border-radius: 4px;
                    }
                    .doctor-notes .note-item {
                        border-left-color: #007bff;
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
                    document.getElementById('patient-notes-content').innerHTML =
                        '<div class="alert alert-info">No notes available for this patient.</div>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('patient-notes-content').innerHTML =
                    '<div class="alert alert-danger">Failed to load notes. Please try again.</div>';
            });
    }

    // Handle form submission for adding a note
    const doctorNoteForm = document.getElementById('doctor-note-form');
    if (doctorNoteForm) {
        doctorNoteForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const admissionId = document.getElementById('admission-id-input').value;
            const note = document.getElementById('doctor-note-input').value;

            fetch('/doctor/api/add_doctor_note/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ admission_id: admissionId, note: note })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Note added successfully!');
                        $('#addNoteModal').modal('hide');
                        document.getElementById('doctor-note-input').value = '';
                    } else {
                        alert(`Failed to add note: ${data.message || 'Unknown error'}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while adding the note. Please try again.');
                });
        });
    }

    // Handle discharge confirmation
    document.getElementById('confirm-discharge-btn').addEventListener('click', function () {
        const admissionId = this.getAttribute('data-admission-id');

        fetch('/doctor/api/discharge_patient/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ admission_id: admissionId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Patient discharged successfully!');
                    $('#dischargeModal').modal('hide');

                    // Refresh immediately to show maintenance status
                    fetchAssignedBeds();

                    // After 15 seconds, the status should change to Vacant
                    // We'll poll again at that time to show the change
                    setTimeout(fetchAssignedBeds, 16000);
                } else {
                    alert(`Failed to discharge patient: ${data.message || 'Unknown error'}`);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while discharging the patient. Please try again.');
            });
    });

    // Initialize the page
    fetchAssignedBeds();
});