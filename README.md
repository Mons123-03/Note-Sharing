# Note Sharing

A web-based **Note Sharing Platform** developed using Flask and MySQL that allows users to register, log in, upload academic notes, view shared notes, and manage their own uploaded notes.

## Features

* User registration and login
* Secure user authentication
* Upload and share academic notes
* View available notes
* View individual note details
* Manage personal uploaded notes
* Download shared notes
* Simple and responsive web interface
* MySQL database for storing user and note information

## Technologies Used

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python, Flask
* **Database:** MySQL
* **Database Connectivity:** Flask/MySQL
* **Templates:** Jinja2
* **File Storage:** Local uploads directory

## Project Structure

```text
note_sharing_codebase/
│
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── schema.sql
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── my_notes.html
│   └── note_detail.html
│
└── uploads/
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Mons123-03/Note-Sharing.git
cd Note-Sharing
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL

Create a MySQL database and import the provided `schema.sql` file.

Update the database configuration in `config.py` according to your MySQL username, password, host, and database name.

### 5. Run the Application

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000/
```

## How It Works

1. A new user creates an account through the registration page.
2. The user logs into the platform.
3. Users can upload their academic notes.
4. Uploaded notes are stored and associated with the respective user.
5. Users can browse and view available notes.
6. Users can access their uploaded notes through **My Notes**.
7. Notes can be downloaded for study and reference.

## Database

The application uses **MySQL** to manage application data such as:

* User information
* Note details
* Uploaded file information
* Note ownership and related records

The database structure is provided in:

```text
schema.sql
```

## Future Enhancements

* Search and filter notes
* Notes categorized by subject and semester
* User profile management
* Note ratings and reviews
* Admin dashboard
* Cloud-based file storage
* Improved access control
* Pagination for large numbers of notes


