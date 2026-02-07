<template>
  <div class="dashboard-container">
    <n-layout has-sider>
      <n-layout-sider
        bordered
        :width="420"
        :native-scrollbar="false"
        class="sidebar"
      >
        <div class="sidebar-title">
          <n-text strong style="font-size: 18px; color: rgba(255, 255, 255, 0.9);">
            GreenMind AI
          </n-text>
        </div>
        <n-menu
          :value="activeKey"
          :options="menuOptions"
          :default-expanded-keys="defaultExpandedKeys"
          @update:value="handleMenuUpdate"
        />
      </n-layout-sider>

      <n-layout>
        <n-layout-header bordered class="header">
          <div class="header-content">
            <n-space align="center" :size="16">
              <img src="/logo.png" alt="Greenmind AI" class="header-logo-img" />
              <n-h2 class="page-title">{{ pageTitle }}</n-h2>
            </n-space>
            <div class="user-section">
              <LanguageSelector />
              <n-dropdown :options="userDropdownOptions" @select="handleUserAction">
                <n-button text>
                  <template #icon>
                    <div style="font-size: 32px; line-height: 36px;">
                      {{ getAvatarEmoji(selectedAvatar) }}
                    </div>
                  </template>
                  {{ authStore.user?.username }}
                </n-button>
              </n-dropdown>
            </div>
          </div>
        </n-layout-header>

        <n-layout-content content-style="padding: 24px;">
          <router-view />
        </n-layout-content>

        <n-layout-footer bordered class="footer">
          <div class="footer-content">
            <div class="copyright">
              &copy; {{ currentYear }} <a href="https://greenmind.ai" target="_blank">GreenMind AI</a>, made with ❤️ for a sustainable future
            </div>
            <div class="footer-links">
              <a href="https://greenmind.ai" target="_blank">About Us</a>
              <a href="#" @click.prevent="message.info('Privacy Policy')">Privacy Policy</a>
              <a href="#" @click.prevent="message.info('Terms')">Terms</a>
            </div>
          </div>
        </n-layout-footer>
      </n-layout>
    </n-layout>

    <!-- Settings Modal -->
    <n-modal v-model:show="showSettingsModal" preset="card" title="⚙️ Settings" style="width: 600px;">
      <n-form label-placement="left" label-width="120px;">
        <n-form-item label="Language">
          <n-select
            v-model:value="selectedLanguage"
            :options="languageOptions"
            placeholder="Select language"
          />
        </n-form-item>

        <n-form-item label="Nickname">
          <n-input
            v-model:value="userNickname"
            placeholder="Enter your nickname"
            :disabled="true"
          >
            <template #prefix>
              <n-text>👤</n-text>
            </template>
          </n-input>
          <template #feedback>
            <n-text depth="3" style="font-size: 12px;">Username cannot be changed here</n-text>
          </template>
        </n-form-item>

        <n-form-item label="Avatar Icon">
          <n-select
            v-model:value="selectedAvatar"
            :options="avatarOptions"
            placeholder="Select your avatar"
          >
            <template #prefix>
              <n-text style="font-size: 20px;">{{ getAvatarEmoji(selectedAvatar) }}</n-text>
            </template>
          </n-select>
        </n-form-item>

        <n-form-item label="Preview">
          <n-space align="center" :size="16">
            <n-text style="font-size: 48px;">{{ getAvatarEmoji(selectedAvatar) }}</n-text>
            <n-space vertical :size="4">
              <n-text strong style="font-size: 16px;">{{ userNickname }}</n-text>
              <n-text depth="3" style="font-size: 12px;">{{ languageOptions.find(l => l.value === selectedLanguage)?.label }}</n-text>
            </n-space>
          </n-space>
        </n-form-item>

        <!-- Company Branding -->
        <n-divider title-placement="left">🎨 Company Branding</n-divider>

        <n-alert type="info" style="margin-bottom: 16px;">
          Upload your company logo to generate branded PDF reports with AI-analyzed colors and styling.
        </n-alert>

        <n-form-item label="Company Logo">
          <n-space vertical style="width: 100%;">
            <n-upload
              ref="logoUploadRef"
              :max="1"
              accept="image/png,image/jpeg,image/jpg,image/webp"
              :custom-request="handleLogoUpload"
              @before-upload="beforeLogoUpload"
              :show-file-list="false"
            >
              <n-button>
                <template #icon>
                  <n-icon :component="CloudUploadOutline" />
                </template>
                Choose Logo
              </n-button>
            </n-upload>

            <div v-if="brandingInfo.logo_url" style="margin-top: 12px;">
              <n-space align="center" :size="16">
                <img
                  :src="brandingInfo.logo_url"
                  alt="Company Logo"
                  style="max-width: 120px; max-height: 80px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);"
                />
                <n-space vertical :size="4">
                  <n-text strong>Current Logo</n-text>
                  <n-button size="small" type="error" @click="deleteLogo" :loading="deletingLogo">
                    Delete Logo
                  </n-button>
                </n-space>
              </n-space>
            </div>

            <div v-if="uploadingLogo" style="margin-top: 12px;">
              <n-spin size="small">
                <n-text depth="3">Analyzing logo with AI...</n-text>
              </n-spin>
            </div>
          </n-space>
        </n-form-item>

        <n-form-item v-if="brandingInfo.brand_style?.colors" label="Brand Colors">
          <n-space :size="12">
            <div v-for="(color, key) in brandingInfo.brand_style.colors" :key="key" style="text-align: center;">
              <div
                :style="{
                  width: '50px',
                  height: '50px',
                  backgroundColor: color,
                  borderRadius: '8px',
                  border: '2px solid rgba(255,255,255,0.2)',
                  marginBottom: '4px'
                }"
              ></div>
              <n-text depth="3" style="font-size: 10px;">{{ key }}</n-text>
            </div>
          </n-space>
        </n-form-item>

        <n-form-item v-if="brandingInfo.brand_style?.personality" label="Brand Personality">
          <n-space :size="8">
            <n-tag
              v-for="trait in brandingInfo.brand_style.personality"
              :key="trait"
              type="success"
            >
              {{ trait }}
            </n-tag>
          </n-space>
        </n-form-item>

        <!-- RAG TIER Settings -->
        <n-divider title-placement="left">🚀 AI RAG Configuration</n-divider>

        <n-alert type="info" style="margin-bottom: 16px;">
          Configure when TIER 1, TIER 2, or TIER 3 RAG enhancements are used based on confidence thresholds.
        </n-alert>

        <n-form-item>
          <n-space vertical style="width: 100%;">
            <n-space align="center" style="width: 100%; justify-content: space-between;">
              <n-text strong>TIER 1</n-text>
              <n-switch v-model:value="ragSettings.tier1_enabled">
                <template #checked>Enabled</template>
                <template #unchecked>Disabled</template>
              </n-switch>
            </n-space>
            <n-text depth="3" style="font-size: 12px;">
              Hybrid BM25 + Embeddings search (60% semantic + 40% keyword)
            </n-text>
          </n-space>
        </n-form-item>

        <n-form-item>
          <n-space vertical style="width: 100%;">
            <n-text strong>TIER 2 Threshold</n-text>
            <n-slider
              v-model:value="ragSettings.tier2_threshold"
              :min="0"
              :max="100"
              :step="5"
              :marks="{ 0: '0%', 40: '40%', 60: '60%', 80: '80%', 100: '100%' }"
            />
            <n-text depth="3" style="font-size: 12px;">
              Use Multi-Query + Document Expansion when confidence &lt; {{ ragSettings.tier2_threshold }}%
            </n-text>
          </n-space>
        </n-form-item>

        <n-form-item>
          <n-space vertical style="width: 100%;">
            <n-space align="center" style="width: 100%; justify-content: space-between;">
              <n-text strong>TIER 3</n-text>
              <n-switch v-model:value="ragSettings.tier3_enabled">
                <template #checked>Enabled</template>
                <template #unchecked>Disabled</template>
              </n-switch>
            </n-space>
            <n-text depth="3" style="font-size: 12px;">
              LLM Self-Reflection + Query Reformulation + Reranking
            </n-text>
          </n-space>
        </n-form-item>

        <n-form-item>
          <n-space vertical style="width: 100%;">
            <n-text strong>TIER 3 Threshold</n-text>
            <n-slider
              v-model:value="ragSettings.tier3_threshold"
              :min="0"
              :max="100"
              :step="5"
              :marks="{ 0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%' }"
            />
            <n-text depth="3" style="font-size: 12px;">
              Use Contextual Retrieval + Reranking when confidence &lt; {{ ragSettings.tier3_threshold }}%
            </n-text>
          </n-space>
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showSettingsModal = false">Cancel</n-button>
          <n-button type="primary" @click="saveSettings">Save Settings</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth.store'
import {
  useMessage,
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NLayoutFooter,
  NMenu,
  NGradientText,
  NH2,
  NDropdown,
  NButton,
  NSpace,
  NText,
  NIcon,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NAlert,
  NUpload,
  NSwitch,
  NSlider,
  NDivider,
  NSpin,
  NTag,
  type MenuOption,
  type UploadCustomRequestOptions
} from 'naive-ui'
import {
  HomeOutline,
  PersonOutline,
  LogOutOutline,
  SettingsOutline,
  DocumentTextOutline,
  ClipboardOutline,
  CloudUploadOutline,
  ChevronDownOutline
} from '@vicons/ionicons5'
import LanguageSelector from '../components/LanguageSelector.vue'
import api from '../services/api'

interface StandardType {
  type: string
  name: string
  description: string
  icon: string
  total_requirements: number
  answered_requirements: number
  completion_percentage: number
}

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const message = useMessage()
const { t, locale } = useI18n()

const activeKey = ref('dashboard')
const standardTypes = ref<StandardType[]>([])
const esrsStandards = ref<any[]>([])
const currentYear = new Date().getFullYear()
const defaultExpandedKeys = ref<string[]>(['esrs-reporting'])

// Settings modal state
const showSettingsModal = ref(false)
const userNickname = ref(authStore.user?.username || '')
const selectedAvatar = ref(localStorage.getItem('userAvatar') || 'default')
const selectedLanguage = ref(localStorage.getItem('locale') || 'en')

// RAG TIER Settings
const ragSettings = ref({
  tier1_enabled: true,
  tier2_threshold: 60,
  tier3_enabled: false,
  tier3_threshold: 40
})

// Branding state
const brandingInfo = ref<{
  has_logo: boolean
  logo_url: string | null
  brand_style: any
}>({
  has_logo: false,
  logo_url: null,
  brand_style: null
})

const uploadingLogo = ref(false)
const deletingLogo = ref(false)
const logoUploadRef = ref()

const avatarOptions = [
  { label: '👤 Default', value: 'default' },
  { label: '🌿 Green Leaf', value: 'leaf' },
  { label: '🌍 Earth', value: 'earth' },
  { label: '♻️ Recycle', value: 'recycle' },
  { label: '🌱 Seedling', value: 'seedling' },
  { label: '🌳 Tree', value: 'tree' },
  { label: '💚 Green Heart', value: 'heart' },
  { label: '⚡ Energy', value: 'energy' },
  { label: '🏭 Factory', value: 'factory' },
  { label: '📊 Chart', value: 'chart' }
]

const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Slovenščina', value: 'sl' },
  { label: 'Deutsch', value: 'de' }
]

const pageTitle = computed(() => {
  if (route.name === 'dashboard') return t('dashboard.title')
  if (route.name === 'standards') return t('nav.standardsReporting', { standard: route.params.standardType })
  if (route.name === 'documents') return t('nav.documents')
  if (route.name === 'team') return t('nav.teamManagement')
  return 'GreenMind AI'
})

const menuOptions = computed(() => {
  const baseMenu = [
    {
      label: t('nav.dashboard'),
      key: 'dashboard',
      icon: () => h(NIcon, null, { default: () => h(HomeOutline) })
    }
  ]

  // Add ESRS Reporting with submenu grouped by category (ESRS, E, S, G)
  const groupStandardsByPrefix = (standards: any[]) => {
    const groups: any = { ESRS: [], E: [], S: [], G: [] }

    standards.forEach(standard => {
      if (standard.code.startsWith('ESRS')) {
        groups.ESRS.push(standard)
      } else if (standard.code.startsWith('E')) {
        groups.E.push(standard)
      } else if (standard.code.startsWith('S')) {
        groups.S.push(standard)
      } else if (standard.code.startsWith('G')) {
        groups.G.push(standard)
      }
    })

    return groups
  }

  const groupedStandards = groupStandardsByPrefix(esrsStandards.value)

  const esrsSubMenu = [
    // ESRS group
    ...(groupedStandards.ESRS.length > 0 ? [{
      type: 'group',
      label: t('nav.groupEsrs'),
      key: 'group-esrs',
      children: groupedStandards.ESRS.map((standard: any) => ({
        label: `${standard.code}: ${standard.name}`,
        key: `esrs-standard-${standard.id}`,
        icon: () => h(NIcon, null, { default: () => h(ClipboardOutline) })
      }))
    }] : []),
    // Environmental group
    ...(groupedStandards.E.length > 0 ? [{
      type: 'group',
      label: t('nav.groupEnvironmental'),
      key: 'group-e',
      children: groupedStandards.E.map((standard: any) => ({
        label: `${standard.code}: ${standard.name}`,
        key: `esrs-standard-${standard.id}`,
        icon: () => h(NIcon, null, { default: () => h(ClipboardOutline) })
      }))
    }] : []),
    // Social group
    ...(groupedStandards.S.length > 0 ? [{
      type: 'group',
      label: t('nav.groupSocial'),
      key: 'group-s',
      children: groupedStandards.S.map((standard: any) => ({
        label: `${standard.code}: ${standard.name}`,
        key: `esrs-standard-${standard.id}`,
        icon: () => h(NIcon, null, { default: () => h(ClipboardOutline) })
      }))
    }] : []),
    // Governance group
    ...(groupedStandards.G.length > 0 ? [{
      type: 'group',
      label: t('nav.groupGovernance'),
      key: 'group-g',
      children: groupedStandards.G.map((standard: any) => ({
        label: `${standard.code}: ${standard.name}`,
        key: `esrs-standard-${standard.id}`,
        icon: () => h(NIcon, null, { default: () => h(ClipboardOutline) })
      }))
    }] : [])
  ]

  // Add other standard types
  const otherStandards = standardTypes.value
    .filter(standard => standard.type !== 'ESRS')
    .map(standard => ({
      label: standard.name,
      key: `standard-${standard.type}`,
      icon: () => h(NIcon, null, { default: () => h(ClipboardOutline) })
    }))

  const esrsReportingMenu = esrsSubMenu.length > 0 ? [{
    label: t('nav.esrsReporting'),
    key: 'esrs-reporting',
    icon: () => h(NIcon, null, { default: () => h(ClipboardOutline) }),
    children: esrsSubMenu
  }] : []

  // Check if user can manage team (admin or organization owner)
  const canManageTeam = authStore.user?.is_staff || authStore.user?.is_organization_owner

  const otherMenus = [
    {
      label: t('nav.documents'),
      key: 'documents',
      icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) })
    },
    // Only show Team Management for admins and organization owners
    ...(canManageTeam ? [{
      label: t('nav.teamManagement'),
      key: 'team',
      icon: () => h(NIcon, null, { default: () => h(PersonOutline) })
    }] : []),
    {
      label: t('nav.profile'),
      key: 'profile',
      icon: () => h(NIcon, null, { default: () => h(PersonOutline) })
    },
    {
      label: t('nav.settings'),
      key: 'settings',
      icon: () => h(NIcon, null, { default: () => h(SettingsOutline) })
    }
  ]

  return [...baseMenu, ...esrsReportingMenu, ...otherStandards, ...otherMenus]
})

const userDropdownOptions = [
  {
    label: 'Profil',
    key: 'profile'
  },
  {
    label: 'Nastavitve',
    key: 'settings'
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: 'Odjava',
    key: 'logout'
  }
]

// Update active key based on route
watch(() => route.path, (newPath) => {
  if (newPath === '/dashboard') {
    activeKey.value = 'dashboard'
  } else if (newPath.startsWith('/standards/ESRS')) {
    // Check if there's a standard query parameter
    const standardId = route.query.standard
    if (standardId) {
      activeKey.value = `esrs-standard-${standardId}`
    } else {
      activeKey.value = 'esrs-reporting'
    }
  } else if (newPath.startsWith('/standards/')) {
    const standardType = route.params.standardType as string
    activeKey.value = `standard-${standardType}`
  } else if (newPath === '/documents') {
    activeKey.value = 'documents'
  } else if (newPath === '/team') {
    activeKey.value = 'team'
  }
}, { immediate: true })

const handleMenuUpdate = async (key: string) => {
  if (key === 'dashboard') {
    activeKey.value = 'dashboard'
    router.push('/dashboard')
  } else if (key === 'esrs-reporting') {
    // Don't navigate, just expand/collapse
    return
  } else if (key.startsWith('esrs-standard-')) {
    activeKey.value = key
    const standardId = key.replace('esrs-standard-', '')
    router.push({ path: '/standards/ESRS', query: { standard: standardId } })
  } else if (key.startsWith('standard-')) {
    activeKey.value = key
    const standardType = key.replace('standard-', '')
    router.push(`/standards/${standardType}`)
  } else if (key === 'team') {
    activeKey.value = 'team'
    router.push('/team')
  } else if (key === 'documents') {
    activeKey.value = 'documents'
    router.push('/documents')
  } else if (key === 'bulk-processing') {
    activeKey.value = 'bulk-processing'
    router.push('/bulk-processing')
  } else if (key === 'settings') {
    showSettingsModal.value = true
    // Load branding info when opening settings
    await loadBrandingInfo()
  } else if (key === 'profile') {
    activeKey.value = 'profile'
    message.info('Profile page coming soon')
  } else {
    activeKey.value = key
    message.info(`Navigacija na: ${key}`)
  }
}

const handleUserAction = async (key: string) => {
  if (key === 'logout') {
    await authStore.logout()
    message.success('Uspešno ste se odjavili')
    router.push('/login')
  } else if (key === 'settings') {
    showSettingsModal.value = true
    await loadBrandingInfo()
  } else {
    message.info(`Akcija: ${key}`)
  }
}

const saveSettings = async () => {
  try {
    // Save avatar
    localStorage.setItem('userAvatar', selectedAvatar.value)

    // Save and change language
    localStorage.setItem('locale', selectedLanguage.value)
    locale.value = selectedLanguage.value

    // Save RAG TIER settings to backend
    await api.post('/auth/update-rag-settings', {
      rag_tier1_enabled: ragSettings.value.tier1_enabled,
      rag_tier2_threshold: ragSettings.value.tier2_threshold,
      rag_tier3_enabled: ragSettings.value.tier3_enabled,
      rag_tier3_threshold: ragSettings.value.tier3_threshold
    })

    showSettingsModal.value = false
    message.success('Settings saved successfully!')

    // Reload page to apply language changes
    window.location.reload()
  } catch (error: any) {
    console.error('Error saving RAG settings:', error)
    message.error('Failed to save RAG settings')
  }
}

const getAvatarEmoji = (avatarValue: string) => {
  const avatar = avatarOptions.find(a => a.value === avatarValue)
  return avatar ? avatar.label.split(' ')[0] : '👤'
}

// Branding functions
const loadBrandingInfo = async () => {
  try {
    const response = await api.get('/branding/style')
    brandingInfo.value = response.data
  } catch (error) {
    console.error('Failed to load branding:', error)
  }
}

const beforeLogoUpload = (data: { file: { file: File | null }; fileList: any[] }) => {
  const file = data.file.file
  if (!file) {
    message.error('No file selected')
    return false
  }

  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    message.error('Please upload an image file (PNG, JPG, WEBP)')
    return false
  }

  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    message.error(`Logo must be smaller than 5MB (current: ${(file.size / 1024 / 1024).toFixed(2)}MB)`)
    return false
  }

  return true
}

const handleLogoUpload = async (options: UploadCustomRequestOptions) => {
  const { file, onFinish, onError } = options
  uploadingLogo.value = true

  try {
    const formData = new FormData()
    formData.append('file', file.file as File)

    const response = await api.post('/branding/upload-logo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    brandingInfo.value = {
      has_logo: true,
      logo_url: response.data.logo_url,
      brand_style: response.data.brand_style
    }

    message.success('Logo uploaded and analyzed with AI successfully! 🎨')
    onFinish()
  } catch (error: any) {
    console.error('Failed to upload logo:', error)
    message.error(error.response?.data?.message || 'Failed to upload logo')
    onError()
  } finally {
    uploadingLogo.value = false
  }
}

const deleteLogo = async () => {
  deletingLogo.value = true
  try {
    await api.delete('/branding/logo')
    brandingInfo.value = {
      has_logo: false,
      logo_url: null,
      brand_style: null
    }
    message.success('Logo deleted successfully')
  } catch (error: any) {
    console.error('Failed to delete logo:', error)
    message.error('Failed to delete logo')
  } finally {
    deletingLogo.value = false
  }
}

const loadStandardTypes = async () => {
  try {
    const response = await api.get('/standards/types')
    standardTypes.value = response.data
  } catch (error) {
    message.error('Failed to load standard types')
    console.error(error)
  }
}

const loadESRSStandards = async () => {
  try {
    const response = await api.get('/esrs/standards')
    // Filter only ESRS standards and sort by code
    esrsStandards.value = response.data
      .filter((s: any) => s.category?.standard_type === 'ESRS')
      .sort((a: any, b: any) => {
        // Sort by code (ESRS 1, ESRS 2, E1, E2, etc.)
        return a.code.localeCompare(b.code, undefined, { numeric: true })
      })
  } catch (error) {
    console.error('Failed to load ESRS standards:', error)
  }
}

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchCurrentUser()
  }

  // Load RAG TIER settings
  try {
    const response = await api.get('/auth/rag-settings')
    if (response.data) {
      ragSettings.value = {
        tier1_enabled: response.data.rag_tier1_enabled ?? true,
        tier2_threshold: response.data.rag_tier2_threshold ?? 60,
        tier3_enabled: response.data.rag_tier3_enabled ?? false,
        tier3_threshold: response.data.rag_tier3_threshold ?? 40
      }
    }
  } catch (error) {
    console.error('Error loading RAG settings:', error)
  }

  // Load branding info
  await loadBrandingInfo()

  // Load standard types for menu
  await loadStandardTypes()

  // Load ESRS standards for submenu
  await loadESRSStandards()
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
}

.sidebar {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(20px);
}

.sidebar-title {
  padding: 20px 24px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(20px);
  padding: 0 24px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.header-logo-img {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  object-fit: cover;
}

.page-title {
  margin: 0;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.footer {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(20px);
  padding: 20px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.copyright {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.copyright a {
  color: #41B883;
  text-decoration: none;
  font-weight: 600;
}

.copyright a:hover {
  color: #54d944;
}

.footer-links {
  display: flex;
  gap: 24px;
}

.footer-links a {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s ease;
}

.footer-links a:hover {
  color: #41B883;
}
</style>
