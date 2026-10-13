# Instalite
Instagram-inspired social media platform built with Django and Python
# InstaLite – Social Media Platform

InstaLite is a Django-based social media web application inspired by Instagram. Users can share photos, connect with other users, interact with posts, and manage their profiles through a simple, user-friendly interface.

## Features

- User registration, login, and logout
- User profiles and profile picture uploads
- Create posts with images and captions
- Support for multiple images per post
- Like and comment on posts
- Follow and unfollow users
- Stories with profile pictures
- Save posts for later
- Notifications for user interactions
- Direct messaging between users
- Responsive interface

## Technologies Used

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Database:** MySQL / PostgreSQL / SQLite (depending on configuration)
- **Authentication:** Django Authentication
- **Version Control:** Git and GitHub

## Project Structure

- `accounts/` – User accounts and profile management
- `posts/` – Posts and social interaction features
- `insights/` – Additional application functionality
- `instalite/` – Main Django project configuration
- `templates/` – HTML templates
- `static/` – Static assets such as CSS, JavaScript, and images
- `manage.py` – Django management utility

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/shabbarcyclewala47-blip/Instalite.git
cd Instalite
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

If a `requirements.txt` file is available:

```bash
pip install -r requirements.txt
```

Otherwise, install Django and the other dependencies used by the project.

### 4. Configure the database

Configure your database settings in `settings.py`. Set up the required database and keep credentials and secret keys out of version control.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Learning Outcomes

This project provides practical experience with Django, database models, authentication, CRUD operations, file uploads, template rendering, and building interactive web application features.

## Repository

GitHub: https://github.com/shabbarcyclewala47-blip/Instalite

## Author

Shabbar Cyclewala

*Built as a full-stack web development learning project.*
