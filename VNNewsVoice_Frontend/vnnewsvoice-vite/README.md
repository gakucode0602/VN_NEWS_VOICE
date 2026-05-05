# VNNewsVoice Frontend (Vite)

React + Vite frontend for VNNewsVoice. The app uses TanStack Query for data
fetching and axios with a shared API client that unwraps backend responses.

## Requirements
- Node.js 18+ (or 20+)
- Yarn 1.x

## Setup
```powershell
yarn
yarn dev
```

## Build and preview
```powershell
yarn build
yarn preview
```

## Environment
Create a `.env` file (see `.env.example`):
```
VITE_API_BASE_URL=http://localhost:8080/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

## Project structure
```
src/
  app/                App shell and providers
  components/         Shared layout components
  contexts/           UI state contexts (search filters)
  features/           Feature-first modules
    articles/
    auth/
    profile/
  hooks/              Reusable hooks
  lib/                Shared utilities (apiClient)
  styles/             Global and feature styles
```

## API response format
Backend responses use a wrapper:
```
{ "success": true, "code": 200, "message": "...", "result": ... }
```
`src/lib/apiClient.js` unwraps `result` and throws on `success: false`.
