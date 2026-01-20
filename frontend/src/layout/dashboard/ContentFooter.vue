<template>
  <footer class="footer">
    <div class="container-fluid d-flex flex-wrap justify-content-between">
      <nav>
        <ul>
          <li>
            <router-link :to="{ path: '/dashboard' }">Dashboard</router-link>
          </li>
        </ul>
      </nav>
      <div class="copyright d-flex flex-wrap">
        &copy; {{ new Date().getFullYear() }} GreenMind AI - ESRS Compliance Platform
      </div>
    </div>
  </footer>
</template>
<script setup lang="ts">
</script>
<style></style>
