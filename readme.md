# PyShop API

This is a test task for the PyShop company, which includes the development of an API for user management and token handling using Django and Docker.

## Description

The API provides the following functionalities:
- User registration and authentication.
- Fetching user information.
- Updating user data.
- Generating access and refresh tokens for authentication.
- Logging out the user (removing the refresh token).

## Technologies

- **Python**
- **Django**
- **Django REST Framework**
- **JWT for authentication (using PyJWT)**
- **Docker**
- **Constance for configuration management**


## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/alexunder2003/py_shop_task.git
cd py_shop_task
```

### 2. Create and activate a virtual environment (if not using Docker)

```bash
python3 -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate     # For Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup environment variables

Create a `.env` file in the root of the project and add the following variables:

```
SECRET_KEY=your-secret-key
```

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Run the development server

```bash
python manage.py runserver 0.0.0.0:8000
```

Your server should now be accessible at http://localhost:8000.

## Using Docker

### 1. Build and run the container

If you want to run the project using Docker, follow these steps:

```bash
docker-compose build
docker-compose up
```

The project will be accessible at port `8080` (or the port you've specified).

## API Endpoints

### 1. `POST /api/login/`

To obtain JWT tokens (access and refresh):

#### Request body:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Response:

```json
{
  "access": "access-token",
  "refresh": "refresh-token"
}
```

### 2. `POST /api/refresh/`

To refresh the access token using the refresh token.

#### Request body:

```json
{
  "refresh": "your-refresh-token"
}
```

#### Response:

```json
{
  "access": "new-access-token"
}
```

### 3. `POST /api/logout/`

To log the user out and delete the refresh token.

#### Request body:

```json
{
  "refresh": "your-refresh-token"
}
```

#### Response:

```json
{
  "success": "User logged out."
}
```

### 4. `GET /api/me/`

To get the current authenticated user's information.

#### Response:

```json
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com"
}
```

### 5. `PUT /api/me/`

To update the user's data.

#### Request body:

```json
{
  "username": "new-username",
  "email": "new-email@example.com"
}
```

#### Response:

```json
{
  "id": 1,
  "username": "new-username",
  "email": "new-email@example.com"
}
```

## Settings

### Constance

The project uses **django-constance** for managing token expiration settings. You can configure the constants either through the Django admin panel or directly in the database.

### Example constants:

- **ACCESS_TOKEN_LIFETIME** — The expiration time for access tokens in seconds.
- **REFRESH_TOKEN_LIFETIME** — The expiration time for refresh tokens in days.

