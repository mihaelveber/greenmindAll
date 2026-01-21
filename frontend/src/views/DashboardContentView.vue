<template>
  <div>
    <!-- Export Buttons Row -->
    <n-space :size="12" style="margin-bottom: 24px;">
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
                    <n-text strong>{{
                      task.task_type === 'bulk' ? `Bulk: ${task.standard_code}` :
                      task.task_type === 'rag_processing' ? `📄 ${task.document_name || 'Document Processing'}` :
                      `Single: ${task.disclosure_code}`
                    }}</n-text>
                    <n-text depth="3" style="font-size: 12px;">
                      {{ task.status === 'pending' ? 'Waiting to start...' :
                         task.task_type === 'rag_processing' ? 'Processing document...' :
                         `Processing ${task.completed_items}/${task.total_items}` }}
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

      <!-- Standards Overview - Full Width -->
      <n-gi :span="24">
        <n-card :bordered="false">
          <template #header>
            <div>
              <h4 class="card-title">Compliance Standards Overview</h4>
              <p class="card-category">Track your progress across all standards</p>
            </div>
          </template>
          <n-spin :show="loadingStats">
            <div v-if="standardTypes.length === 0" style="padding: 24px; text-align: center;">
              <n-text depth="3">Loading standards...</n-text>
            </div>
            <div v-else style="display: flex; gap: 24px; flex-wrap: wrap; justify-content: center;">
              <div v-for="standard in standardTypes" :key="standard.type"
                   @click="navigateToStandard(standard.type)"
                   style="cursor: pointer; flex: 0 0 auto; text-align: center; padding: 15px;">
                <n-progress
                  type="circle"
                  :percentage="standard.completion_percentage"
                  :stroke-width="8"
                  :color="'#41B883'"
                  :rail-color="'rgba(0, 0, 0, 0.1)'"
                  :style="{ width: '140px', height: '140px', margin: '0 auto' }"
                >
                  <div style="text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <div style="font-size: 32px; font-weight: 300; color: #333; line-height: 1;">{{ standard.completion_percentage.toFixed(0) }}%</div>
                    <div style="font-size: 12px; color: #9A9A9A; margin-top: 6px; line-height: 1;">{{ standard.answered_requirements }}/{{ standard.total_requirements }}</div>
                  </div>
                </n-progress>
                <div style="margin-top: 16px;">
                  <div style="font-size: 14px; font-weight: 600; color: #333;">{{ standard.name }}</div>
                  <div style="font-size: 12px; color: #9A9A9A; margin-top: 4px;">{{ standard.description }}</div>
                </div>
              </div>
            </div>
          </n-spin>
          <template #footer>
            <hr />
            <div class="stats">
              <i class="ti-reload"></i> Updated just now
            </div>
          </template>
        </n-card>
      </n-gi>

      <!-- Individual cards for each category - Full Width Row -->
      <n-gi :span="24">
        <n-grid :cols="4" :x-gap="24">
          <n-gi v-for="stat in statistics" :key="stat.category_id">
            <n-card :bordered="false" style="height: 100%;">
              <template #header>
                <div>
                  <h4 class="card-title">{{ stat.category_name }}</h4>
                  <p class="card-category">{{ stat.category_code }}</p>
                </div>
              </template>
              <div @click="navigateToCategory(stat.category_id)" style="cursor: pointer; text-align: center; padding: 20px 0;">
                <n-progress
                  type="circle"
                  :percentage="stat.completion_percentage"
                  :stroke-width="8"
                  :color="'#41B883'"
                  :rail-color="'rgba(0, 0, 0, 0.1)'"
                  :style="{ width: '120px', height: '120px', margin: '0 auto', display: 'block' }"
                >
                  <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <div style="font-size: 32px; font-weight: 300; color: #333; line-height: 1;">{{ stat.completion_percentage }}%</div>
                    <div style="font-size: 12px; color: #9A9A9A; margin-top: 8px; line-height: 1;">{{ stat.answered_disclosures }}/{{ stat.total_disclosures }}</div>
                  </div>
                </n-progress>
              </div>
              <template #footer>
                <hr />
                <div class="stats">
                  <i class="ti-reload"></i> Click to view details
                </div>
              </template>
            </n-card>
          </n-gi>
        </n-grid>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, NGrid, NGi, NCard, NSpace, NText, NTag, NSpin, NProgress, NButton, NIcon } from 'naive-ui'
import { DocumentTextOutline } from '@vicons/ionicons5'
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

interface AITask {
  task_id: string
  task_type: string
  status: string
  progress: number
  total_items: number
  completed_items: number
  disclosure_code?: string
  standard_code?: string
  document_name?: string
  created_at: string
  updated_at: string
}

const router = useRouter()
const message = useMessage()

const loadingStats = ref(false)
const statistics = ref<CategoryStatistic[]>([])
const standardTypes = ref<StandardType[]>([])
const exportingPDF = ref(false)
const exportingWord = ref(false)

const activeTasks = ref<AITask[]>([])
const displayProgress = ref<Record<string, number>>({})
let pollingInterval: number | null = null
let progressInterval: number | null = null

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
      await loadStatistics()
      await loadStandardTypes()

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
  activeTasks.value.forEach(task => {
    const currentDisplay = displayProgress.value[task.task_id] || 0
    const targetProgress = task.progress

    if (currentDisplay < targetProgress) {
      const increment = Math.min(2, targetProgress - currentDisplay)
      displayProgress.value[task.task_id] = Math.min(targetProgress, currentDisplay + increment)
    } else if (currentDisplay > targetProgress) {
      displayProgress.value[task.task_id] = targetProgress
    }
  })
}

const startPolling = () => {
  loadActiveTasks()

  pollingInterval = window.setInterval(() => {
    loadActiveTasks()
  }, 3000)

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
  await Promise.all([loadStatistics(), loadStandardTypes()])
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
.task-item {
  padding: 16px;
  background: rgba(84, 217, 68, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(84, 217, 68, 0.2);
}
</style>
