export default defineNuxtConfig({
  compatibilityDate: '2026-10-24',
  modules: ['@nuxt/ui'],
  css: ['~/assets/css/main.css', 'mapbox-gl/dist/mapbox-gl.css'],
  devtools: { enabled: false },
  ui: { fonts: false, colorMode: false },
  icon: { serverBundle: { collections: ['lucide'] } },
  runtimeConfig: {
    public: {
      mapboxToken: '',
      mapboxStyle: 'mapbox://styles/mapbox/light-v11',
    },
  },
  app: {
    head: {
      title: 'Maldives Mobility — Starter',
      meta: [{ name: 'description', content: 'Nuxt, Nuxt UI and Mapbox starter for a Maldives facilities map and transport simulator.' }],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
      htmlAttrs: { lang: 'en' },
    },
  },
  typescript: { strict: true },
})
