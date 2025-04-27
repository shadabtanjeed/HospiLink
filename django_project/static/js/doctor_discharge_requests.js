document.addEventListener('DOMContentLoaded', function () {
    // Sidebar functionality
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

    // DOM elements
    const loadingIndicator = document.getElementById('loading-indicator');
    const noRequestsMessage = document.getElementById('no-requests-message');
    const requestsTableContainer = document.getElementById('requests-table-container');
    const requestsTableBody = document.getElementById('requests-table-body');
    const confirmActionBtn = document.getElementById('confirm-action-btn');

    // Get CSRF token
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

    // Fetch discharge requests
    async function fetchDischargeRequests() {
        try {
            const response = await fetch('/doctor/api/discharge_requests/');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const requests = await response.json();

            // Hide loading indicator
            loadingIndicator.classList.add('d-none');

            if (requests.length === 0) {
                // Show no requests message
                noRequestsMessage.classList.remove('d-none');
            } else {
                // Show table and populate it
                requestsTableContainer.classList.remove('d-none');
                displayRequests(requests);
            }
        } catch (error) {
            console.error('Error fetching discharge requests:', error);
            loadingIndicator.classList.add('d-none');
            requestsTableContainer.insertAdjacentHTML('beforebegin',
                `<div class="alert alert-danger">Failed to load discharge requests. Please try again later.</div>`);
        }
    }

    // Display requests in the table
    function displayRequests(requests) {
        requestsTableBody.innerHTML = '';

        requests.forEach(request => {
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${request.patient_name}</td>
                <td>${request.ward_name}</td>
                <td>${request.bed_number}</td>
                <td>${request.request_date}</td>
                <td class="action-buttons">
                    <button class="btn btn-sm btn-success approve-btn mr-1" 
                        data-discharge-id="${request.discharge_id}" 
                        data-admission-id="${request.admission_id}">
                        <i class="bx bx-check"></i> Approve
                    </button>
                    <button class="btn btn-sm btn-danger reject-btn" 
                        data-discharge-id="${request.discharge_id}">
                        <i class="bx bx-x"></i> Reject
                    </button>
                </td>
            `;

            requestsTableBody.appendChild(row);
        });

        // Add event listeners to action buttons
        attachButtonListeners();
    }

    // Attach event listeners to action buttons
    function attachButtonListeners() {
        // Approve buttons
        document.querySelectorAll('.approve-btn').forEach(button => {
            button.addEventListener('click', function () {
                const dischargeId = this.getAttribute('data-discharge-id');
                const admissionId = this.getAttribute('data-admission-id');

                // Set modal message and show it
                document.getElementById('modal-message').textContent = 'Are you sure you want to approve this discharge request?';
                $('#confirmationModal').attr('data-action', 'approve').modal('show');

                // Set up confirm button for approval action
                confirmActionBtn.setAttribute('data-action', 'approve');
                confirmActionBtn.setAttribute('data-discharge-id', dischargeId);
                confirmActionBtn.setAttribute('data-admission-id', admissionId);
            });
        });

        // Reject buttons
        document.querySelectorAll('.reject-btn').forEach(button => {
            button.addEventListener('click', function () {
                const dischargeId = this.getAttribute('data-discharge-id');

                // Set modal message and show it
                document.getElementById('modal-message').textContent = 'Are you sure you want to reject this discharge request?';
                $('#confirmationModal').attr('data-action', 'reject').modal('show');

                // Set up confirm button for reject action
                confirmActionBtn.setAttribute('data-action', 'reject');
                confirmActionBtn.setAttribute('data-discharge-id', dischargeId);
            });
        });
    }

    // Handle confirmation modal action
    confirmActionBtn.addEventListener('click', function () {
        const action = this.getAttribute('data-action');
        const dischargeId = this.getAttribute('data-discharge-id');

        if (action === 'approve') {
            const admissionId = this.getAttribute('data-admission-id');
            approveDischarge(dischargeId, admissionId);
        } else if (action === 'reject') {
            rejectDischarge(dischargeId);
        }

        // Hide the modal
        $('#confirmationModal').modal('hide');
    });

    // Approve discharge function
    async function approveDischarge(dischargeId, admissionId) {
        try {
            const response = await fetch('/doctor/api/approve_discharge/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    discharge_id: dischargeId,
                    admission_id: admissionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                // Show success message
                requestsTableContainer.insertAdjacentHTML('beforebegin',
                    `<div class="alert alert-success alert-dismissible fade show" role="alert">
                        Discharge request approved successfully.
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>`);

                // Refresh the discharge requests
                fetchDischargeRequests();
            } else {
                throw new Error(result.message || 'Failed to approve discharge');
            }
        } catch (error) {
            console.error('Error approving discharge:', error);
            requestsTableContainer.insertAdjacentHTML('beforebegin',
                `<div class="alert alert-danger alert-dismissible fade show" role="alert">
                    Failed to approve discharge. ${error.message}
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>`);
        }
    }

    // Reject discharge function
    async function rejectDischarge(dischargeId) {
        try {
            const response = await fetch('/doctor/api/reject_discharge/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    discharge_id: dischargeId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                // Show success message
                requestsTableContainer.insertAdjacentHTML('beforebegin',
                    `<div class="alert alert-success alert-dismissible fade show" role="alert">
                        Discharge request rejected successfully.
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>`);

                // Refresh the discharge requests
                fetchDischargeRequests();
            } else {
                throw new Error(result.message || 'Failed to reject discharge');
            }
        } catch (error) {
            console.error('Error rejecting discharge:', error);
            requestsTableContainer.insertAdjacentHTML('beforebegin',
                `<div class="alert alert-danger alert-dismissible fade show" role="alert">
                    Failed to reject discharge. ${error.message}
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>`);
        }
    }

    // Initialize the page
    fetchDischargeRequests();
});