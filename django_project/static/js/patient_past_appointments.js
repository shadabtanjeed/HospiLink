const navBar = document.querySelector("nav"),
    menuBtns = document.querySelectorAll(".menu-icon"),
    overlay = document.querySelector(".overlay");

menuBtns.forEach((menuBtn) => {
    menuBtn.addEventListener("click", () => {
        navBar.classList.toggle("open");
    });
});

overlay.addEventListener("click", () => {
    navBar.classList.remove("open");
});

document.addEventListener('DOMContentLoaded', function () {
    const tableBody = document.getElementById('table-body');

    async function fetchAppointments() {
        // Changed to use the patient API endpoint
        const response = await fetch('/patient/api/past_appointments/');
        const data = await response.json();

        const pastAppointments = data.filter(item => {
            const appointmentDate = new Date(item.appointment_date);
            const appointmentTime = item.appointment_time.split(':');
            appointmentDate.setHours(appointmentTime[0], appointmentTime[1], appointmentTime[2]);
            return appointmentDate;
        });
        renderTable(pastAppointments);
    }

    function renderTable(data) {
        tableBody.innerHTML = '';
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.appointment_id}</td>
                <td>${item.appointment_date}</td>
                <td>${item.appointment_time}</td>
                <td>Dr. ${item.doctor_name}</td>
                <td>
                    <button class="btn view-btn" onclick="viewPrescription(${item.appointment_id})">View</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    fetchAppointments();
});

async function viewPrescription(appointmentId) {
    try {
        // Update this to use a patient-specific endpoint
        const response = await fetch(`/patient/api/prescription/${appointmentId}/`);
        if (!response.ok) {
            throw new Error('No prescription found');
        }
        const prescription = await response.json();

        if (prescription) {
            showPrescriptionTemplate(prescription);
        } else {
            alert('No prescription found for this appointment.');
        }
    } catch (error) {
        console.error('Error fetching prescription:', error);
        alert('No prescription found for this appointment.');
    }
}

function showPrescriptionTemplate(prescription) {
    // Hide the table container
    document.querySelector('.container.mt-5').style.display = 'none';

    // Update prescription template content
    document.getElementById('doctorName').textContent = prescription.prescribed_by;
    document.getElementById('doctorDegrees').textContent = prescription.doctor_degrees;
    document.getElementById('patientName').textContent = prescription.prescribed_to;
    document.getElementById('prescriptionDate').textContent = prescription.created_at;
    document.getElementById('diagnosisText').textContent = prescription.diagnosis;
    document.getElementById('medicationText').textContent = prescription.medication;
    document.getElementById('additionalNotesText').textContent = prescription.additional_notes || 'None';
    document.getElementById('doctorSignature').textContent = `Dr. ${prescription.prescribed_by}`;

    // Show the prescription template
    document.getElementById('prescriptionTemplate').style.display = 'block';
}

function goBackToTable() {
    document.getElementById('prescriptionTemplate').style.display = 'none';
    document.querySelector('.container.mt-5').style.display = 'block';
}

function printPrescription() {
    window.print();
}