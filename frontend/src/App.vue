<template>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { darkTheme, lightTheme, NConfigProvider, NGlobalStyle, NMessageProvider, NNotificationProvider, NDialogProvider } from 'naive-ui'

// Theme mode: 'greenmind' | 'dark' | 'light'
const themeMode = ref<'greenmind' | 'dark' | 'light'>(localStorage.getItem('theme') as any || 'greenmind')

// Computed theme based on mode
const isDarkMode = computed(() => {
  return themeMode.value === 'greenmind' || themeMode.value === 'dark'
})

const isGreenMind = computed(() => themeMode.value === 'greenmind')

const theme = computed(() => isDarkMode.value ? darkTheme : null)

onMounted(() => {
  // Watch for storage changes (cross-tab sync)
  window.addEventListener('storage', (e) => {
    if (e.key === 'theme') {
      themeMode.value = (e.newValue as any) || 'greenmind'
    }
  })
  
  // Apply theme class to body
  watch([isDarkMode, isGreenMind], ([dark, green]) => {
    document.documentElement.classList.toggle('dark', dark)
    document.documentElement.classList.toggle('greenmind', green)
    document.body.classList.toggle('theme-greenmind', green)
    document.body.classList.toggle('theme-dark', !green && dark)
    document.body.classList.toggle('theme-light', !dark)
  }, { immediate: true })
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

// Select theme overrides based on mode
const themeOverrides = computed(() => {
  if (themeMode.value === 'greenmind') return greenMindOverrides
  if (themeMode.value === 'dark') return darkOverrides
  return lightOverrides
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* GreenMind theme - dark with green accents */
body.theme-greenmind {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: radial-gradient(circle at 20% 30%, rgba(84, 217, 68, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 80% 70%, rgba(84, 217, 68, 0.1) 0%, transparent 50%),
              linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  min-height: 100vh;
  background-attachment: fixed;
  color: #ffffff;
}

/* Standard dark theme - no green accents */
body.theme-dark {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  min-height: 100vh;
  background-attachment: fixed;
  color: #ffffff;
}

/* Light theme */
body.theme-light {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
  min-height: 100vh;
  background-attachment: fixed;
  color: #1a1a1a;
}

/* Default/fallback */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}
</style>