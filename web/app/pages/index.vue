<template>
  <div class="starter">
    <header class="site-header">
      <NuxtLink to="/" class="brand"><span class="brand-mark">m.</span> Maldives Mobility</NuxtLink>
      <UBadge color="neutral" variant="subtle">Starter</UBadge>
    </header>
    <main>
      <div class="page-heading">
        <div><p class="eyebrow">A foundation for connected islands</p><h1>Map. Explore. Connect.</h1></div>
        <p class="page-description">A Nuxt workspace for your facilities atlas and transport simulator. Ready for your first layer.</p>
      </div>
      <ClientOnly>
        <MaldivesMap />
        <template #fallback><div class="map-shell map-placeholder" role="status">Preparing map…</div></template>
      </ClientOnly>
      <footer class="page-footer">
        <span>Nuxt · Vue · Nuxt UI · Mapbox</span>
        <UButton to="https://docs.mapbox.com/mapbox-gl-js/" target="_blank" rel="noopener noreferrer" color="neutral" variant="link" trailing-icon="i-lucide-arrow-up-right">Mapbox documentation</UButton>
      </footer>
    </main>
  </div>
</template>
