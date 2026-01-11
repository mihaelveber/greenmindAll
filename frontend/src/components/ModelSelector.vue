<template>
  <div class="model-selector">
    <n-space vertical :size="12">
      <n-text strong>{{ $t('ai.selectModel') }}</n-text>
      
      <n-select
        v-model:value="selectedModel"
        :options="modelOptions"
        :loading="loading"
        @update:value="handleModelChange"
        :render-label="renderLabel"
        :render-tag="renderTag"
        size="large"
      >
        <template #empty>
          <n-empty :description="$t('ai.noModelsAvailable')" />
        </template>
      </n-select>
      
      <n-collapse v-if="selectedModelInfo" arrow-placement="right">
        <n-collapse-item :title="$t('ai.modelDetails')" name="details">
          <n-space vertical :size="8">
            <n-text>
              <n-icon :component="CloudOutline" />
              <strong>{{ $t('ai.provider') }}:</strong> {{ providerName(selectedModelInfo.provider) }}
            </n-text>
            <n-text>
              <n-icon :component="SpeedometerOutline" />
              <strong>{{ $t('ai.contextWindow') }}:</strong> {{ formatNumber(selectedModelInfo.context_window) }} tokens
            </n-text>
            <n-text>
              <n-icon :component="CashOutline" />
              <strong>{{ $t('ai.costPer1M') }}:</strong> 
              ${{ selectedModelInfo.cost_per_1m_input }}/${{ selectedModelInfo.cost_per_1m_output }}
            </n-text>
            <n-text type="info">
              <n-icon :component="InformationCircleOutline" />
              {{ selectedModelInfo.description }}
            </n-text>
          </n-space>
        </n-collapse-item>
      </n-collapse>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NSelect, NSpace, NText, NCollapse, NCollapseItem, NEmpty, NIcon, NTag, useMessage } from 'naive-ui'
import { CloudOutline, SpeedometerOutline, CashOutline, InformationCircleOutline, StarOutline } from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const { t } = useI18n()
const message = useMessage()

interface ModelInfo {
  model: string
  provider: string
  name: string
  context_window: number
  max_output: number
  supports_streaming: boolean
  supports_json: boolean
  cost_per_1m_input: number
  cost_per_1m_output: number
  description: string
  is_current?: boolean
}

const loading = ref(false)
const models = ref<ModelInfo[]>([])
const selectedModel = ref<string>('')
const selectedModelInfo = computed(() => models.value.find(m => m.model === selectedModel.value))

const modelOptions = computed(() => 
  models.value.map(model => ({
    label: model.name,
    value: model.model,
    provider: model.provider,
    isCurrent: model.is_current,
    description: model.description,
    contextWindow: model.context_window,
    cost: `$${model.cost_per_1m_input}/$${model.cost_per_1m_output}`
  }))
)

const providerName = (provider: string) => {
  const names: Record<string, string> = {
    'openai': 'OpenAI',
    'anthropic': 'Anthropic',
    'google': 'Google'
  }
  return names[provider] || provider
}

const formatNumber = (num: number) => {
  if (num >= 1_000_000) {
    return (num / 1_000_000).toFixed(1) + 'M'
  } else if (num >= 1_000) {
    return (num / 1_000).toFixed(0) + 'K'
  }
  return num.toString()
}

const renderLabel = (option: any) => {
  return h('div', { style: 'display: flex; align-items: center; justify-content: space-between; width: 100%;' }, [
    h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
      h('span', { style: 'font-weight: 500;' }, option.label),
      option.isCurrent && h(NTag, { 
        type: 'success', 
        size: 'small',
        round: true
      }, { default: () => t('ai.current') })
    ]),
    h('span', { style: 'font-size: 12px; color: var(--n-text-color-3);' }, option.cost)
  ])
}

const renderTag = ({ option }: any) => {
  return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
    h('span', option.label),
    option.isCurrent && h(NIcon, { component: StarOutline, color: '#f59e0b', size: 16 })
  ])
}

const loadModels = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('authToken')
    const response = await axios.get('/api/ai/models', {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    models.value = response.data
    
    // Set current model as selected
    const currentModel = models.value.find(m => m.is_current)
    if (currentModel) {
      selectedModel.value = currentModel.model
    } else if (models.value.length > 0) {
      selectedModel.value = models.value[0].model
    }
  } catch (error: any) {
    console.error('Failed to load models:', error)
    message.error(t('ai.failedToLoadModels'))
  } finally {
    loading.value = false
  }
}

const handleModelChange = async (value: string) => {
  try {
    const token = localStorage.getItem('authToken')
    await axios.put(
      '/api/ai/user/preferred-model',
      null,
      {
        params: { model: value },
        headers: { Authorization: `Bearer ${token}` }
      }
    )
    
    // Update is_current flag
    models.value.forEach(m => {
      m.is_current = (m.model === value)
    })
    
    message.success(t('ai.modelUpdated'))
  } catch (error: any) {
    console.error('Failed to update model:', error)
    message.error(t('ai.failedToUpdateModel'))
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.model-selector {
  width: 100%;
}
</style>
