## HospiLink
A comprehensive Hospital Management System built with Django, designed to streamline hospital operations by connecting patients, doctors, and receptionists in a unified platform.

## Features
### For Patients
- Appointment Management: Book, modify, and cancel appointments with doctors
- Medical History: View past appointments and prescriptions
- Blood Repository: Search blood donors by blood group
- Bed Admission: Request hospital bed admission and track status
- Discharge Requests: Submit discharge requests when ready to leave
- Notes System: Add personal notes about condition for doctors to view

### For Doctors
- Appointment Dashboard: View and manage upcoming appointments
- Prescription Tool: Create and print professional prescriptions
- Ward Management: Monitor assigned beds and manage patient care
- Discharge Approval: Review and approve/reject patient discharge requests
- Medical History: Access patient history and previous appointments

### For Receptionists
- Patient Registration: Register new patients in the system
- Appointment Management: Book and manage appointments on behalf of patients
- Blood Donor Management: Register and manage blood donors
- Patient Lookup: Quick search for patients by phone number

## Technology Stack
- **Backend:** Django/Python
- **Frontend:** HTML, CSS, JavaScript
- **Database:** PostgreSQL
- **UI Components:** Bootstrap 4, Boxicons
- **Maps Integration:** Leaflet.js (for blood donor locations)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/ahsanbulbul/HospiLink/
   cd HospiLink
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv django_venv
   source django_venv/bin/activate  # On Windows: django_venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up PostgreSQL:

    - Create a database
    - Import the schema from ```backup_file.sql```
    - Configure database settings in ```.env```

    - env file structure:
      ```bash
      POSTGRES_DB=DB name here
      POSTGRES_USER=your username here
      POSTGRES_PASSWORD=your password here
      ```
    
5. Run the application
   ```bash
   python django_project/manage.py runserver
   ```
6. Access the application at http://localhost:8000

## Project Structure
```bash
.env
.gitignore
Changelog.md
Credits.md
README.md
requirements.txt
django_project/
    doctor/             # Doctor-specific functionality
    hospilink_django/   # Project settings
    patient/            # Patient-specific functionality 
    receptionist/       # Receptionist-specific functionality
    static/             # Static assets
    user_authentication/# Login and user management
postgres/               # Database files and backups
scripts/                # Utility scripts
static/                 # Global static assets
```

