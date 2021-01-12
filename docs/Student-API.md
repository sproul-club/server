# Student API

<!-- MarkdownTOC autolink="true" -->

- [Managing Account](#managing-account)
    - [Login user](#login-user)
    - [Finish registeration](#finish-registeration)
    - [Refresh access token](#refresh-access-token)
    - [Revoke access token](#revoke-access-token)
    - [Revoke refresh token](#revoke-refresh-token)
- [Managing Data](#managing-data)

<!-- /MarkdownTOC -->

## Managing Account

### Login user
* Description: Logs in a student user via Google OAuth w/ CalNet integration
* Path: `POST /api/student/login`
* Result: Redirects user to CalNet sign in page if not logged in recently, if at all. If the user never had an account before,
a partial account is made, in which the registeration is expected to finish when `/finish-register` is called. If there is an account, it should lead you to the Student Dashboard.
* Sample body output:
```json
{
    "profile": {
        "name": "Example User",
        "email": "exampleuser@berkeley.edu"
    },
    "token": {
        "access": "<access_token>",
        "access_expires_in": 900,
        "refresh": "<refresh_token>",
        "refresh_expires_in": 86400
    }
}
```

### Finish registeration
* Description:
* Path: `POST /api/student/finish-register`
* Sample body input:
```json
{
    "email": "exampleuser@berkeley.edu",
    "majors": [2, 7, 3],
    "minors": [3, 1, 4],
    "interests": [6, 2, 8]
}
```
* Sample body output:
```json
{
    "status": "success"
}
```

### Refresh access token
* Description: Fetches a new access token given a valid refresh token
* Path: `POST /api/student/refresh`
* Headers:
    - `Authorization: Bearer <refresh_token>`
* Sample body output:
```json
{
    "access": "<access_token>",
    "access_expires_in": 900
}
```
* Note: `expires_in` values are just example values

### Revoke access token
* Description: Revokes an issued access token, preventing further use of it
* Path: `DELETE /api/student/revoke-access`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
{
    "status": "success",
    "message": "Access token revoked!"
}
```

### Revoke refresh token
* Description: Revokes an issued refresh token, preventing further use of it
* Path: `DELETE /api/student/revoke-refresh`
* Headers:
    - `Authorization: Bearer <refresh_token>`
* Sample body output:
```json
{
    "status": "success",
    "message": "Refresh token revoked!"
}
```

## Managing Data
