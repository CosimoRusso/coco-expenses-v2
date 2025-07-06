<script setup lang="ts">
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <header>
    <Navbar />
  </header>
  <main>
    <router-view />
  </main>
</template>

<style scoped>
main {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}
@media (max-width: 767px) {
  main {
    padding: 0;
  }
}
</style>
