<template>
  <div class="chart-editor-wrapper">
    <n-tabs type="line" animated>
      <!-- Data Tab -->
      <n-tab-pane name="data" tab="📊 Data">
        <n-space vertical :size="16">
          <n-alert type="info" closable>
            💡 Edit chart data directly in the table. Click cells to edit values.
          </n-alert>
          
          <n-data-table
            :columns="dataColumns"
            :data="localData"
            :pagination="false"
            :max-height="400"
            :bordered="true"
            striped
          />
          
          <n-space>
            <n-button type="primary" @click="addRow" ghost>
              + Add Row
            </n-button>
            <n-button @click="removeLastRow" :disabled="localData.length <= 1">
              - Remove Last Row
            </n-button>
          </n-space>
        </n-space>
      </n-tab-pane>
      
      <!-- Style Tab -->
      <n-tab-pane name="style" tab="🎨 Style">
        <n-space vertical :size="16">
          <n-form label-placement="left" label-width="120px">
            <n-form-item label="Chart Type">
              <n-select
                v-model:value="chartConfig.type"
                :options="chartTypeOptions"
                @update:value="handleConfigChange"
              />
            </n-form-item>
            
            <n-form-item label="Title">
              <n-input
                v-model:value="chartConfig.title"
                placeholder="Enter chart title..."
                @update:value="handleConfigChange"
              />
            </n-form-item>
            
            <n-form-item label="Show Legend">
              <n-switch
                v-model:value="chartConfig.showLegend"
                @update:value="handleConfigChange"
              />
            </n-form-item>
            
            <n-form-item label="Show Grid">
              <n-switch
                v-model:value="chartConfig.showGrid"
                @update:value="handleConfigChange"
              />
            </n-form-item>
            
            <n-form-item label="Animation">
              <n-switch
                v-model:value="chartConfig.animated"
                @update:value="handleConfigChange"
              />
            </n-form-item>
          </n-form>
        </n-space>
      </n-tab-pane>
      
      <!-- Preview Tab -->
      <n-tab-pane name="preview" tab="👁️ Preview">
        <n-space vertical :size="16">
          <n-alert type="success">
            ✨ Live preview of your chart
          </n-alert>
          
          <div class="chart-preview-container">
            <ChartRenderer
              :chart-data="previewChartData"
              :height="400"
            />
          </div>
        </n-space>
      </n-tab-pane>
    </n-tabs>
    
    <n-divider />
    
    <n-space justify="end">
      <n-button @click="handleCancel">
        Cancel
      </n-button>
      <n-button type="primary" @click="handleSave">
        💾 Save Chart
      </n-button>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, h } from 'vue'
import {
  NInput,
  NTabs,
  NTabPane,
  NSpace,
  NAlert,
  NDataTable,
  NButton,
  NForm,
  NFormItem,
  NSelect,
  NColorPicker,
  NSwitch,
  NDivider,
  NInputNumber,
  useMessage
} from 'naive-ui'
import ChartRenderer from './ChartRenderer.vue'

interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
  }>
}

interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'doughnut'
  title: string
  primaryColor: string
  showLegend: boolean
  showGrid: boolean
  animated: boolean
}

interface Props {
  chartData: any
}

interface Emits {
  (e: 'save', data: any): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const message = useMessage()

// Local state
const localData = ref<any[]>([])
const chartConfig = ref<ChartConfig>({
  type: 'bar',
  title: 'Chart Title',
  primaryColor: '#54d944',
  showLegend: true,
  showGrid: true,
  animated: true
})

// Initialize from props
const initializeData = () => {
  if (props.chartData) {
    // Parse existing chart data (ChartRenderer format)
    const { type, title, data, config } = props.chartData
    
    chartConfig.value.type = type || 'bar'
    chartConfig.value.title = title || 'Chart Title'
    chartConfig.value.showLegend = config?.show_legend ?? true
    chartConfig.value.showGrid = config?.show_grid ?? true
    chartConfig.value.animated = config?.animated ?? true
    chartConfig.value.primaryColor = config?.colors?.[0] || '#54d944'
    
    // Convert chart data to table format
    if (Array.isArray(data)) {
      const defaultColors = ['#54d944', '#ff6b6b', '#4ecdc4', '#ffd93d', '#a29bfe', '#fd79a8', '#74b9ff']
      localData.value = data.map((item: any, idx: number) => ({
        id: idx + 1,
        label: item.label || `Category ${idx + 1}`,
        value: item.value || 0,
        color: item.color || defaultColors[idx % defaultColors.length]
      }))
    } else {
      // Fallback: default data
      localData.value = [
        { id: 1, label: 'Category 1', value: 100, color: '#54d944' },
        { id: 2, label: 'Category 2', value: 200, color: '#ff6b6b' },
        { id: 3, label: 'Category 3', value: 150, color: '#4ecdc4' }
      ]
    }
  } else {
    // Default data
    localData.value = [
      { id: 1, label: 'Category 1', value: 100, color: '#54d944' },
      { id: 2, label: 'Category 2', value: 200, color: '#ff6b6b' },
      { id: 3, label: 'Category 3', value: 150, color: '#4ecdc4' }
    ]
  }
}

initializeData()

// Chart type options
const chartTypeOptions = [
  { label: '📊 Bar Chart', value: 'bar' },
  { label: '📈 Line Chart', value: 'line' },
  { label: '🥧 Pie Chart', value: 'pie' },
  { label: '🍩 Doughnut Chart', value: 'doughnut' }
]

// Data table columns with inline editing
const dataColumns = [
  {
    title: '#',
    key: 'id',
    width: 60
  },
  {
    title: 'Label',
    key: 'label',
    render: (row: any, index: number) => {
      return h(NInput, {
        value: row.label,
        onUpdateValue: (val: string) => {
          localData.value[index].label = val
        },
        placeholder: 'Enter label...'
      })
    }
  },
  {
    title: 'Value',
    key: 'value',
    width: 120,
    render: (row: any, index: number) => {
      return h(NInput, {
        value: String(row.value),
        type: 'number',
        onUpdateValue: (val: string) => {
          localData.value[index].value = parseFloat(val) || 0
        },
        placeholder: 'Enter value...'
      })
    }
  },
  {
    title: 'Color',
    key: 'color',
    width: 100,
    render: (row: any, index: number) => {
      return h(NColorPicker, {
        value: row.color || '#54d944',
        modes: ['hex'],
        onUpdateValue: (val: string) => {
          localData.value[index].color = val
        }
      })
    }
  }
]

// Preview chart data - format for ChartRenderer
const previewChartData = computed(() => {
  return {
    id: props.chartData?.id, // Preserve chart ID
    type: chartConfig.value.type,
    title: chartConfig.value.title,
    data: localData.value.map(d => ({
      label: d.label,
      value: d.value,
      color: d.color || chartConfig.value.primaryColor
    })),
    config: {
      show_legend: chartConfig.value.showLegend,
      show_grid: chartConfig.value.showGrid,
      animated: chartConfig.value.animated,
      colors: localData.value.map(d => d.color || chartConfig.value.primaryColor)
    }
  }
})

// Actions
const addRow = () => {
  const newId = Math.max(...localData.value.map(d => d.id), 0) + 1
  localData.value.push({
    id: newId,
    label: `Category ${newId}`,
    value: 0
  })
  message.success('Row added')
}

const removeLastRow = () => {
  if (localData.value.length > 1) {
    localData.value.pop()
    message.success('Row removed')
  }
}

const handleConfigChange = () => {
  // Trigger reactivity
}

const handleSave = () => {
  emit('save', previewChartData.value)
  message.success('Chart saved successfully')
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
.chart-editor-wrapper {
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  min-height: 500px;
}

:deep(.n-tabs-nav) {
  background: linear-gradient(135deg, rgba(84, 217, 68, 0.05) 0%, rgba(84, 217, 68, 0.1) 100%);
  padding: 8px;
  border-radius: 8px 8px 0 0;
}

:deep(.n-tabs-tab) {
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.n-tabs-tab:hover) {
  color: #54d944;
}

:deep(.n-tabs-tab.n-tabs-tab--active) {
  color: #54d944;
}

:deep(.n-data-table) {
  border-radius: 6px;
  overflow: hidden;
}

:deep(.n-data-table-th) {
  background: rgba(84, 217, 68, 0.15);
  font-weight: 600;
  color: #54d944;
}

:deep(.n-data-table-td) {
  transition: background 0.2s ease;
}

:deep(.n-data-table-tr:hover .n-data-table-td) {
  background: rgba(84, 217, 68, 0.05);
}

.chart-preview-container {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-height: 400px;
}

:deep(.n-form-item-label) {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

:deep(.n-color-picker-trigger) {
  border: 2px solid rgba(84, 217, 68, 0.3);
  transition: all 0.3s ease;
}

:deep(.n-color-picker-trigger:hover) {
  border-color: #54d944;
  box-shadow: 0 0 0 2px rgba(84, 217, 68, 0.2);
}

/* Animation */
.chart-editor-wrapper {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
