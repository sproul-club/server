# Catalog API

## Fetch set of tags
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

## Fetch organizations
* Description: Fetches the list of organizations without filters, sorted alphabetically.
* Path: `GET /api/catalog/organizations?limit={limit}&skip={skip}`

* Sample body output:
```json
{
    "results": [
        {
            "id": "example-club",
            "name": "Example Club",
            "logo": "<logo-pic-url>",
            "banner": "<banner-pic-url>",
            "tags": [1, 3, 4],
            "app_required": true,
            "new_members": false,
        }
    ],
    "num_results": 1
}
```

## Fetch single organization
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