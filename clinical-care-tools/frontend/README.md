# Clinical Care Tools - Frontend

Vue 3 + TypeScript + Vuetify frontend for the Clinical Care Tools platform.

## Tech Stack

- **Framework**: Vue 3.5+ with Composition API
- **Build Tool**: Vite 6.3+
- **UI Library**: Vuetify 3.7+ (Material Design 3)
- **Language**: TypeScript 5.6+ (strict mode)
- **State Management**: Pinia 2+
- **Routing**: Vue Router 4+
- **HTTP Client**: Axios
- **Testing**: Vitest

## Prerequisites

- Node.js 20+ LTS or 22+
- npm 10+ or yarn 1.22+
- Docker (for production builds)

## Quick Start

### Development

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev

# Open browser at http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Docker build
docker build -t clinical-care-tools-frontend .

# Run Docker container
docker run -p 80:80 clinical-care-tools-frontend
```

## Project Structure

```
src/
├── main.ts           # Application entry point
├── App.vue           # Root component
├── router/           # Vue Router configuration
├── stores/           # Pinia stores
├── views/            # Page components
├── components/       # Reusable components
│   ├── layout/       # Layout components
│   └── common/       # Common components
├── composables/      # Composition API utilities
├── services/         # API services
├── types/            # TypeScript types
├── plugins/          # Vue plugins
└── assets/           # Static assets
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run unit tests
- `npm run test:ui` - Run tests with UI
- `npm run test:coverage` - Run tests with coverage
- `npm run lint` - Lint and fix files
- `npm run type-check` - Run TypeScript type checking

## Environment Variables

See `.env.example` for all available environment variables.

Key variables:
- `VITE_API_BASE_URL` - Backend API URL
- `VITE_AUTH_TOKEN_KEY` - JWT token storage key
- `VITE_MEDCAT_SERVICE_URL` - MedCAT service URL

## Features

- JWT authentication with refresh tokens
- Protected routes with navigation guards
- Responsive Material Design 3 UI
- Dark/light theme support
- API request/response interceptors
- Centralized error handling
- Loading states management
- TypeScript strict mode

## Code Style

- Vue 3 Composition API (no Options API)
- TypeScript strict mode
- ESLint + Prettier formatting
- Component naming: PascalCase
- Composables naming: use* prefix

## Testing

```bash
# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run with UI
npm run test:ui
```

## Security

- Content Security Policy (CSP) headers
- XSS protection
- HTTPS only in production
- JWT token rotation
- Secure cookie storage
- Input validation

## Performance

- Code splitting by routes
- Lazy loading components
- Tree shaking
- Vendor chunk optimization
- Image optimization
- Compression (gzip/brotli)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow Vue 3 Style Guide
2. Write tests for new features
3. Update documentation
4. Use conventional commits
5. Run linter before committing

## License

Proprietary - See LICENSE file