<template>
  <component
    :is="tag"
    @click="hideSidebar"
    class="nav-item"
    v-bind="$attrs"
  >
    <a class="nav-link">
      <slot>
        <i v-if="icon" :class="icon"></i>
        <p>{{ name }}</p>
      </slot>
    </a>
  </component>
</template>
<script setup lang="ts">
import { inject, onMounted, onBeforeUnmount, getCurrentInstance } from 'vue'

interface Props {
  name?: string
  icon?: string
  tag?: string
  to?: string
}

const props = withDefaults(defineProps<Props>(), {
  tag: 'router-link'
})

const autoClose = inject('autoClose', true)
const addLink = inject<((link: any) => void) | null>('addLink', null)
const removeLink = inject<((link: any) => void) | null>('removeLink', null)

const instance = getCurrentInstance()

const hideSidebar = () => {
  // Sidebar auto-close functionality can be handled by parent
}

const isActive = () => {
  return instance?.proxy?.$el?.classList.contains('active')
}

onMounted(() => {
  if (addLink && instance) {
    addLink(instance.proxy)
  }
})

onBeforeUnmount(() => {
  if (removeLink && instance) {
    removeLink(instance.proxy)
  }
})
</script>
<style></style>
