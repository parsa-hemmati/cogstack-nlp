# Clinical Care Tools - Frontend

Vue 3 + TypeScript + Vite + Vuetify frontend application for Clinical Care Tools.

## Tech Stack

- **Vue 3** - Progressive JavaScript Framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Next Generation Frontend Tooling
- **Vuetify** - Material Design Component Framework
- **Vue Router** - Official router for Vue.js
- **Pinia** - State management for Vue
- **Axios** - Promise-based HTTP client

## Project Structure

```
frontend/
├── src/
│   ├── main.ts              # Application entry point
│   ├── App.vue              # Root component
│   ├── router/              # Vue Router configuration
│   ├── stores/              # Pinia stores
│   ├── views/               # Page components
│   ├── components/          # Reusable components
│   ├── plugins/             # Plugin configurations
│   ├── styles/              # Global styles
│   └── types/               # TypeScript type definitions
├── index.html               # HTML entry point
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
└── package.json             # Dependencies and scripts
```

## Development

### Prerequisites

- Node.js 22.x (available in web environment)
- npm (comes with Node.js)

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

Application will be available at http://localhost:3000

### Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Lint code with ESLint
- `npm run format` - Format code with Prettier
- `npm run type-check` - Run TypeScript type checking

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## API Integration

The frontend proxies API requests to the backend:

- Development: `http://localhost:3000/api` → `http://localhost:8000/api`
- Production: Configure reverse proxy (nginx/Apache)

## Deployment

### Web Environment (Current)

1. Build the application: `npm run build`
2. Serve the `dist/` directory using a static file server
3. Configure reverse proxy for API requests

### Production (Docker)

See main project README for Docker deployment instructions.

## Sprint Progress

- **Phase 0**: ✅ Frontend structure created
- **Sprint 1**: 🔜 Patient Search & Discovery (next)
- **Sprint 2**: 🔜 Timeline View
- **Sprint 3+**: See `.specify/roadmap/ROADMAP.md`

## Contributing

Follow the Spec-Kit workflow defined in `CLAUDE.md`:

1. Read CONTEXT.md for current state
2. Check specifications in `.specify/specifications/`
3. Follow technical plans in `.specify/plans/`
4. Implement tasks from `.specify/tasks/`
5. Update CONTEXT.md with changes

## Compliance

This application handles PHI and must comply with HIPAA and GDPR. See `docs/compliance/` for requirements.
