# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up and unregister students for activities (teacher authentication required)
- Display active announcements on the public page
- Manage announcements (create, edit, delete) for signed-in users

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get all activities with optional day/time filtering |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu&teacher_username=<teacher>` | Register a student for an activity |
| POST | `/activities/{activity_name}/unregister?email=student@mergington.edu&teacher_username=<teacher>` | Remove a student from an activity |
| POST | `/auth/login?username=<username>&password=<password>` | Authenticate a teacher/admin user |
| GET | `/auth/check-session?username=<username>` | Validate a stored session username |
| GET | `/announcements` | Get active announcements for public display |
| GET | `/announcements/manage?username=<teacher>` | List all announcements for management |
| POST | `/announcements?username=<teacher>` | Create a new announcement |
| PUT | `/announcements/{announcement_id}?username=<teacher>` | Update an announcement |
| DELETE | `/announcements/{announcement_id}?username=<teacher>` | Delete an announcement |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in MongoDB and initialized with sample records on first startup.
