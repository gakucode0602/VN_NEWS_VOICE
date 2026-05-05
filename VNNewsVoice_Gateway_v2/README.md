# VNNewsVoice Gateway v2

This folder is reserved for the new microservices gateway setup.

- Do not modify the legacy gateway folder: `VNNewsVoice_Gateway`.
- All new gateway changes for the current migration should be made here.

## Local Startup

1. Start backend services on host machine:
	- AuthService: `localhost:8084`
	- ArticleService: `localhost:8080`
	- CommentService: `localhost:8083`
	- RAG Service: `localhost:8000`
2. Start gateway container:
	- `docker compose up -d`
3. Gateway entrypoint:
	- `http://localhost:8088`

## Routing Table

- `/api/user/**` -> AuthService
- `/api/auth/**` -> AuthService
- `/api/secure/admin/users**` -> AuthService
- `/api/secure/profile**` -> AuthService
- `/api/secure/change-password` -> AuthService
- `/api/.well-known/jwks.json` -> AuthService
- `/api/articles/{id}/comments**` -> CommentService
- `/api/secure/articles/{id}/comments**` -> CommentService
- `/api/comments**` + `/api/secure/comments**` -> CommentService
- `/chat/**` -> RAG Service (`/api/v1/chat/**`)
- `/api/v1/**` -> RAG Service (compatibility alias)
- remaining `/api/**` -> ArticleService
