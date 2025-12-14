<template>
  <n-dropdown :options="languageOptions" @select="handleLanguageSelect">
    <n-button text>
      <template #icon>
        <n-icon :component="GlobeOutline" size="20" />
      </template>
      {{ currentLanguage.toUpperCase() }}
    </n-button>
  </n-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NDropdown, NButton, NIcon } from 'naive-ui'
import { GlobeOutline } from '@vicons/ionicons5'

const { locale } = useI18n()

const currentLanguage = computed(() => locale.value)

const languageOptions = [
  {
    label: 'English',
    key: 'en'
  },
  {
    label: 'Slovenščina',
    key: 'sl'
  },
  {
    label: 'Deutsch',
    key: 'de'
  },
  {
    label: 'Hrvatski',
    key: 'hr'
  },
  {
    label: 'Français',
    key: 'fr'
  },
  {
    label: 'Italiano',
    key: 'it'
  },
  {
    label: 'Español',
    key: 'es'
  },
  {
    label: 'Shqip',
    key: 'sq'
  },
  {
    label: 'Ελληνικά',
    key: 'el'
  }
]

const handleLanguageSelect = (key: string) => {
  locale.value = key
  localStorage.setItem('locale', key)
}
</script>
