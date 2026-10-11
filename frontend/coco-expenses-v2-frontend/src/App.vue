<script setup lang="ts">
import AppNavbar from '@/components/AppNavbar.vue'
</script>

<template>
  <header>
    <AppNavbar />
  </header>
  <main>
    <router-view />
  </main>
</template>

<style scoped>
main {
  padding: 2rem;
  max-width: 1440px;
  margin: 0 auto;
}
@media (max-width: 767px) {
  main {
    padding: 0;
  }
}
</style>
