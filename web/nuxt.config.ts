export default defineNuxtConfig({
  compatibilityDate: '2026-10-24',
  modules: ['@nuxt/ui'],
  css: [
    '~/assets/css/main.css',
    'mapbox-gl/dist/mapbox-gl.css',
    '~/assets/css/multimodal.css',
  ],
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
      title: 'Island Access Atlas — Maldives multimodal accessibility',
      meta: [
        {
          name: 'description',
          content:
            'Reference-day access to health and education facilities across the Maldives: verified ferry timetables, estimated air frequencies and explicit coverage limits.',
        },
        { name: 'theme-color', content: '#faf9f5' },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
      htmlAttrs: { lang: 'en' },
    },
  },
  typescript: { strict: true },
})
