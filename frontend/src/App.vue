<template>
  <div :class="{ 'nav-open': showSidebar }">
    <n-config-provider :theme="theme" :theme-overrides="themeOverrides">
      <n-global-style />
      <n-message-provider>
        <n-notification-provider>
          <n-dialog-provider>
            <router-view />
          </n-dialog-provider>
        </n-notification-provider>
      </n-message-provider>
    </n-config-provider>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, provide } from 'vue'
import { darkTheme, lightTheme, NConfigProvider, NGlobalStyle, NMessageProvider, NNotificationProvider, NDialogProvider } from 'naive-ui'

// Sidebar state
const showSidebar = ref(false)
provide('showSidebar', showSidebar)

// Always use Paper Dashboard theme (no theme selector)
const theme = computed(() => null) // Use light theme always

onMounted(() => {
  // Apply Paper Dashboard theme class to body
  document.documentElement.classList.remove('dark', 'greenmind')
  document.body.classList.remove('theme-greenmind', 'theme-dark', 'theme-light')
  document.body.classList.add('theme-paper')
})

// GreenMind color scheme (green accent on dark background)
const greenMindOverrides = {
  common: {
    primaryColor: '#54d944',
    primaryColorHover: '#6ee85b',
    primaryColorPressed: '#3cb82d',
    primaryColorSuppl: '#54d944',
    infoColor: '#54d944',
    successColor: '#54d944',
    warningColor: '#f0b90b',
    errorColor: '#ff4d4f',
  },
  Button: {
    textColorPrimary: '#1a1a1a',
    textColorHoverPrimary: '#1a1a1a',
    textColorPressedPrimary: '#1a1a1a',
    textColorFocusPrimary: '#1a1a1a',
    colorPrimary: '#54d944',
    colorHoverPrimary: '#6ee85b',
    colorPressedPrimary: '#3cb82d',
    colorFocusPrimary: '#54d944',
    borderPrimary: '1px solid #54d944',
    borderHoverPrimary: '1px solid #6ee85b',
    borderPressedPrimary: '1px solid #3cb82d',
    borderFocusPrimary: '1px solid #54d944',
  },
  Input: {
    borderHover: '1px solid #54d944',
    borderFocus: '1px solid #54d944',
    boxShadowFocus: '0 0 0 2px rgba(84, 217, 68, 0.2)',
    caretColor: '#54d944',
  },
  Card: {
    borderColor: 'rgba(84, 217, 68, 0.2)',
  },
  Menu: {
    // Remove all backgrounds - Paper Dashboard style
    itemColorActive: 'transparent',
    itemColorActiveHover: 'transparent',
    itemColorHover: 'transparent',
    // Text colors
    itemTextColor: 'rgba(255, 255, 255, 0.7)',
    itemTextColorActive: '#41B883',
    itemTextColorActiveHover: '#41B883',
    itemTextColorHover: 'rgba(255, 255, 255, 1)',
    itemTextColorChildActive: '#41B883',
    // Icon colors
    itemIconColor: 'rgba(255, 255, 255, 0.7)',
    itemIconColorActive: '#41B883',
    itemIconColorActiveHover: '#41B883',
    itemIconColorHover: 'rgba(255, 255, 255, 1)',
    itemIconColorChildActive: '#41B883',
    // Background
    color: 'transparent',
    // Arrow colors
    arrowColor: 'rgba(255, 255, 255, 0.7)',
    arrowColorActive: '#41B883',
    arrowColorActiveHover: '#41B883',
    arrowColorHover: 'rgba(255, 255, 255, 1)',
    arrowColorChildActive: '#41B883',
  }
}

// Standard dark theme overrides (blue accent)
const darkOverrides = {
  common: {
    primaryColor: '#3b82f6',
    primaryColorHover: '#60a5fa',
    primaryColorPressed: '#2563eb',
    primaryColorSuppl: '#3b82f6',
  }
}

// Light theme overrides (blue accent)
const lightOverrides = {
  common: {
    primaryColor: '#3b82f6',
    primaryColorHover: '#60a5fa',
    primaryColorPressed: '#2563eb',
    primaryColorSuppl: '#3b82f6',
  }
}

// Use Paper Dashboard theme overrides (based on greenMindOverrides with Paper colors)
const themeOverrides = computed(() => greenMindOverrides)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Paper Dashboard theme */
body.theme-paper,
body {
  font-family: 'Muli', "Helvetica Neue", Arial, sans-serif;
  background: #F5F5F5;
  min-height: 100vh;
  color: #66615B;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
}
</style>