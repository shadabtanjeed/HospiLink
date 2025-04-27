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

    // Fetch beds assigned to the doctor
    async function fetchAssignedBeds() {
        try {
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
            }
        } catch (error) {
            console.error('Error fetching assigned beds:', error);
            loadingIndicator.classList.add('d-none');
            bedsTableContainer.insertAdjacentHTML('beforebegin',
                `<div class="alert alert-danger">Failed to load bed data. Please try again later.</div>`);
        }
    }

    // Display beds in the table
    function displayBeds(beds) {
        bedsTableBody.innerHTML = '';

        beds.forEach(bed => {
            const row = document.createElement('tr');

            // Determine status class
            let statusClass = '';
            if (bed.status === 'Occupied') {
                statusClass = 'text-danger';
            } else if (bed.status === 'Available') {
                statusClass = 'text-success';
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
                        <i class="bx bx-note"></i> View Notes
                    </button>
                    <button class="btn btn-sm btn-danger discharge-btn" 
                        data-admission-id="${bed.admission_id}" 
                        ${!bed.admission_id ? 'disabled' : ''}>
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

        // Reset content
        document.getElementById('patient-notes-content').innerHTML = 'Loading notes...';

        // Fetch patient notes
        fetch(`/doctor/api/patient_notes/${admissionId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.notes && data.notes.length > 0) {
                    let notesHtml = '<ul class="list-group">';
                    data.notes.forEach(note => {
                        notesHtml += `
                            <li class="list-group-item">
                                <div class="note-date text-muted">${formatDate(note.timestamp)}</div>
                                <div class="note-content">${note.text}</div>
                            </li>
                        `;
                    });
                    notesHtml += '</ul>';
                    document.getElementById('patient-notes-content').innerHTML = notesHtml;
                } else {
                    document.getElementById('patient-notes-content').innerHTML =
                        '<p class="text-center">No notes available for this patient.</p>';
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
                    // Refresh the bed data
                    fetchAssignedBeds();
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