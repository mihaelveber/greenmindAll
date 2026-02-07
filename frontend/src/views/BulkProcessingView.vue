<template>
  <div class="bulk-processing-container">
    <n-page-header class="page-header">
      <template #title>
        <h1>🤖 {{ t('bulk.title') }}</h1>
      </template>
      <template #subtitle>
        {{ t('bulk.subtitle') }}
      </template>
    </n-page-header>

    <!-- Standards Selection -->
    <n-card :bordered="false" style="margin-bottom: 24px;">
      <template #header>
        <n-text strong style="font-size: 16px;">{{ t('bulk.selectStandards') }}</n-text>
      </template>

      <n-spin :show="loadingStandards">
        <n-checkbox-group v-model:value="selectedStandards">
          <n-space vertical :size="12">
            <n-checkbox
              v-for="standard in availableStandards"
              :key="standard.type"
              :value="standard.type"
              :label="`${standard.name} (${standard.total_requirements} requirements, ${standard.answered_requirements} answered)`"
            />
          </n-space>
        </n-checkbox-group>
      </n-spin>

      <n-divider />

      <n-space align="center" :size="12" style="margin-bottom: 16px;">
        <n-text strong>{{ t('bulk.temperature') }}</n-text>
        <n-slider v-model:value="bulkTemperature" :min="0" :max="1" :step="0.1" style="width: 220px;" />
        <n-text>{{ bulkTemperature.toFixed(1) }}</n-text>
        <n-tag
          :type="bulkTemperature <= 0.3 ? 'info' : bulkTemperature <= 0.7 ? 'warning' : 'error'"
          size="small"
        >
          {{ bulkTemperature <= 0.3 ? t('bulk.tempFactual') : bulkTemperature <= 0.7 ? t('bulk.tempBalanced') : t('bulk.tempCreative') }}
        </n-tag>
      </n-space>

      <n-space justify="space-between" align="center">
        <n-space align="center">
          <n-button
            type="primary"
            size="large"
            :disabled="selectedStandards.length === 0 || processing"
            :loading="processing"
            @click="startBulkProcessing"
          >
            <template #icon>
              <n-icon :component="PlayOutline" />
            </template>
            {{ t('bulk.start') }}
          </n-button>
          <n-button
            v-if="processing"
            type="error"
            size="large"
            @click="stopBulkProcessing"
          >
            <template #icon>
              <n-icon :component="StopOutline" />
            </template>
            {{ t('bulk.stop') }}
          </n-button>
        </n-space>
        <n-space align="center">
          <n-checkbox v-model:checked="selectAll" @update:checked="handleSelectAll">
            {{ t('bulk.selectAllOnce') }}
          </n-checkbox>
        </n-space>
      </n-space>
    </n-card>

    <!-- Progress Overview -->
    <n-card v-if="processing || taskHistory.length > 0" :bordered="false" style="margin-bottom: 24px;">
      <template #header>
        <n-text strong style="font-size: 16px;">{{ t('bulk.progressTitle') }}</n-text>
      </template>

      <n-space vertical :size="24">
        <!-- Overall Progress -->
        <div>
          <n-space justify="space-between" style="margin-bottom: 8px;">
            <n-text strong>{{ t('bulk.overallProgress') }}</n-text>
            <n-text>{{ completedTasks }} / {{ totalTasks }} {{ t('bulk.standardsCompleted') }}</n-text>
          </n-space>
          <n-progress
            type="line"
            :percentage="overallProgress"
            :color="'#41B883'"
            :height="24"
            :indicator-placement="'inside'"
          />
        </div>

        <!-- Individual Standard Progress -->
        <div v-for="task in activeTasks" :key="task.task_id" class="task-progress">
          <n-space justify="space-between" align="center" style="margin-bottom: 8px;">
            <n-space align="center">
              <n-text strong>{{ task.standard_code }}</n-text>
              <n-tag :type="getTaskStatusType(task.status)" size="small">
                {{ task.status }}
              </n-tag>
            </n-space>
            <n-text depth="3">{{ task.completed_items }} / {{ task.total_items }} {{ t('bulk.requirements') }}</n-text>
          </n-space>
          <n-space vertical :size="4" style="margin-bottom: 8px;">
            <n-text v-if="task.current_step" depth="3">{{ t('bulk.currentStep') }}: {{ task.current_step }}</n-text>
            <n-text depth="3">{{ t('bulk.eta') }}: {{ formatTaskEta(task) }}</n-text>
            <n-text v-if="task.estimated_cost_usd !== null && task.estimated_cost_usd !== undefined" depth="3">
              {{ t('bulk.costSoFar') }}: ${{ task.estimated_cost_usd.toFixed(4) }}
            </n-text>
          </n-space>
          <n-progress
            :percentage="task.progress"
            :color="'#41B883'"
            :height="16"
          />
        </div>
      </n-space>
    </n-card>

    <!-- Task History -->
    <n-card v-if="taskHistory.length > 0" :bordered="false">
      <template #header>
        <n-text strong style="font-size: 16px;">{{ t('bulk.historyTitle') }}</n-text>
      </template>

      <n-data-table
        :columns="historyColumns"
        :data="taskHistory"
        :pagination="{ pageSize: 10 }"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h, watch } from 'vue'
import {
  useMessage,
  NCard,
  NPageHeader,
  NText,
  NButton,
  NSpace,
  NCheckbox,
  NCheckboxGroup,
  NDivider,
  NProgress,
  NTag,
  NSpin,
  NSlider,
  NDataTable,
  NIcon,
  type DataTableColumns
} from 'naive-ui'
import { PlayOutline, StopOutline, CheckmarkCircle, CloseCircle } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import api from '../services/api'

const message = useMessage()
const { locale, t } = useI18n()

interface Standard {
  type: string
  name: string
  description: string
  total_requirements: number
  answered_requirements: number
  completion_percentage: number
}

interface AITask {
  task_id: string
  task_type: string
  standard_code: string
  status: string
  progress: number
  completed_items: number
  total_items: number
  current_step?: string | null
  estimated_cost_usd?: number | null
  total_tokens?: number | null
  created_at: string
}

interface TaskHistoryItem {
  standard_code: string
  status: string
  completed_at: string
  total_items: number
  success: boolean
}

const loadingStandards = ref(false)
const availableStandards = ref<Standard[]>([])
const selectedStandards = ref<string[]>([])
const selectAll = ref(false)
const bulkTemperature = ref(0.2)
const processing = ref(false)
const activeTasks = ref<AITask[]>([])
const taskHistory = ref<TaskHistoryItem[]>([])
let pollingInterval: number | null = null

const totalTasks = computed(() => selectedStandards.value.length)
const completedTasks = computed(() => taskHistory.value.filter(t => t.success).length)
const overallProgress = computed(() => {
  if (totalTasks.value === 0) return 0
  return Math.round((completedTasks.value / totalTasks.value) * 100)
})

const historyColumns: DataTableColumns<TaskHistoryItem> = [
  {
    title: t('bulk.historyStandard'),
    key: 'standard_code',
    width: 150
  },
  {
    title: t('bulk.historyStatus'),
    key: 'status',
    width: 120,
    render: (row) => {
      return h(NTag, {
        type: row.success ? 'success' : 'error',
        size: 'small'
      }, {
        default: () => row.success ? t('bulk.historyCompleted') : t('bulk.historyFailed')
      })
    }
  },
  {
    title: t('bulk.historyRequirementsProcessed'),
    key: 'total_items',
    width: 180
  },
  {
    title: t('bulk.historyCompletedAt'),
    key: 'completed_at',
    render: (row) => new Date(row.completed_at).toLocaleString()
  }
]

const loadStandards = async () => {
  loadingStandards.value = true
  try {
    const response = await api.get('/standards/types')
    availableStandards.value = response.data
  } catch (error: any) {
    message.error(t('bulk.errors.loadStandards'))
    console.error(error)
  } finally {
    loadingStandards.value = false
  }
}

const handleSelectAll = (value: boolean) => {
  if (value) {
    selectedStandards.value = availableStandards.value.map(s => s.type)
  } else {
    selectedStandards.value = []
  }
}

watch(selectedStandards, (newValue) => {
  if (availableStandards.value.length === 0) return
  selectAll.value = newValue.length === availableStandards.value.length
})

const formatTaskEta = (task: AITask) => {
  if (!task.created_at || !task.progress || task.progress <= 0) return 'Estimating...'
  const start = new Date(task.created_at).getTime()
  const now = Date.now()
  const elapsedMs = Math.max(now - start, 0)
  const totalMs = Math.round(elapsedMs / (task.progress / 100))
  const remainingMs = Math.max(totalMs - elapsedMs, 0)
  const seconds = Math.round(remainingMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (minutes <= 0) return `${secs}s`
  return `${minutes}m ${secs}s`
}

const hasProcessingDocuments = async () => {
  try {
    const response = await api.get('/documents/list')
    const docs = response.data || []
    return docs.some((doc: any) => ['pending', 'processing'].includes(doc.rag_processing_status))
  } catch (error) {
    return false
  }
}

const startBulkProcessing = async () => {
  if (selectedStandards.value.length === 0) {
    message.warning(t('bulk.errors.selectAtLeastOne'))
    return
  }

  const processingDocs = await hasProcessingDocuments()
  if (processingDocs) {
    message.warning(t('bulk.errors.docsProcessing'))
    return
  }

  processing.value = true
  taskHistory.value = []

  try {
    // Get all ESRS standards for the selected types
    for (const standardType of selectedStandards.value) {
      // For ESRS type, we need to get all individual ESRS standards
      if (standardType === 'ESRS') {
        console.log('Fetching ESRS standards...')
        const response = await api.get('/esrs/standards')
        console.log('ESRS standards response:', response.data)

        // All standards from /esrs/standards are ESRS standards
        const esrsStandards = response.data

        if (esrsStandards.length === 0) {
            message.warning(t('bulk.errors.noEsrsStandards'))
          continue
        }

        console.log(`Found ${esrsStandards.length} ESRS standards`)

        // Start processing for each ESRS standard
        for (const standard of esrsStandards) {
          console.log(`Starting bulk processing for standard ${standard.code} (ID: ${standard.id})`)
          try {
            await api.post(`/esrs/bulk-ai-answer/${standard.id}`, {
              ai_temperature: bulkTemperature.value,
              model_id: 'gpt-4o',
              language: locale.value
            })
            message.success(t('bulk.startedProcessing', { code: standard.code }))
          } catch (err: any) {
            console.error(`Failed to start processing for ${standard.code}:`, err)
            message.error(t('bulk.errors.failedToStart', { code: standard.code, reason: err.response?.data?.message || err.message }))
          }
        }
      } else {
        // For other standard types, get the standards of that type
        message.warning(t('bulk.errors.notImplemented', { type: standardType }))
      }
    }

    // Start polling for progress
    if (processing.value) {
      startPolling()
    }
  } catch (error: any) {
    message.error(t('bulk.errors.startFailed', { reason: error.response?.data?.message || error.message }))
    console.error('Bulk processing error:', error)
    processing.value = false
  }
}

const stopBulkProcessing = () => {
  processing.value = false
  stopPolling()
  message.info(t('bulk.stopped'))
}

const loadActiveTasks = async () => {
  try {
    const response = await api.get('/esrs/active-tasks')
    const previousTaskCount = activeTasks.value.length
    activeTasks.value = response.data

    // If tasks decreased, some completed
    if (previousTaskCount > response.data.length) {
      // Find completed tasks and add to history
      const activeTaskIds = new Set(response.data.map((t: AITask) => t.task_id))

      // Check which standards completed
      const completedStandards = selectedStandards.value.filter(standard => {
        return !response.data.some((t: AITask) => t.standard_code === standard)
      })

      completedStandards.forEach(standard => {
        if (!taskHistory.value.some(h => h.standard_code === standard)) {
          taskHistory.value.push({
            standard_code: standard,
            status: 'completed',
            completed_at: new Date().toISOString(),
            total_items: 0,
            success: true
          })
        }
      })
    }

    // If no active tasks remaining and we were processing, we're done
    if (processing.value && activeTasks.value.length === 0) {
      processing.value = false
      stopPolling()
      message.success('Bulk processing completed!')
    }
  } catch (error) {
    console.error('Failed to load active tasks:', error)
  }
}

const startPolling = () => {
  loadActiveTasks()
  pollingInterval = window.setInterval(() => {
    loadActiveTasks()
  }, 3000)
}

const stopPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
}

const getTaskStatusType = (status: string): 'success' | 'info' | 'warning' | 'error' => {
  const typeMap: Record<string, 'success' | 'info' | 'warning' | 'error'> = {
    completed: 'success',
    running: 'info',
    pending: 'warning',
    failed: 'error'
  }
  return typeMap[status] || 'info'
}

onMounted(() => {
  loadStandards()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
@import '../assets/sass/paper/variables';

.bulk-processing-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

h1 {
  font-size: 32px;
  font-weight: 300;
  color: $font-color;
  margin: 0;
}

.task-progress {
  padding: 16px;
  background: $smoke-bg;
  border-radius: 12px;
  border: 1px solid $medium-gray;
}

// Override card styling
:deep(.n-card) {
  background: $white-background-color;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
  border-radius: 20px;
  border: none;

  .n-card-header {
    padding: 20px 24px;
    border-bottom: 1px solid $medium-gray;

    .n-card-header__main {
      font-size: 16px;
      font-weight: 600;
      color: $font-color;
    }
  }

  .n-card__content {
    padding: 20px 24px;
  }
}

// Style checkboxes
:deep(.n-checkbox) {
  .n-checkbox-box {
    border-radius: 4px;
    border-color: $medium-gray;
  }

  &.n-checkbox--checked {
    .n-checkbox-box {
      background-color: $success-color;
      border-color: $success-color;
    }
  }

  .n-checkbox__label {
    color: $font-color;
    font-size: 14px;
  }
}

// Style progress bars
:deep(.n-progress) {
  .n-progress-graph {
    .n-progress-graph-line-rail {
      background-color: $light-gray;
    }

    .n-progress-graph-line-fill {
      background-color: $success-color !important;
    }

    .n-progress-graph-circle-rail {
      stroke: $light-gray;
    }

    .n-progress-graph-circle-fill {
      stroke: $success-color;
    }
  }

  .n-progress-text {
    color: $font-color;
    font-weight: 600;
  }
}

// Style data table
:deep(.n-data-table) {
  background: transparent;

  .n-data-table-th {
    background: $smoke-bg;
    color: $font-color;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    padding: 12px 16px;
    border-bottom: 2px solid $medium-gray;
  }

  .n-data-table-td {
    padding: 12px 16px;
    border-bottom: 1px solid $medium-gray;
    color: $font-color;
  }

  .n-data-table-tr:hover {
    background: rgba(0, 0, 0, 0.02);
  }

  .n-data-table-empty {
    color: $dark-gray;
  }
}

// Style tags
:deep(.n-tag) {
  border-radius: 6px;
  font-weight: 500;

  &.n-tag--success-type {
    background-color: rgba($success-color, 0.1);
    color: $success-states-color;
    border: 1px solid rgba($success-color, 0.3);
  }

  &.n-tag--info-type {
    background-color: rgba($info-color, 0.1);
    color: $info-states-color;
    border: 1px solid rgba($info-color, 0.3);
  }

  &.n-tag--warning-type {
    background-color: rgba($warning-color, 0.1);
    color: $warning-states-color;
    border: 1px solid rgba($warning-color, 0.3);
  }

  &.n-tag--error-type {
    background-color: rgba($danger-color, 0.1);
    color: $danger-states-color;
    border: 1px solid rgba($danger-color, 0.3);
  }
}

// Style buttons
:deep(.n-button) {
  border-radius: 6px;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: 0.5px;

  &.n-button--primary-type {
    background-color: $success-color;
    border-color: $success-color;

    &:hover {
      background-color: $success-states-color;
      border-color: $success-states-color;
    }
  }

  &.n-button--error-type {
    background-color: $danger-color;
    border-color: $danger-color;

    &:hover {
      background-color: $danger-states-color;
      border-color: $danger-states-color;
    }
  }
}

// Style switch
:deep(.n-switch) {
  &.n-switch--active {
    .n-switch__rail {
      background-color: $success-color;
    }
  }

  .n-switch__rail {
    background-color: $medium-gray;
  }
}

// Style divider
:deep(.n-divider) {
  background-color: $medium-gray;
}
</style>
