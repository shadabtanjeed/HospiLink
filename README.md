## HospiLink
A comprehensive Hospital Management System built with Django, designed to streamline hospital operations by connecting patients, doctors, and receptionists in a unified platform.

You can try out the application here: https://hospilink.onrender.com

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

## Screenshots

### Main Signup

![Signup Main](https://github.com/user-attachments/assets/1a98994f-f3b9-4769-bcca-75ef46871f5f)

### Doctor Interface

#### Authentication
![Doctor Signup](https://github.com/user-attachments/assets/6632e433-62ed-4ce5-b2de-96c4f8baf5f2)

#### Dashboard
![Doctor Dashboard](https://github.com/user-attachments/assets/1fa726c8-d521-4b35-a96c-169f6a7691d2)

#### Patient Management
![Attend a Patient](https://github.com/user-attachments/assets/6f259f7a-3452-4c39-8279-f1b71a75cef4)
![View All Attended Records](https://github.com/user-attachments/assets/2b0a2798-bbd9-4635-855c-a5d6769e6e15)


#### Ward Management
![Ward Management](https://github.com/user-attachments/assets/3757786f-8a1e-41ea-b180-3ac544055a22)
![View Patient Notes](https://github.com/user-attachments/assets/0242ddbc-223d-49ad-9649-a34fca32b57a)

#### Discharge Requests
![Discharge Requests](https://github.com/user-attachments/assets/080ddd57-27b1-4e78-a1b3-d6385a785ef4)

### Patient Interface

#### Home & Profile
![Home Page](https://github.com/user-attachments/assets/8c53c417-9dc3-4d9c-8f25-a7cf72a31f2a)


#### Appointments
![Search Doctor](https://github.com/user-attachments/assets/0de373c9-49d4-46c7-8bf7-691526ce4994)
![Book Appointment](https://github.com/user-attachments/assets/ce2af502-01c0-4ef6-9d23-e819303d807d)
![Modify Appointment](https://github.com/user-attachments/assets/3c651f37-21fd-4815-9555-2f821fe341fa)


#### Medical Records
![Appointment History](https://github.com/user-attachments/assets/e415fb9d-16e2-4347-b14a-89cd401241a1)
![View Past Prescription](https://github.com/user-attachments/assets/90b660f8-538c-4ce2-beb6-d2bf3cfb4dab)

#### Blood Repository
![Blood Repository](https://github.com/user-attachments/assets/c70b1b71-7da0-4a69-87f9-45d24dee7609)


#### Hospital Admission
![Get Admission](https://github.com/user-attachments/assets/8bb2264e-0d4a-4c39-b14c-ca30c8223dd6)
![Admission Status](https://github.com/user-attachments/assets/fe87f8fd-2d7a-4a2a-aeb0-408e7771fcc9)
![View Doctor Notes](https://github.com/user-attachments/assets/2f8cce8c-bc46-4738-b851-6ad121d0fcd0)

### Receptionist Interface

#### Patient Management
![Find Patient by Phone Number](https://github.com/user-attachments/assets/11445710-576c-4df2-abb4-e04fbe8d5f28)

#### Appointment Management
![Manage User Appointments 2](https://github.com/user-attachments/assets/321db618-c3ec-4ca2-b17c-e9b84d4d0056)
![Manage User Appointments 1](https://github.com/user-attachments/assets/a7f9165b-c246-4720-b76e-8d0ec2d7ac70)


#### Blood Donation
![Add Blood Donor](https://github.com/user-attachments/assets/c4ab6ead-e551-4a11-a816-89038fb9beb9)

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

