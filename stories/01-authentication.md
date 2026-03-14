# Story 1: User Authentication

## As a user, I want to register and log in so I can manage my scans securely.

### Acceptance Criteria
- POST /auth/register creates a new user with email + bcrypt password
- POST /auth/login returns a JWT token
- All scan/finding endpoints require valid JWT
- Passwords are never stored in plaintext
- JWT tokens expire after 24 hours

### Technical Notes
- Use python-jose for JWT encoding/decoding
- Use passlib with bcrypt for password hashing
- JWT_SECRET loaded from .env
