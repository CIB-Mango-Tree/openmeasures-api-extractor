# CLAUDE.md - OpenMeasures API Extractor

> Comprehensive guide for AI assistants working on the OpenMeasures API Extractor codebase.

## Project Overview

**OpenMeasures API Extractor** is a cross-platform desktop application that extracts social media data from platforms like Bluesky and Truth Social via the OpenMeasures API. The application bundles a Python backend, React frontend, and Node.js launcher into standalone executables for Windows, macOS Intel, and macOS Apple Silicon.

**Key Features:**
- Query builder for social media data extraction
- Real-time progress updates via WebSocket
- Export to Excel, CSV, and JSON formats
- API rate limit tracking and alerts
- Dark/light theme support
- Cross-platform distribution (Windows, macOS)

**License:** MIT
**Organization:** CIB Mango Tree

---

## Repository Structure

This is a **monorepo** with three main components:

```
openmeasures-api-extractor/
├── api/          # Python backend API (Starlette/FastAPI-style)
├── app/          # Node.js application launcher/wrapper
├── site/         # React frontend (TanStack Start)
├── .github/      # GitHub Actions CI/CD workflows
├── LICENSE       # MIT license
├── README.md     # Project readme
└── mango.entitlements  # macOS code signing entitlements
```

### api/ - Python Backend

**Purpose:** REST API server that interfaces with OpenMeasures API for data extraction.

**Key Files:**
- `main.py` - Application entry point, routes, DI setup
- `pyinstaller.spec` - PyInstaller build configuration
- `pyproject.toml` - Python dependencies (managed by uv)
- `requirements.txt` - Locked dependencies
- `.python-version` - Python 3.13

**Architecture Pattern:** Clean layered architecture
```
Endpoints (HTTP/WebSocket) → Services → Repositories → Models
```

**Source Structure:**
```
api/src/
├── endpoints/        # HTTP/WebSocket request handlers
├── services/         # Business logic (QueryService, WebSocketService, etc.)
├── db/
│   ├── models/      # SQLAlchemy ORM models
│   ├── repositories/# Data access layer (repository pattern)
│   └── connection.py# Database initialization
├── validators/       # Pydantic request validators
├── serializers/      # Model-to-dict converters
├── websocket/        # WebSocket connection/topic management
├── utils/
│   ├── constants/   # Application constants
│   ├── responses/   # Response builders
│   └── export.py    # Data export utilities (Excel/CSV/JSON)
├── settings.py      # Environment-based configuration
├── log.py           # Logging setup
└── event.py         # Event types for real-time updates
```

**API Endpoints:**
- `GET/POST /api/queries` - List/create queries
- `GET/PATCH/DELETE /api/queries/{id}` - Query CRUD operations
- `GET /api/queries/{id}/download/{format}` - Export (xlsx/csv/json)
- `GET /api/limit` - Rate limit status
- `WS /api/ws/updates` - WebSocket for real-time progress
- `GET /api/platforms` - Available platforms

### app/ - Node.js Launcher

**Purpose:** Wrapper that bundles backend and frontend into a single executable.

**Key Files:**
- `index.ts` - Main entry point
- `src/start.ts` - Asset extraction and process management
- `src/screen.ts` - Terminal UI with ASCII art
- `src/dir.ts` - Directory utilities
- `copy_assets.sh` - Build script to copy backend/frontend

**Workflow:**
1. Extracts embedded assets (backend binary + frontend files) to app data directory
2. Uses MD5 hash caching to avoid re-extraction
3. Spawns backend process (Python on port 8000)
4. Spawns frontend process (Nitro server on port 3000)
5. Displays branded terminal UI
6. Handles graceful shutdown on SIGINT

### site/ - React Frontend

**Purpose:** Modern web UI for query management and monitoring.

**Key Files:**
- `src/routes/__root.tsx` - Root layout with theme provider
- `src/routes/index.tsx` - Main app page with WebSocket integration
- `src/router.tsx` - TanStack Router configuration
- `vite.config.ts` - Vite build configuration

**Source Structure:**
```
site/src/
├── components/
│   ├── ui/          # Shadcn UI components (Radix UI + Tailwind)
│   ├── builder.tsx  # Query builder form
│   ├── table.tsx    # Query results table
│   ├── results.tsx  # Results viewer
│   ├── details.tsx  # Query details dialog
│   ├── limit.tsx    # API limit tracking
│   └── header.tsx   # App header
├── lib/
│   ├── fetch/       # API client functions
│   ├── state/       # Zustand state stores
│   ├── types/       # TypeScript type definitions
│   ├── constants/   # Application constants
│   ├── websocket.ts # WebSocket client with auto-reconnect
│   ├── map.ts       # Response mappers
│   └── utils.ts     # Utility functions
└── routes/          # File-based routing (TanStack Router)
```

---

## Technology Stack

### Backend (api/)
- **Runtime:** Python 3.13
- **Package Manager:** uv (with locked dependencies)
- **Web Framework:** Starlette 0.47.3 (ASGI)
- **Server:** Uvicorn 0.35.0
- **ORM:** SQLAlchemy 2.0.43
- **Database:** SQLite (default, configurable)
- **Validation:** Pydantic 2.11.7
- **Data Processing:** Pandas 2.3.2, PyArrow 21.0.0
- **Export:** XlsxWriter 3.2.9
- **Events:** PyVentus 0.7.1
- **DI Container:** Lagom 2.7.7
- **WebSocket:** websockets 15.0.1
- **Packaging:** PyInstaller 6.16.0

### Frontend (site/)
- **Runtime:** Node.js 22.x
- **Package Manager:** pnpm 10.20.x
- **Framework:** React 19.0.0
- **Meta-Framework:** TanStack Start 1.132.0
- **Router:** TanStack Router 1.132.0
- **Build Tool:** Vite 7.1.7
- **Server:** Nitro v2 (SSR-capable)
- **Styling:** Tailwind CSS 4.0.6
- **UI Components:** Radix UI
- **State Management:** Zustand 5.0.8
- **Data Tables:** TanStack Table 8.21.3
- **Testing:** Vitest 3.0.5, Testing Library
- **TypeScript:** 5.7.2

### Application Wrapper (app/)
- **Runtime:** Node.js 22.x
- **Package Manager:** pnpm 10.7.0
- **Build Tool:** esbuild 0.27.0
- **Packager:** @yao-pkg/pkg 6.10.1
- **TypeScript:** 5.9.3

---

## Development Setup

### Prerequisites
- **Python:** 3.13+ (use pyenv or similar)
- **Node.js:** 22.x (use nvm or similar)
- **pnpm:** 10.7.0+
- **uv:** Latest version (Python package manager)

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd openmeasures-api-extractor
   ```

2. **Backend setup:**
   ```bash
   cd api
   uv sync --locked --all-extras --dev
   ```

3. **Frontend setup:**
   ```bash
   cd ../site
   pnpm install
   ```

4. **App wrapper setup:**
   ```bash
   cd ../app
   pnpm install
   ```

### Running in Development

**Backend only:**
```bash
cd api
python main.py
# Server runs on http://localhost:8000
```

**Frontend only:**
```bash
cd site
pnpm dev
# Development server runs on http://localhost:3000
```

**Full application (simulated):**
Run backend and frontend in separate terminals as shown above.

---

## Build and Deployment

### Multi-Stage Build Process

The application uses a three-stage build process:

**Stage 1: Backend Executable (PyInstaller)**
```bash
cd api
uv run pyinstaller pyinstaller.spec
# Output: api/dist/mango-tree-api-extractor-backend
```

**Stage 2: Frontend Production Build (Vite + Nitro)**
```bash
cd site
pnpm build
# Output: site/.output/, site/.nitro/, site/dist/
```

**Stage 3: Bundle Assets (Copy Script)**
```bash
cd app
./copy_assets.sh
# Copies backend and frontend to app/bundle/
```

**Stage 4: Application Executable (pkg)**
```bash
cd app
pnpm build     # Compile TypeScript
pnpm compile   # Create executable
# Output: app/dist/mango-tree-api-extractor-{platform}
```

### GitHub Actions CI/CD

**Workflows:**
- `.github/workflows/build_exe.yml` - Reusable build workflow
- `.github/workflows/release.yml` - Release workflow

**Build Matrix:**
- Windows 2022
- macOS 15 (Apple Silicon)
- macOS 15 Intel

**Triggers:**
- Push tags matching `v*.*.*`
- Manual workflow_dispatch

**Artifacts:**
- `mango-tree-api-extractor-windows.exe` + SHA1
- `mango-tree-api-extractor-macos-x86` + SHA1 + .pkg
- `mango-tree-api-extractor-macos-arm64` + SHA1 + .pkg

**macOS Code Signing:**
- Developer ID Application certificate
- Developer ID Installer certificate
- Notarization with Apple

**Required Secrets:**
- `APPLE_DEV_EMAIL`, `APP_SPEC_PASS`
- `DEV_APP_CERT`, `DEV_APP_CERT_PASS`
- `DEV_INST_CERT`, `DEV_INST_CERT_PASS`
- `APPLE_KEY_PASS`, `APPLE_APP_CERT_ID`
- `APPLE_INST_CERT_ID`, `TEAM_ID`

---

## Code Organization and Conventions

### Backend (Python)

**Architecture:** Clean Architecture / Layered Architecture

**Dependency Flow:**
```
Endpoints → Services → Repositories → Models
```

**Key Patterns:**
- **Repository Pattern:** Data access abstraction
- **Dependency Injection:** Lagom containers
- **Event-Driven:** PyVentus for real-time updates
- **Type Safety:** Type hints throughout
- **Validation:** Pydantic models

**Naming Conventions:**
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/Methods: `snake_case()`
- Constants: `UPPER_SNAKE_CASE`

**Important Services:**

1. **QueryService** (`api/src/services/query.py`)
   - Core business logic for data extraction
   - Fetches data from OpenMeasures API
   - Implements rate limiting and pagination
   - Emits real-time progress events
   - Query lifecycle states:
     - `FETCH_IN_PROGRESS` → `CLEAN_IN_PROGRESS` → `PARSE_IN_PROGRESS` → `QUERY_COMPLETE`

2. **WebSocketService** (`api/src/services/websocket.py`)
   - Manages WebSocket connections
   - Topic-based pub/sub for query updates
   - Broadcasts events to subscribed clients

3. **QueryExportService** (`api/src/services/export.py`)
   - Converts processed data to Excel/CSV/JSON
   - Uses Pandas for format conversion

**Database Models:**
- `Query` - Main query entity
- `QueryTerm` - Individual search terms
- `QueryRequest` - Request data storage
- `QueryLimit` - API rate limits

### Frontend (React/TypeScript)

**Architecture:** Feature-based organization

**Key Patterns:**
- **Functional Components:** React hooks
- **State Management:** Zustand stores (domain-separated)
- **Type Safety:** TypeScript strict mode
- **Path Aliases:** `@/`, `@components/`, `@lib/`, `@state/`
- **File-based Routing:** TanStack Router

**Naming Conventions:**
- Files: `kebab-case.tsx` or `camelCase.tsx`
- Components: `PascalCase`
- Hooks: `useCamelCase()`
- Utilities: `camelCase()`

**WebSocket Integration:**
- Custom WebSocket wrapper with auto-reconnect
- Event listeners for real-time updates:
  - `FETCH_UPDATE_PROGRESS` - Query progress
  - `CLEAN_IN_PROGRESS` - Data cleaning
  - `PARSE_IN_PROGRESS` - Data parsing
  - `FETCH_INCOMPLETE` - Requires user approval
  - `QUERY_COMPLETE` - Extraction finished
  - `LIMIT_UPDATE` - Rate limit changed
  - `LIMIT_MAXED_OUT` - Hit API limit

**State Persistence:**
- Uses localStorage for persistence
- Zustand stores: `limit`, `queries`, `meta`

### Application Launcher (Node.js)

**Key Functions:**
- `main()` - Entry point
- `start()` - Asset extraction and process spawning
- `extractAssets()` - Hash-based caching
- `drawScreen()` - Terminal UI

---

## Testing

### Frontend Testing
- **Framework:** Vitest 3.0.5
- **Testing Library:** @testing-library/react 16.2.0
- **Environment:** jsdom 27.0.0
- **Command:** `cd site && pnpm test`

**Note:** No test files currently exist in the repository.

### Backend Testing
- No testing framework currently configured
- Could use pytest if needed

---

## Git Workflow

### Branch Strategy

**Main Branch:** `main` (or master)

**Feature Branches:**
- Prefix: `claude/`
- Format: `claude/claude-md-{session-id}`
- Example: `claude/claude-md-minoqqm2e2oq517j-016GNUABkKNCNoh4TtCRS3wm`

**Important:** AI assistants must develop on the designated branch and push with `-u origin <branch-name>`.

### Commit Conventions

- Use clear, descriptive commit messages
- Focus on "why" rather than "what"
- Follow existing commit message style (see git log)
- Avoid committing secrets (.env, credentials.json)

### Git Commands

**Push:**
```bash
git push -u origin <branch-name>
# Retry up to 4 times with exponential backoff on network errors
```

**Fetch/Pull:**
```bash
git fetch origin <branch-name>
git pull origin <branch-name>
# Retry up to 4 times with exponential backoff on network errors
```

---

## Important Configuration Files

### api/pyproject.toml
- Python project metadata
- Dependencies (Starlette, SQLAlchemy, Pandas, etc.)
- Requires Python >=3.12

### api/pyinstaller.spec
- PyInstaller bundling configuration
- Hidden imports for dynamic modules
- Code signing configuration
- macOS entitlements reference

### api/src/settings.py
- Environment-based configuration
- API URL: `https://api.openmeasures.io/content`
- Database URL: SQLite in app data directory
- Host/Port configuration

### site/vite.config.ts
- Vite build configuration
- TanStack Start plugin
- Nitro v2 plugin for SSR
- Tailwind CSS plugin

### site/components.json
- Shadcn UI configuration
- Component aliases and paths
- Style: New York, Color: zinc

### mango.entitlements
- macOS app entitlements (plist)
- Allows unsigned executable memory (for Python runtime)
- Allows JIT compilation
- Disables library validation

### .gitignore
- Standard Python + Node.js ignores
- Build artifacts: dist/, build/, bundle/
- Environment files: api/.env

---

## Common Tasks

### Adding a New API Endpoint

1. **Define model** (if needed) in `api/src/db/models/`
2. **Create repository** in `api/src/db/repositories/`
3. **Create validator** in `api/src/validators/`
4. **Create serializer** in `api/src/serializers/`
5. **Create service** in `api/src/services/`
6. **Create endpoint** in `api/src/endpoints/`
7. **Register route** in `api/main.py`

### Adding a New Frontend Component

1. **Create component** in `site/src/components/`
2. **Define types** in `site/src/lib/types/`
3. **Add API client** in `site/src/lib/fetch/`
4. **Create state store** (if needed) in `site/src/lib/state/`
5. **Use component** in routes or other components

### Adding a New WebSocket Event

1. **Define event** in `api/src/event.py`
2. **Emit event** from service using EventEmitter
3. **Handle in WebSocketService** broadcast
4. **Add listener** in `site/src/routes/index.tsx`

### Modifying the Build Process

**Backend:**
- Update `api/pyinstaller.spec` for PyInstaller configuration
- Update `api/pyproject.toml` for dependencies

**Frontend:**
- Update `site/vite.config.ts` for Vite configuration
- Update `site/package.json` for dependencies

**App Wrapper:**
- Update `app/copy_assets.sh` for asset copying
- Update `app/package.json` pkg configuration for bundling

### Running Type Checks

**Backend:**
```bash
cd api
# No explicit type checker configured (could use mypy)
```

**Frontend:**
```bash
cd site
pnpm exec tsc --noEmit
```

**App:**
```bash
cd app
pnpm typecheck
```

---

## Security Considerations

### Code Signing (macOS)

The application is code-signed and notarized for macOS distribution:
- Uses Developer ID Application certificate
- Uses Developer ID Installer certificate
- Notarized with Apple for Gatekeeper compatibility

### Environment Variables

Never commit sensitive data:
- `api/.env` is gitignored
- Use environment variables for secrets
- Settings are in `api/src/settings.py`

### API Security

- Rate limiting enforced by OpenMeasures API
- Local SQLite database (no network exposure)
- WebSocket connections validated

---

## Troubleshooting

### Build Issues

**PyInstaller fails:**
- Check `api/pyinstaller.spec` for hidden imports
- Verify all dependencies are in requirements.txt
- Check Python version (must be 3.13)

**pkg fails:**
- Ensure `app/bundle/` contains all assets
- Run `./copy_assets.sh` before `pnpm compile`
- Check Node.js version (must be 22.x)

### Runtime Issues

**Backend fails to start:**
- Check SQLite database permissions
- Verify port 8000 is available
- Check logs for Python errors

**Frontend fails to start:**
- Check port 3000 is available
- Verify Nitro server is properly built
- Check for missing dependencies

**WebSocket connection fails:**
- Ensure backend is running on port 8000
- Check WebSocket endpoint: `ws://localhost:8000/api/ws/updates`
- Verify no firewall blocking

### Development Issues

**Type errors:**
- Run type checks: `tsc --noEmit`
- Update types in `site/src/lib/types/`

**Import errors:**
- Check path aliases in `site/vite.config.ts`
- Verify tsconfig.json paths

---

## Key Entry Points

### Backend Entry Point
**File:** `api/main.py`
**Function:** `main()`
**Port:** 8000

### Frontend Entry Point
**File:** `site/src/routes/index.tsx`
**Component:** `App`
**Port:** 3000

### Application Entry Point
**File:** `app/index.ts`
**Function:** `main()`
**Spawns:** Backend (8000) + Frontend (3000)

---

## Best Practices for AI Assistants

### Before Making Changes

1. **Read existing code** - Never propose changes without reading the file first
2. **Understand architecture** - Follow the layered architecture pattern
3. **Check conventions** - Use naming conventions consistently
4. **Review dependencies** - Don't add unnecessary dependencies

### When Making Changes

1. **Keep it simple** - Avoid over-engineering
2. **Maintain patterns** - Follow existing code organization
3. **Type safety** - Use type hints (Python) and TypeScript
4. **Test locally** - Run type checks before committing
5. **No breaking changes** - Maintain backward compatibility unless explicitly requested

### Code Quality

1. **No unused code** - Delete unused imports, functions, variables
2. **Clear names** - Use descriptive variable and function names
3. **Comments when needed** - Document complex logic only
4. **Security first** - Avoid vulnerabilities (XSS, SQL injection, etc.)
5. **Performance** - Consider performance for data processing operations

### Git Practices

1. **Work on feature branch** - Never commit directly to main
2. **Clear commit messages** - Explain why, not what
3. **Atomic commits** - One logical change per commit
4. **Push when done** - Use `git push -u origin <branch-name>`

---

## Resources

### Documentation
- **Starlette:** https://www.starlette.io/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **TanStack Start:** https://tanstack.com/start
- **TanStack Router:** https://tanstack.com/router
- **Vite:** https://vitejs.dev/
- **PyInstaller:** https://pyinstaller.org/

### Tools
- **uv:** https://github.com/astral-sh/uv
- **pnpm:** https://pnpm.io/
- **esbuild:** https://esbuild.github.io/
- **pkg:** https://github.com/yao-pkg/pkg

---

## Project Statistics

- **Backend:** ~1,668 lines of Python code
- **Frontend:** ~56 TypeScript/TSX files
- **Total Components:** 3 (api, site, app)
- **Supported Platforms:** Windows x64, macOS Intel, macOS ARM64
- **License:** MIT

---

**Last Updated:** 2025-12-01
**Version:** Based on current repository state
