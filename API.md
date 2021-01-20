# sproul.club backend API

* Base URL (development): https://sc-backend-dev.herokuapp.com
* Base URL (production): https://sc-backend-prod.herokuapp.com

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

## API definitions

* [Admin API](docs/Admin-API.md)
* [Catalog API](docs/Catalog-API.md)
* [Monitor API](docs/Monitor-API.md)
* [Student API](docs/Student-API.md)
* [User API](docs/User-API.md)
