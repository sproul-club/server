# Admin API

<!-- MarkdownTOC autolink="true" -->

- [Postman Collection](#postman-collection)
- [Fetch profile info](#fetch-profile-info)
- [Edit profile info](#edit-profile-info)
- [Upload logo](#upload-logo)
- [Upload banner](#upload-banner)
- [Resources](#resources)
    - [Get resources](#get-resources)
    - [Add resource](#add-resource)
    - [Update resource](#update-resource)
    - [Delete resource](#delete-resource)
- [Events](#events)
    - [Get events](#get-events)
    - [Add event](#add-event)
    - [Update event](#update-event)
    - [Delete event](#delete-event)
- [Recruiting Events](#recruiting-events)
    - [Get recruiting events](#get-recruiting-events)
    - [Add recruiting event](#add-recruiting-event)
    - [Update recruiting nevent](#update-recruiting-nevent)
    - [Delete recruiting event](#delete-recruiting-event)
- [Change password](#change-password)

<!-- /MarkdownTOC -->

## Postman Collection
[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/d94f6e43c7f713013796)

## Fetch profile info
* Description: Fetches the complete club profile information
* Path: `GET /api/admin/profile`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
{
    "name": "Example Club",
    "link_name": "example-club",
    "owner": "exampleuser@berkeley.edu",
    "about_us": "This is something about the club.",
    "get_involved": "This is something about getting involved.",
    "banner_url": "<banner-pic-url>",
    "logo_url": "<logo-pic-url>",
    "app_required": true,
    "new_members": false,
    "num_users": 0,
    "apply_link": "https://www.apply-here-now.com",
    "apply_deadline_start": "2020-04-20T12:00:00",
    "apply_deadline_end": "2020-05-20T12:00:00",
    "recruiting_start": "2020-03-20T12:00:00",
    "recruiting_end": "2020-06-20T12:00:00",
    "tags": [1, 3, 4],
    "resources": [
        {
            "id": "example-resource",
            "name": "Example resource",
            "link": "https://www.resource.com"
        }
    ],
    "events": [
        {
            "name": "Example event",
            "link": "https://www.event.com",
            "event_start": "2020-04-20T12:00:00",
            "event_end": "2020-06-20T12:00:00",
            "description": "This is a description about example event.",
        }
    ],
    "recruiting_events": [
        {
            "name": "Example event",
            "link": "https://www.event.com",
            "virtual_link": "https://www.zoom.com/example-event",
            "event_start": "2020-04-20T12:00:00",
            "event_end": "2020-06-20T12:00:00",
            "description": "This is a description about example event.",
        }
    ],
    "social_media_links": {
        "contact_email": "example-email@gmail.com",
        "website": "http://example.com/",
        "facebook": "https://www.facebook.com/pages/example-club",
        "instagram": "https://www.instagram.com/example-club",
        "linkedin": "https://www.linkedin.com/in/example-club",
        "twitter": "https://twitter.com/example-club",
        "youtube": "https://www.youtube.com/channel/example-club",
        "github": "https://github.com/example-club",
        "behance": "https://www.behance.net/example-club",
        "medium": "https://medium.com/@example-club",
        "gcalendar": "<google-calendar-link>",
        "discord": "<discord-invite-link>"
    },
    "last_updated": "2020-10-20T12:00:00"
}
```

## Edit profile info
* Description: Edits the club profile information
* Path: `POST /api/admin/profile`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "name": "Example Club",
    "link_name": "example-club",
    "owner": "exampleuser@berkeley.edu",
    "about_us": "This is something about the club.",
    "get_involved": "This is something about getting involved.",
    "app_required": true,
    "new_members": false,
    "num_users": 0,
    "apply_link": "https://www.apply-here-now.com",
    "apply_deadline_start": "2020-04-20T12:00:00",
    "apply_deadline_end": "2020-05-20T12:00:00",
    "recruiting_start": "2020-03-20T12:00:00",
    "recruiting_end": "2020-06-20T12:00:00",
    "tags": [1, 3, 4],
    "social_media_links": {
        "contact_email": "example-email@gmail.com",
        "website": "http://example.com/",
        "facebook": "https://www.facebook.com/pages/example-club",
        "instagram": "https://www.instagram.com/example-club",
        "linkedin": "https://www.linkedin.com/in/example-club",
        "twitter": "https://twitter.com/example-club",
        "youtube": "https://www.youtube.com/channel/example-club",
        "github": "https://github.com/example-club",
        "behance": "https://www.behance.net/example-club",
        "medium": "https://medium.com/@example-club",
        "gcalendar": "<google-calendar-link>",
        "discord": "<discord-invite-link>"
    }
}
```
* Sample body output:
```json
{
    "status": "success"
}
```

## Upload logo
* Description: Uploads the logo. Logos must respect a 1:1 aspect ratio. A 16 MB limit is imposed as well
* Path: `POST /api/admin/upload-logo`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
    * multipart/form-data
        * `logo` - logo image
* Sample body output
```json
{
    "status": "success",
    "logo_url": "https://sproul-club-images-prod.s3-us-west-1.amazonaws.com/logo/example-club-logo.png"
}
```

## Upload banner
* Description: Uploads the banner. banners must respect a 10:3 aspect ratio. A 16 MB limit is imposed as well
* Path: `POST /api/admin/upload-banner`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
    * multipart/form-data
        * `banner` - banner image
* Sample body output
```json
{
    "status": "success",
    "banner_url": "https://sproul-club-images-prod.s3-us-west-1.amazonaws.com/banner/example-club-banner.png"
}
```

## Resources

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

## Events

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

## Recruiting Events

### Get recruiting events
* Description: Gets all recruiting events from a club
* Path: `GET /api/admin/recruiting-events`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
[
    {
        "id": "example-recruiting-event-1",
        "name": "Example recruiting event 1",
        "link": "http://example.com/",
        "virtual_link": "https://zoom.com/example-link",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the event."
    }
]
```

### Add recruiting event
* Description: Adds a recruiting event to the club
* Path: `POST /api/admin/recruiting-events`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "name": "Example recruiting event 2",
    "link": "http://example.com/",
    "virtual_link": "https://zoom.com/example-link",
    "event_start": "2020-04-01T07:00:00.000Z",
    "event_end": "2020-08-01T07:00:00.000Z",
    "description": "This is something about the event."
}
```
* Sample body output:
```json
[
    {
        "id": "example-recruiting-event-1",
        "name": "Example recruiting event 1",
        "link": "http://example.com/",
        "virtual_link": "https://zoom.com/example-link",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the event."
    },
    {
        "id": "example-recruiting-event-2",
        "name": "Example recruiting event 2",
        "link": "http://example.com/",
        "virtual_link": "https://zoom.com/example-link",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the event."
    }
]
```

### Update recruiting nevent
* Description: Updates a recruiting nevent from the club
* Path: `PUT /api/admin/recruiting-events/<event-id>`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body input:
```json
{
    "name": "Example recruiting event 10",
    "link": "http://example.com/",
    "virtual_link": "https://zoom.com/example-link",
    "event_start": "2020-04-01T07:00:00.000Z",
    "event_end": "2020-08-01T07:00:00.000Z",
    "description": "This is something about the new event."
}
```
* Sample body output:
```json
[
    {
        "id": "example-recruiting-event-1",
        "name": "Example recruiting event 10",
        "link": "http://example.com/",
        "virtual_link": "https://zoom.com/example-link",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the new event."
    },
    {
        "id": "example-recruiting-event-2",
        "name": "Example recruiting event 2",
        "link": "http://example.com/",
        "virtual_link": "https://zoom.com/example-link",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the event."
    }
]
```

### Delete recruiting event
* Description: Deletes a recruiting event from the club
* Path: `DELETE /api/admin/recruiting-events/<event-id>`
* Headers:
    - `Authorization: Bearer <access_token>`
* Sample body output:
```json
[
    {
        "id": "example-recruiting-event-10",
        "name": "Example recruiting event 10",
        "link": "http://example.com/",
        "virtual_link": "https://zoom.com/example-link",
        "event_start": "2020-04-01T07:00:00.000Z",
        "event_end": "2020-08-01T07:00:00.000Z",
        "description": "This is something about the new event."
    }
]
```

## Change password
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
