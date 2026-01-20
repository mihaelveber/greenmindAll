<template>
  <nav class="navbar navbar-expand-lg navbar-light">
    <div class="container-fluid">
      <a class="navbar-brand">{{ routeName }}</a>
      <button
        class="navbar-toggler navbar-burger"
        type="button"
        @click="toggleSidebar"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-bar"></span>
        <span class="navbar-toggler-bar"></span>
        <span class="navbar-toggler-bar"></span>
      </button>
      <div class="collapse navbar-collapse">
        <ul class="navbar-nav ml-auto">
          <li class="nav-item" style="display: flex; align-items: center; gap: 12px;">
            <slot name="actions"></slot>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

interface Props {
  user?: any
}

defineProps<Props>()

const route = useRoute()

const emit = defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const routeName = computed(() => {
  const name = route.name?.toString() || ''
  return capitalizeFirstLetter(name)
})

const capitalizeFirstLetter = (string: string) => {
  if (!string) return ''
  return string.charAt(0).toUpperCase() + string.slice(1)
}

const toggleSidebar = () => {
  emit('toggle-sidebar')
}
</script>
<style></style>
