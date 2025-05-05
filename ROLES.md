# Role Management in Panacare Healthcare

This document explains how to set up and manage roles for users in the Panacare Healthcare system.

## Available Roles

Users can have one or more of the following roles:

- **admin**: Administrator with full access (only assignable through admin interface)
- **doctor**: Medical professional who can manage patients
- **patient**: Regular user who receives healthcare

## Setting Up Roles

### Option 1: Using the Management Command

To set up the default roles quickly, run the following command:

```bash
python manage.py create_roles
```

This will create all the default roles if they don't already exist.

### Option 2: Using the Admin Interface

1. Log in to the admin interface at `/admin/`
2. Go to the "Roles" section
3. Click "Add Role"
4. Fill in the name and description
5. Click "Save"

## Assigning Roles to Users

### During Registration

When users register, they can select from available roles (doctor or patient). The admin role is hidden from regular registration. If no role is selected, the system will assign the "patient" role by default.

### Through the Admin Interface

1. Log in to the admin interface at `/admin/`
2. Go to the "Users" section
3. Click on a user
4. In the "Permissions" section, select one or more roles from the "Roles" field
5. Click "Save"

## API Endpoints for Roles

- **GET /api/roles/**: List all available roles
- **POST /api/roles/**: Create a new role (authenticated admin only)
- **GET /api/roles/{id}/**: Get details of a specific role
- **PUT /api/roles/{id}/**: Update a role (authenticated admin only)
- **DELETE /api/roles/{id}/**: Delete a role (authenticated admin only)

- **GET /api/users/register/**: Get available roles for registration form

## Testing Role Assignment

1. First, create roles using the management command: `python manage.py create_roles`
2. Register a new user through the API, providing role IDs in the request
3. Verify the roles have been assigned correctly through the admin interface