<template>
  <div class="dashboard-container">
    <n-layout has-sider>
      <n-layout-sider
        bordered
        :width="240"
        :native-scrollbar="false"
        class="sidebar"
      >
        <div class="logo">
          <img src="/logo.png" alt="Greenmind AI" class="logo-img" />
          <n-gradient-text :size="20" type="info">
            Greenmind AI
          </n-gradient-text>
        </div>
        <n-menu
          :value="activeKey"
          :options="menuOptions"
          @update:value="handleMenuUpdate"
        />
      </n-layout-sider>

      <n-layout>
        <n-layout-header bordered class="header">
          <div class="header-content">
            <n-space align="center" :size="16">
              <n-h2 class="page-title">{{ t('dashboard.title') }}</n-h2>
              <n-space :size="12">
                <n-button type="primary" @click="exportPDF" :loading="exportingPDF">
                  <template #icon>
                    <n-icon :component="DocumentTextOutline" />
                  </template>
                  Export PDF
                </n-button>
                <n-button type="info" @click="exportWord" :loading="exportingWord">
                  <template #icon>
                    <n-icon :component="DocumentTextOutline" />
                  </template>
                  Export Word
                </n-button>
              </n-space>
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
          <n-grid :cols="1" :x-gap="24" :y-gap="24" responsive="screen">
            <!-- Active AI Tasks Monitor -->
            <n-gi v-if="activeTasks.length > 0">
              <n-card title="🤖 Active AI Processing" :bordered="false">
                <n-space vertical :size="16">
                  <n-text depth="3">{{ activeTasks.length }} task(s) in progress</n-text>
                  <n-space vertical :size="12">
                    <div v-for="task in activeTasks" :key="task.task_id" class="task-item">
                      <n-space justify="space-between" align="center">
                        <n-space vertical :size="4" style="flex: 1;">
                          <n-text strong>{{ task.task_type === 'bulk' ? `Bulk: ${task.standard_code}` : `Single: ${task.disclosure_code}` }}</n-text>
                          <n-text depth="3" style="font-size: 12px;">
                            {{ task.status === 'pending' ? 'Waiting to start...' : `Processing ${task.completed_items}/${task.total_items}` }}
                          </n-text>
                        </n-space>
                        <n-tag :type="task.status === 'running' ? 'info' : 'default'" size="small">
                          {{ task.status }}
                        </n-tag>
                      </n-space>
                      <n-progress 
                        :percentage="displayProgress[task.task_id] || task.progress" 
                        :color="'#54d944'"
                        :rail-color="'rgba(255, 255, 255, 0.1)'"
                        :height="8"
                        style="margin-top: 12px;"
                      />
                    </div>
                  </n-space>
                </n-space>
              </n-card>
            </n-gi>

            <!-- Standards Overview -->
            <n-gi>
              <n-card title="📋 Compliance Standards Overview" :bordered="false">
                <n-spin :show="loadingStats">
                  <div v-if="standardTypes.length === 0" style="padding: 24px; text-align: center;">
                    <n-text depth="3">Loading standards...</n-text>
                  </div>
                  <n-grid v-else :cols="3" :x-gap="24" :y-gap="24" responsive="screen">
                    <n-gi v-for="standard in standardTypes" :key="standard.type">
                      <div class="stat-card-circle" @click="navigateToStandard(standard.type)">
                        <n-space vertical :size="16" align="center">
                          <div class="circle-progress-wrapper">
                            <n-progress
                              type="circle"
                              :percentage="standard.completion_percentage"
                              :stroke-width="10"
                              :color="getProgressColor(standard.completion_percentage)"
                              :rail-color="'rgba(255, 255, 255, 0.1)'"
                              :style="{ width: '160px', height: '160px' }"
                            >
                              <div class="progress-content">
                                <div style="font-size: 48px; margin-bottom: 8px;">{{ standard.icon }}</div>
                                <n-text strong style="font-size: 28px; color: #54d944;">{{ standard.completion_percentage.toFixed(0) }}%</n-text>
                                <n-text depth="3" style="font-size: 12px; margin-top: 4px;">{{ standard.answered_requirements }}/{{ standard.total_requirements }}</n-text>
                              </div>
                            </n-progress>
                          </div>
                          <n-text strong style="font-size: 16px; text-align: center;">{{ standard.name }}</n-text>
                          <n-text depth="3" style="font-size: 12px; text-align: center;">{{ standard.description }}</n-text>
                        </n-space>
                      </div>
                    </n-gi>
                  </n-grid>
                </n-spin>
              </n-card>
            </n-gi>

            <n-gi>
              <n-card title="📊 Detailed Progress by Category" :bordered="false">
                <n-spin :show="loadingStats">
                  <div v-if="statistics.length === 0" style="padding: 24px; text-align: center;">
                    <n-text depth="3">Loading statistics...</n-text>
                  </div>
                  <n-grid v-else :cols="4" :x-gap="24" :y-gap="24" responsive="screen">
                    <n-gi v-for="stat in statistics" :key="stat.category_id">
                      <div class="stat-card-circle" @click="navigateToCategory(stat.category_id)">
                        <n-space vertical :size="16" align="center">
                          <div class="circle-progress-wrapper">
                            <n-progress
                              type="circle"
                              :percentage="stat.completion_percentage"
                              :stroke-width="8"
                              :color="getProgressColor(stat.completion_percentage)"
                              :rail-color="'rgba(255, 255, 255, 0.1)'"
                              :style="{ width: '140px', height: '140px' }"
                            >
                              <div class="progress-content">
                                <n-text strong style="font-size: 28px; color: #54d944;">{{ stat.completion_percentage }}%</n-text>
                                <n-text depth="3" style="font-size: 12px; margin-top: 4px;">{{ stat.answered_disclosures }}/{{ stat.total_disclosures }}</n-text>
                              </div>
                            </n-progress>
                          </div>
                          <n-text strong style="font-size: 14px; text-align: center;">{{ stat.category_name }}</n-text>
                          <n-text depth="3" style="font-size: 12px; text-align: center;">{{ stat.category_code }}</n-text>
                        </n-space>
                      </div>
                    </n-gi>
                  </n-grid>
                </n-spin>
              </n-card>
            </n-gi>
          </n-grid>
        </n-layout-content>
      </n-layout>
    </n-layout>

    <!-- Settings Modal -->
    <n-modal v-model:show="showSettingsModal" preset="card" title="⚙️ Settings" style="width: 600px;">
      <n-alert type="info" style="margin-bottom: 16px;">
        Dark theme is enabled by default for optimal visibility.
      </n-alert>
      <n-form label-placement="left" label-width="120px">
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
import { ref, h, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth.store'
import { 
  useMessage,
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NGradientText,
  NH2,
  NDropdown,
  NButton,
  NAvatar,
  NGrid,
  NGi,
  NCard,
  NSpace,
  NText,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NStatistic,
  NIcon,
  NSpin,
  NProgress,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NAlert,
  type MenuOption
} from 'naive-ui'
import { 
  HomeOutline, 
  PersonOutline, 
  LogOutOutline,
  PeopleOutline,
  SettingsOutline,
  DocumentTextOutline,
  ClipboardOutline
} from '@vicons/ionicons5'
import LanguageSelector from '../components/LanguageSelector.vue'
import api from '../services/api'

interface CategoryStatistic {
  category_id: number
  category_name: string
  category_code: string
  total_disclosures: number
  answered_disclosures: number
  completion_percentage: number
}

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
const authStore = useAuthStore()
const message = useMessage()
const { t } = useI18n()

const activeKey = ref('dashboard')
const loadingStats = ref(false)
const statistics = ref<CategoryStatistic[]>([])
const standardTypes = ref<StandardType[]>([])

// Export states
const exportingPDF = ref(false)
const exportingWord = ref(false)

interface AITask {
  task_id: string
  task_type: string
  status: string
  progress: number
  total_items: number
  completed_items: number
  disclosure_code?: string
  standard_code?: string
  created_at: string
  updated_at: string
}

const activeTasks = ref<AITask[]>([])
const displayProgress = ref<Record<string, number>>({}) // Smooth animated progress
let pollingInterval: number | null = null
let progressInterval: number | null = null

// Settings modal state
const showSettingsModal = ref(false)
const userNickname = ref(authStore.user?.username || '')
const selectedAvatar = ref(localStorage.getItem('userAvatar') || 'default')
const selectedLanguage = ref(localStorage.getItem('locale') || 'en')

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

const menuOptions = computed(() => {
  const baseMenu = [
    {
      label: t('nav.dashboard'),
      key: 'dashboard',
      icon: () => h(NIcon, null, { default: () => h(HomeOutline) })
    }
  ]
  
  // Add dynamic standard type menus
  const standardMenus = standardTypes.value.map(standard => ({
    label: `${standard.icon} ${standard.name}`,
    key: `standard-${standard.type}`,
    icon: () => h(NIcon, null, { default: () => h(ClipboardOutline) })
  }))
  
  console.log('🎯 Menu - standardTypes:', standardTypes.value.length, 'items')
  console.log('🎯 Menu - generated:', standardMenus.length, 'standard menus')
  
  const otherMenus = [
    {
      label: t('nav.documents'),
      key: 'documents',
      icon: () => h(NIcon, null, { default: () => h(DocumentTextOutline) })
    },
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
  
  return [...baseMenu, ...standardMenus, ...otherMenus]
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

const handleMenuUpdate = (key: string) => {
  if (key === 'dashboard') {
    activeKey.value = 'dashboard'
    router.push('/dashboard')
  } else if (key.startsWith('standard-')) {
    activeKey.value = key
    const standardType = key.replace('standard-', '')
    router.push(`/standards/${standardType}`)
  } else if (key === 'esrs') {
    // Legacy support - redirect to ESRS standard
    activeKey.value = 'standard-ESRS'
    router.push('/standards/ESRS')
  } else if (key === 'documents') {
    activeKey.value = 'documents'
    router.push('/documents')
  } else if (key === 'settings') {
    showSettingsModal.value = true
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
  } else {
    message.info(`Akcija: ${key}`)
  }
}

const saveSettings = async () => {
  // Theme is always dark (no toggle)
  
  // Save avatar
  localStorage.setItem('userAvatar', selectedAvatar.value)
  
  // Save and change language
  const { locale } = useI18n()
  localStorage.setItem('locale', selectedLanguage.value)
  locale.value = selectedLanguage.value
  
  showSettingsModal.value = false
  message.success('Settings saved successfully!')
  
  // Reload page to apply language changes
  window.location.reload()
}

const getAvatarEmoji = (avatarValue: string) => {
  const avatar = avatarOptions.find(a => a.value === avatarValue)
  return avatar ? avatar.label.split(' ')[0] : '👤'
}

const formatDate = (date: any) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('sl-SI', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const loadStatistics = async () => {
  loadingStats.value = true
  try {
    const response = await api.get('/esrs/dashboard-statistics')
    statistics.value = response.data.statistics
  } catch (error) {
    message.error('Failed to load statistics')
    console.error(error)
  } finally {
    loadingStats.value = false
  }
}

const loadStandardTypes = async () => {
  try {
    const response = await api.get('/standards/types')
    standardTypes.value = response.data
    console.log('📊 Loaded standard types:', response.data)
  } catch (error) {
    message.error('Failed to load standard types')
    console.error(error)
  }
}

const navigateToCategory = (categoryId: number) => {
  router.push({ path: '/esrs', query: { category: categoryId } })
}

const navigateToStandard = (standardType: string) => {
  router.push(`/standards/${standardType}`)
}

const getProgressColor = (percentage: number) => {
  if (percentage > 75) return '#54d944'
  if (percentage > 30) return '#f0a020'
  return '#999999'
}

const loadActiveTasks = async () => {
  try {
    const previousTaskCount = activeTasks.value.length
    const response = await api.get('/esrs/active-tasks')
    const newTaskCount = response.data.length
    
    // Initialize display progress for new tasks
    response.data.forEach((task: AITask) => {
      if (!(task.task_id in displayProgress.value)) {
        displayProgress.value[task.task_id] = 0
      }
    })
    
    activeTasks.value = response.data
    
    // If number of tasks decreased (task finished and removed from active list)
    if (previousTaskCount > newTaskCount) {
      console.log(`✅ Task completed (${previousTaskCount} → ${newTaskCount}) - reloading statistics`)
      await loadStatistics()
      
      // Clean up display progress for completed tasks
      const activeTaskIds = new Set(response.data.map((t: AITask) => t.task_id))
      Object.keys(displayProgress.value).forEach(taskId => {
        if (!activeTaskIds.has(taskId)) {
          delete displayProgress.value[taskId]
        }
      })
    }
  } catch (error) {
    console.error('Failed to load active tasks:', error)
  }
}

const animateProgress = () => {
  // Smoothly animate progress towards actual backend progress
  activeTasks.value.forEach(task => {
    const currentDisplay = displayProgress.value[task.task_id] || 0
    const targetProgress = task.progress
    
    if (currentDisplay < targetProgress) {
      // Increment by small amount (1-2% per tick)
      const increment = Math.min(2, targetProgress - currentDisplay)
      displayProgress.value[task.task_id] = Math.min(targetProgress, currentDisplay + increment)
    } else if (currentDisplay > targetProgress) {
      // Should not happen, but sync just in case
      displayProgress.value[task.task_id] = targetProgress
    }
  })
}

const startPolling = () => {
  // Load immediately
  loadActiveTasks()
  
  // Poll active tasks every 3 seconds
  pollingInterval = window.setInterval(() => {
    loadActiveTasks()
  }, 3000)
  
  // Animate progress smoothly every 300ms (faster updates for smooth animation)
  progressInterval = window.setInterval(() => {
    animateProgress()
  }, 300)
}

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
}

// Export functions
const exportPDF = async () => {
  exportingPDF.value = true
  try {
    const response = await api.get('/export/pdf', {
      responseType: 'blob'
    })
    
    // Create blob and download
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `ESRS_Report_${new Date().toISOString().split('T')[0]}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
    
    message.success('PDF report downloaded successfully')
  } catch (error) {
    console.error('Failed to export PDF:', error)
    message.error('Failed to export PDF report')
  } finally {
    exportingPDF.value = false
  }
}

const exportWord = async () => {
  exportingWord.value = true
  try {
    const response = await api.get('/export/word', {
      responseType: 'blob'
    })
    
    // Create blob and download
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `ESRS_Report_${new Date().toISOString().split('T')[0]}.docx`
    link.click()
    window.URL.revokeObjectURL(url)
    
    message.success('Word report downloaded successfully')
  } catch (error) {
    console.error('Failed to export Word:', error)
    message.error('Failed to export Word report')
  } finally {
    exportingWord.value = false
  }
}

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchCurrentUser()
  }
  
  // Initialize theme
  const theme = localStorage.getItem('theme')
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
  
  await Promise.all([loadStatistics(), loadStandardTypes()])
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
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

.logo {
  padding: 24px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.logo-img {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  object-fit: cover;
  box-shadow: 0 4px 12px rgba(84, 217, 68, 0.3);
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

.page-title {
  margin: 0;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card {
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.stat-card-circle {
  padding: 24px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border: 1px solid rgba(84, 217, 68, 0.2);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card-circle:hover {
  background: rgba(84, 217, 68, 0.05);
  border-color: rgba(84, 217, 68, 0.4);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(84, 217, 68, 0.2);
}

.circle-progress-wrapper {
  position: relative;
}

.progress-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.task-item {
  padding: 16px;
  background: rgba(84, 217, 68, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(84, 217, 68, 0.2);
}

/* Mobile Responsive Styles */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 12px;
  }

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  :deep(.n-h1) {
    font-size: 24px !important;
  }

  :deep(.n-grid) {
    grid-template-columns: 1fr !important;
  }

  .stat-card-circle {
    padding: 20px 16px;
  }

  :deep(.n-progress-circle) {
    width: 80px !important;
    height: 80px !important;
  }

  .progress-content h2 {
    font-size: 28px !important;
  }

  .progress-content span {
    font-size: 12px !important;
  }

  :deep(.n-card-header) {
    font-size: 16px !important;
  }

  :deep(.n-card__content) {
    padding: 12px !important;
  }

  :deep(.n-button) {
    font-size: 13px !important;
    padding: 8px 16px !important;
  }

  .task-item {
    padding: 12px;
  }
}

@media (max-width: 480px) {
  .dashboard-container {
    padding: 8px;
  }

  :deep(.n-h1) {
    font-size: 20px !important;
  }

  .stat-card-circle {
    padding: 16px 12px;
  }

  :deep(.n-progress-circle) {
    width: 70px !important;
    height: 70px !important;
  }

  .progress-content h2 {
    font-size: 24px !important;
  }

  .progress-content span {
    font-size: 11px !important;
  }

  :deep(.n-card-header) {
    font-size: 14px !important;
  }

  :deep(.n-button) {
    font-size: 12px !important;
    padding: 6px 12px !important;
  }
}
</style>
