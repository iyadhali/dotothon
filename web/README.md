# Nuxt + Mapbox boilerplate

This is a basic application scaffold. It contains one starter page, Nuxt UI, a client-only Mapbox component, public environment configuration and a health endpoint. It does **not** implement the facilities atlas, route simulator or QGIS integration.

## Run locally

Requirements: Node.js 24+, pnpm 9+; Python 3.10+ for the separate agent data tools.

From this directory:

```powershell
pnpm install
Copy-Item .env.example .env
# Set NUXT_PUBLIC_MAPBOX_TOKEN in .env, then:
pnpm dev
```

Open the local URL printed by Nuxt. Without a token, the page shows a setup placeholder and makes no Mapbox requests. Mapbox requires a browser-visible public token; configure allowed URLs in your Mapbox account. Never put a secret token in public runtime configuration.

```powershell
pnpm typecheck
pnpm build
pnpm preview
pnpm test
```

`pnpm test` runs the repository's Python agent-tool tests; it is not a UI test suite. The health endpoint is `/api/health`.

## Where to extend

| Path | Purpose |
|---|---|
| `app/pages/index.vue` | Minimal starter page |
| `app/components/MaldivesMap.client.vue` | Mapbox lifecycle and empty point, line and polygon layers |
| `app/assets/css/main.css` | Starter styling and Nuxt UI imports |
| `nuxt.config.ts` | Nuxt UI module and Mapbox public runtime config |
| `server/api/health.get.ts` | Example Nitro server endpoint |
| `../tools/` | Read-only repository data tools; separate from the web bundle |

The map component accepts an optional standard GeoJSON `FeatureCollection` as its `data` prop. Its source is initially empty. Keep raw datathon data outside `public/`; prepare only the fields needed for a particular layer before exposing them to a browser.

## Stack decisions

- **Nuxt + Vue + TypeScript:** matches the team's existing stack; Nuxt supplies routing, runtime configuration and Nitro endpoints.
- **Nuxt UI + Tailwind:** ready-made interface primitives with connected Nuxt/Nuxt UI documentation MCP tools. No UI map component is assumed.
- **Mapbox GL JS directly:** one client-only component, a hosted basemap and examples that match the installed Mapbox integration/data-visualisation/performance skills. Avoid adding another wrapper dependency to this starter.
- **Local catalogue tools:** the standard-library Python CLI and MCP stdio adapter expose dataset identities, schemas, samples and caveats without starting Nuxt. See [tools/README.md](../tools/README.md).
- **QGIS remains optional:** it can inspect or prepare GeoJSON/GeoPackage layers later. It is not needed to run the app, and no QGIS Server is provisioned.
- **Transport simulation is future work:** Mapbox's map and Directions API do not replace an RTL timetable-aware router. No route, demand or accessibility claims are produced by this starter.
- **Data stays local:** no database, raw dataset upload, live operator feed or data processing pipeline is introduced.

Mapbox MCP servers exist but are not required to run the app and have not been configured by this scaffold. [Official servers](https://docs.mapbox.com/location-ai/mcp-servers/). Nuxt and Nuxt UI docs MCP tools and Playwright tools were available in the authoring session.

References: [Nuxt](https://nuxt.com/docs/4.x/getting-started/introduction), [Nuxt UI setup](https://ui.nuxt.com/docs/getting-started/installation/nuxt), [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/), [Mapbox agent skills](https://github.com/mapbox/mapbox-agent-skills).

## Validation status

The agent data-tool tests run without dependencies. JavaScript package downloads were denied in the authoring environment, so the Nuxt production build and live Mapbox rendering could not be checked locally. The repository CI workflow installs packages, runs type checking/build and runs the Python tests on GitHub. A first successful dependency installation should retain the generated lockfile.
