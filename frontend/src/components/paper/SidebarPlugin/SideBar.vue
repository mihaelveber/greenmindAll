<template>
  <div
    class="sidebar"
    :data-background-color="backgroundColor"
    :data-active-color="activeColor"
  >
    <div class="sidebar-wrapper" id="style-3">
      <div class="logo">
        <router-link to="/dashboard" class="simple-text">
          <div class="logo-img">
            <img src="@/assets/img/new_logo.png" alt="GreenMind AI Logo" />
          </div>
          {{ title }}
        </router-link>
      </div>
      <slot></slot>
      <ul class="nav">
        <slot name="links">
          <sidebar-link
            v-for="(link, index) in sidebarLinks"
            :key="index"
            :to="link.path"
            :name="link.name"
            :icon="link.icon"
          >
          </sidebar-link>
        </slot>
      </ul>
      <moving-arrow :move-y="arrowMovePx"></moving-arrow>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, provide, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import MovingArrow from "./MovingArrow.vue"
import SidebarLink from "./SidebarLink.vue"

interface Props {
  title?: string
  backgroundColor?: 'white' | 'black' | 'darkblue'
  activeColor?: 'primary' | 'info' | 'success' | 'warning' | 'danger'
  sidebarLinks?: Array<{ path: string; name: string; icon: string }>
  autoClose?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'GreenMind AI',
  backgroundColor: 'black',
  activeColor: 'success',
  sidebarLinks: () => [],
  autoClose: true
})

const route = useRoute()
const linkHeight = 65
const activeLinkIndex = ref(0)
const links = ref<any[]>([])

const arrowMovePx = computed(() => linkHeight * activeLinkIndex.value)

const findActiveLink = () => {
  links.value.forEach((link, index) => {
    if (link.isActive && link.isActive()) {
      activeLinkIndex.value = index
    }
  })
}

const addLink = (link: any) => {
  links.value.push(link)
}

const removeLink = (link: any) => {
  const index = links.value.indexOf(link)
  if (index > -1) {
    links.value.splice(index, 1)
  }
}

provide('autoClose', props.autoClose)
provide('addLink', addLink)
provide('removeLink', removeLink)

onMounted(() => {
  watch(() => route.path, findActiveLink, { immediate: true })
})
</script>
<style></style>
