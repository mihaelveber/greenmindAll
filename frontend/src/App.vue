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
import { ref, computed, onMounted } from 'vue'
import { darkTheme, NConfigProvider, NGlobalStyle, NMessageProvider, NNotificationProvider, NDialogProvider } from 'naive-ui'

// Default to dark theme (light theme has visibility issues)
const isDarkMode = ref(localStorage.getItem('theme') !== 'light')

const theme = computed(() => isDarkMode.value ? darkTheme : null)

onMounted(() => {
  // Watch for storage changes
  window.addEventListener('storage', (e) => {
    if (e.key === 'theme') {
      isDarkMode.value = e.newValue === 'dark'
    }
  })
})

// AI GREENMIND barvna shema
const themeOverrides = {
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
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: radial-gradient(circle at 20% 30%, rgba(84, 217, 68, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 80% 70%, rgba(84, 217, 68, 0.1) 0%, transparent 50%),
              linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  min-height: 100vh;
  background-attachment: fixed;
}

#app {
  min-height: 100vh;
}
</style>