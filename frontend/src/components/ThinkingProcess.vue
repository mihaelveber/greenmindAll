<template>
  <div class="thinking-process">
    <n-space vertical :size="16">
      <!-- Header with toggle -->
      <div class="thinking-header">
        <n-button
          text
          @click="expanded = !expanded"
          :style="{ display: 'flex', alignItems: 'center', gap: '8px' }"
        >
          <n-icon :component="expanded ? ChevronDownOutline : ChevronForwardOutline" />
          <n-text strong>{{ reasoningSummary ? '🧠 AI Reasoning' : $t('ai.thinkingProcess') }}</n-text>
          <n-badge 
            :value="steps.length" 
            :type="allCompleted ? 'success' : 'info'"
            :processing="!allCompleted"
          />
        </n-button>
        
        <n-text depth="3" :style="{ fontSize: '12px' }">
          {{ formatDuration(totalDuration) }}
        </n-text>
      </div>
      
      <!-- Reasoning Summary (if available) -->
      <n-collapse-transition :show="expanded && !!reasoningSummary">
        <n-card size="small" style="margin-bottom: 16px;">
          <template #header>
            <n-space align="center">
              <n-icon :component="BulbOutline" :size="20" />
              <n-text strong>AI Reasoning Summary</n-text>
            </n-space>
          </template>
          <n-text depth="2" style="white-space: pre-wrap;">{{ reasoningSummary }}</n-text>
        </n-card>
      </n-collapse-transition>
      
      <!-- Timeline -->
      <n-collapse-transition :show="expanded">
        <div class="timeline-container">
          <n-timeline>
            <n-timeline-item
              v-for="(step, index) in steps"
              :key="index"
              :type="getStepType(step.status)"
              :title="step.message"
              :time="step.timestamp ? formatTime(step.timestamp) : ''"
            >
              <template #icon>
                <n-icon :component="getStepIcon(step.step)" :size="20" />
              </template>
              
              <template #default>
                <n-space vertical :size="8">
                  <!-- Step result -->
                  <n-text v-if="step.result" depth="2">
                    {{ step.result }}
                  </n-text>
                  
                  <!-- Duration -->
                  <n-text v-if="step.duration" depth="3" :style="{ fontSize: '12px' }">
                    ⏱️ {{ formatDuration(step.duration) }}
                  </n-text>
                  
                  <!-- Details (expandable) -->
                  <n-collapse v-if="step.details" arrow-placement="right">
                    <n-collapse-item :title="$t('ai.details')" name="details">
                      <pre class="details-pre">{{ JSON.stringify(step.details, null, 2) }}</pre>
                    </n-collapse-item>
                  </n-collapse>
                  
                  <!-- Error message -->
                  <n-alert v-if="step.status === 'error' && step.error" type="error" :title="$t('ai.error')">
                    {{ step.error }}
                  </n-alert>
                </n-space>
              </template>
            </n-timeline-item>
          </n-timeline>
        </div>
      </n-collapse-transition>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  NSpace, NButton, NIcon, NText, NCollapseTransition, NTimeline, NTimelineItem, 
  NBadge, NCollapse, NCollapseItem, NAlert 
} from 'naive-ui'
import { 
  ChevronDownOutline, ChevronForwardOutline, SearchOutline, BulbOutline,
  CheckmarkCircleOutline, CloseCircleOutline, 
  TimeOutline, RefreshOutline, FlashOutline 
} from '@vicons/ionicons5'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface ThinkingStep {
  step: string
  status: 'in_progress' | 'completed' | 'error'
  message: string
  result?: string
  timestamp?: string
  duration?: number
  details?: any
  error?: string
}

interface Props {
  steps: ThinkingStep[]
  reasoningSummary?: string  // AI reasoning summary from OpenAI o1/Anthropic extended thinking
}

const props = defineProps<Props>()
const expanded = ref(true)

const allCompleted = computed(() => 
  props.steps.every(s => s.status === 'completed' || s.status === 'error')
)

const totalDuration = computed(() => 
  props.steps.reduce((sum, step) => sum + (step.duration || 0), 0)
)

const getStepType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'error': return 'error'
    case 'in_progress': return 'info'
    default: return 'default'
  }
}

const getStepIcon = (stepName: string) => {
  const iconMap: Record<string, any> = {
    'tier_check': FlashOutline,
    'tier1_hybrid': SearchOutline,
    'semantic_only': SearchOutline,
    'tier2_expansion': RefreshOutline,
    'tier2_skip': CheckmarkCircleOutline,
    'tier3_critique': BulbOutline,
    'tier3_reformulation': RefreshOutline,
    'tier3_reranking': SearchOutline,
    'tier3_regeneration': BulbOutline,
    'tier3_keep_original': CheckmarkCircleOutline,
    'tier3_skip': CheckmarkCircleOutline,
    'tier3_error': CloseCircleOutline,
    'context_building': SearchOutline
  }
  
  return iconMap[stepName] || TimeOutline
}

const formatTime = (timestamp: string) => {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  } catch {
    return timestamp
  }
}

const formatDuration = (ms: number) => {
  if (ms < 1000) {
    return `${ms}ms`
  } else {
    return `${(ms / 1000).toFixed(1)}s`
  }
}
</script>

<style scoped>
.thinking-process {
  padding: 16px;
  background: var(--n-color);
  border-radius: 8px;
  border: 1px solid var(--n-border-color);
}

.thinking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timeline-container {
  padding: 8px 0;
  max-height: 500px;
  overflow-y: auto;
}

.details-pre {
  background: var(--n-color-modal);
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 200px;
}
</style>
