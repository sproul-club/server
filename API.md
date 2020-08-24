# API

Base URL: https://sc-backend-v0.herokuapp.com

### Note about error responses
All endpoints except for the email confirmation and confirming a password reset will return a JSON object of the following form:
```json
{
    "status": "error",
    "reason": "Sample error message",
    "data": [
        "any extra data goes here"
    ]
}
```


## User API
We use JWTs to manage authentication, mainly for allowing the user to edit their club's information.

### Does email exist? (before sign up)
* Description: Given an email for a potential sign up, check if it exists within to list of scrapped CalLink emails?
* Path: `POST /api/user/email-exists`
* Sample body input:
```json
{
    "email": "example@gmail.com",
}
```
* Sample body output:
```json
{
    "exists": true
}
```

### Register a new user
* Description: Registers a new user and club pair
* Path: `POST /api/user/register`
* Sample body input:
```json
{
    "name": "Example Club",
    "email": "example@gmail.com",
    "password": "examplepassword",
    "tags": [3, 1, 4],
    "app_required": true,
    "new_members": true,
}
```
* Sample body output:
```json
{
    "status": "success"
}
```

### Resend confirmation email
* Description: Resends a new confirmation email if the user exists
* Path: `POST /api/user/resend-confirm`
* Sample body input:
```json
{
    "email": "example@gmail.com",
}
```
* Sample body output:
```json
{
    "status": "success"
}
```

### Confirm new user
* Description: Confirms the new user and club pair (this endpoint is normally within an email)
* Path: `GET /api/user/confirm/<confirm_token>`
* Result: Redirects you to the club edit profile page (ideally)

### Login user
* Description: Logs in a user
* Path: `POST /api/user/login`
* Sample body input:
```json
{
    "email": "example@gmail.com",
    "password": "examplepassword"
}
```
* Sample body output:
```json
{
    "access": "<access_token>",
    "access_expires_in": 900,
    "refresh": "<refresh_token>",
    "refresh_expires_in": 86400
}
```
* Note: `expires_in` values are just example values

### Request password reset
* Description: Sends a password confirmation email to the user.
* Path: `POST /api/user/request-reset`
* Sample body input:
```json
{
    "email": "example@gmail.com"
}
```
* Sample body output:
```json
{
    "status": "success"
}
```

### Confirm Reset Password
* Description: Resets the user's password and revokes all access and refresh tokens.
* Path: `POST /api/user/confirm-reset`
* Sample body input:
```json
{
    "token": "<reset-password-token>",
    "password": "examplepassword",
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
* Path: `POST /api/user/refresh`
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
* Path: `DELETE /api/user/revoke-access`
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
* Path: `DELETE /api/user/revoke-refresh`
* Headers:
    - `Authorization: Bearer <refresh_token>`
* Sample body output:
```json
{
    "status": "success",
    "message": "Refresh token revoked!"
}
```


## Catalog API

### Fetch set of tags
* Description: Fetches the set of category tags
* Path: `GET /api/catalog/tags`
* Sample body output:
```json
[
    {
        "id": 42,
        "name": "Example tag"
    },
    {
        "id": 84,
        "name": "Another Example Tag"
    }
]
```

### Fetch organizations (unfiltered)
* Description: Fetches the list of organizations without filters, sorted alphabetically.
* Path: `POST /api/catalog/organizations` (TBD)
* Sample body input:
```json
{
    "limit": 50,
    "skip": 0
}
```
* Sample body output:
```json
[
    {
        "id": "example-club",
        "name": "Example Club",
        "logo": "<logo-pic-url>",
        "banner": "<banner-pic-url>",
        "tags": [1, 3, 4],
        "app_required": true,
        "new_members": false,
    }
]
```

### Fetch organizations (filtered)
* Description: Fetches the list of organizations with filters, sorted by match relevency
* Path: `POST /api/catalog/organizations` (TBD)
* Sample body input:
```json
{
    "search": "example club",
    "tags": [],
    "app_required": true,
    "new_members": false,
    "limit": 50,
    "skip": 0
}
```
* Sample body output:
```json
[
    {
        "id": "example-club",
        "name": "Example Club",
        "tags": [1, 3, 4],
        "logo": "<logo-pic-url>",
        "banner": "<banner-pic-url>",
        "app_required": true,
        "new_members": false,
    }
]
```

### Fetch single organization
* Description: Fetches all the information of a single organization by ID
* Path: `GET /api/catalog/organizations/<org-id>`
* Sample body output:
```json
{
    "id": "example-club",
    "name": "Example Club",
    "owner": "example@gmail.com",
    "tags": [1, 3, 4],
    "logo_url": "https://sproul-club-images-prod.s3-us-west-1.amazonaws.com/logo/example-club-logo.png",
    "banner_url": "https://sproul-club-images-prod.s3-us-west-1.amazonaws.com/banner/example-club-banner.png",
    "app_required": true,
    "new_members": false,
    "about_us": "This is something about the club.",
    "get_involved": "This is something about getting involved.",
    "resources": [
        {
            "name": "Example resource",
            "link": "https://www.resource.com"
        }
    ],
    "events": [
        {
            "name": "Example event",
            "link": "https://www.event.com",
            "start_datetime": "<start-datetime>",
            "end_datetime": "<end-datetime>",
            "description": "This is a description about example event.",
        }
    ],
    "social_media_links": {
        "contact_email": "example-contact-email@gmail.com",
        "website": "http://example.com/",
        "facebook": "https://www.facebook.com/pages/example-club",
        "instagram": "https://www.instagram.com/example-club",
        "linkedin": "https://www.linkedin.com/in/example-club",
        "twitter": "https://twitter.com/example-club",
        "youtube": "https://www.youtube.com/channel/example-club",
        "github": "https://github.com/example-club",
        "behance": "https://www.behance.net/example-club",
        "medium": "https://medium.com/@example-club",
        "gcalendar": "<google-calendar-link>"
    }
}
```


## Admin API

### Fetch profile info
* Description: Fetches the complete club profile information
* Path: `GET /api/admin/profile`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
{
    "id": "example-club",
    "name": "Example Club",
    "owner": "example@gmail.com",
    "tags": [1, 3, 4],
    "logo_url": "https://sproul-club-images-prod.s3-us-west-1.amazonaws.com/logo/example-club-logo.png",
    "banner_url": "https://sproul-club-images-prod.s3-us-west-1.amazonaws.com/banner/example-club-banner.png",
    "app_required": true,
    "new_members": false,
    "about_us": "This is something about the club.",
    "get_involved": "This is something about getting involved.",
    "resources": [
        {
            "name": "Example resource",
            "link": "https://www.resource.com"
        }
    ],
    "events": [
        {
            "name": "Example event",
            "link": "https://www.event.com",
            "start_datetime": "<start-datetime>",
            "end_datetime": "<end-datetime>",
            "description": "This is a description about example event.",
        }
    ],
    "social_media_links": {
        "contact_email": "example-contact-email@gmail.com",
        "website": "http://example.com/",
        "facebook": "https://www.facebook.com/pages/example-club",
        "instagram": "https://www.instagram.com/example-club",
        "linkedin": "https://www.linkedin.com/in/example-club",
        "twitter": "https://twitter.com/example-club",
        "youtube": "https://www.youtube.com/channel/example-club",
        "github": "https://github.com/example-club",
        "behance": "https://www.behance.net/example-club",
        "medium": "https://medium.com/@example-club",
        "gcalendar": "<google-calendar-link>"
    }
}
```

### Edit profile info
* Description: Edits the club profile information
* Path: `POST /api/admin/profile`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "name": "Example Club",
    "tags": [1, 3, 4],
    "app_required": true,
    "new_members": false,
    "about_us": "This is something about the club.",
    "get_involved": "This is something about getting involved.",
    "social_media_links": {
        "contact_email": "example-contact-email@gmail.com",
        "website": "http://example.com/",
        "facebook": "https://www.facebook.com/pages/example-club",
        "instagram": "https://www.instagram.com/example-club",
        "linkedin": "https://www.linkedin.com/in/example-club",
        "twitter": "https://twitter.com/example-club",
        "youtube": "https://www.youtube.com/channel/example-club",
        "github": "https://github.com/example-club",
        "behance": "https://www.behance.net/example-club",
        "medium": "https://medium.com/@example-club",
        "gcalendar": "<google-calendar-link>"
    }
}
```
* Sample body output:
```json
{
    "status": "success"
}
```

### Upload logo/banner images
* Description: Uploads the logo and banner images. Logos must respect a 1:1 aspect ratio and 16:9 for banners. A 16 MB limit is imposed as well
* Path: `POST /api/admin/upload-images`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
    * multipart/form-data
        * `logo` - logo image
        * `banner` - banner image
* Sample body output
```json
{
    "banner_url": "https://sproul-club-images-prod.s3-us-west-1.amazonaws.com/banner/example-club-banner.png",
    "logo_url": "https://sproul-club-images-prod.s3-us-west-1.amazonaws.com/logo/example-club-logo.png",
    "status": "success"
}
```

### Get resources
* Description: Gets all resources from a club
* Path: `GET /api/admin/resources`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
[
    {
        "id": "example-resource-1",
        "name": "Example resource 1",
        "link": "http://example.com/"
    }
]
```

### Add resource
* Description: Adds a resource to the club
* Path: `POST /api/admin/resources`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "name": "Example Resource 2",
    "link": "http://example.com/"
}
```
* Sample body output:
```json
[
    {
        "id": "example-resource-1",
        "name": "Example resource 1",
        "link": "http://example.com/"
    },
    {
        "id": "example-resource-2",
        "name": "Example resource 2",
        "link": "http://example.com/"
    }
]
```

### Update resource
* Description: Updates a resource from the club
* Path: `PUT /api/admin/resources/<resource-id>`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "name": "Example Resource 10",
    "link": "http://example.com/"
}
```
* Sample body output:
```json
[
    {
        "id": "example-resource-1",
        "name": "Example resource 10",
        "link": "http://example.com/"
    },
    {
        "id": "example-resource-2",
        "name": "Example resource 2",
        "link": "http://example.com/"
    }
]
```

### Delete resource
* Description: Deletes a resource from the club
* Path: `DELETE /api/admin/resources/<resource-id>`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
[
    {
        "id": "example-resource-10",
        "name": "Example resource 10",
        "link": "http://example.com/"
    }
]
```

### Get events
* Description: Gets all events from a club
* Path: `GET /api/admin/events`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
[
    {
        "id": "example-event-1",
        "name": "Example event 1",
        "link": "http://example.com/",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the event."
    }
]
```

### Add event
* Description: Adds a event to the club
* Path: `POST /api/admin/events`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "name": "Example event 2",
    "link": "http://example.com/",
    "event_start": "2020-04-01T07:00:00.000Z",
    "event_end": "2020-08-01T07:00:00.000Z",
    "description": "This is something about the event."
}
```
* Sample body output:
```json
[
    {
        "id": "example-event-1",
        "name": "Example event 1",
        "link": "http://example.com/",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the event."
    },
    {
        "id": "example-event-2",
        "name": "Example event 2",
        "link": "http://example.com/",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the event."
    }
]
```

### Update event
* Description: Updates a event from the club
* Path: `PUT /api/admin/events/<event-id>`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "name": "Example event 10",
    "link": "http://example.com/",
    "event_start": "2020-04-01T07:00:00.000Z",
    "event_end": "2020-08-01T07:00:00.000Z",
    "description": "This is something about the new event."
}
```
* Sample body output:
```json
[
    {
        "id": "example-event-1",
        "name": "Example event 10",
        "link": "http://example.com/",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the new event."
    },
    {
        "id": "example-event-2",
        "name": "Example event 2",
        "link": "http://example.com/",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the event."
    }
]
```

### Delete event
* Description: Deletes a event from the club
* Path: `DELETE /api/admin/events/<event-id>`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
[
    {
        "id": "example-event-10",
        "name": "Example event 10",
        "link": "http://example.com/",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the new event."
    }
]
```

### Change password
* Description: Changes the current user's password without revoking all the access and refresh tokens
* Path: `POST /api/admin/change-password`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "old_password": "exampleoldpassword",
    "new_password": "examplenewpassword",
}
```
* Sample body output:
```json
{
    "status": "success"
}
```
