<template>
  <n-card v-if="show" size="small" class="thinking-card">
    <n-space vertical :size="8">
      <!-- Header -->
      <n-space align="center">
        <n-spin size="small" />
        <n-text strong>{{ title }}</n-text>
      </n-space>

      <!-- Progress Steps -->
      <n-collapse-transition :show="showSteps">
        <n-space vertical :size="4" style="margin-left: 24px;">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="progress-step"
            :class="{ 'active': index === safeCurrentStep, 'completed': index < safeCurrentStep }"
          >
            <n-space align="center" :size="8">
              <!-- Icon -->
              <span class="step-icon">
                <span v-if="index < safeCurrentStep">✓</span>
                <n-spin v-else-if="index === safeCurrentStep" size="small" />
                <span v-else>○</span>
              </span>

              <!-- Step Text -->
              <n-text :depth="index > safeCurrentStep ? 3 : 1" :type="index === safeCurrentStep ? 'info' : undefined">
                {{ step.text }}
              </n-text>

              <!-- Result Badge -->
              <n-tag
                v-if="step.result"
                size="tiny"
                :type="step.resultType || 'default'"
              >
                {{ step.result }}
              </n-tag>
            </n-space>
          </div>
        </n-space>
      </n-collapse-transition>

      <!-- Toggle Button -->
      <n-button
        text
        size="tiny"
        @click="showSteps = !showSteps"
        style="margin-left: 24px;"
      >
        {{ showSteps ? '▼ Hide details' : '▶ Show details' }}
      </n-button>
    </n-space>
  </n-card>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { NCard, NSpace, NText, NSpin, NTag, NButton, NCollapseTransition } from 'naive-ui'

interface ProgressStep {
  text: string
  result?: string
  resultType?: 'success' | 'info' | 'warning' | 'error'
}

const props = defineProps<{
  show: boolean
  title?: string
  steps?: ProgressStep[]
  currentStep?: number
}>()

const showSteps = ref(true)

// Default currentStep to 0 if undefined
const safeCurrentStep = computed(() => props.currentStep ?? 0)

// Watch show prop to auto-expand when visible
watch(() => props.show, (newVal) => {
  if (newVal) {
    showSteps.value = true
  }
})
</script>

<style scoped>
.thinking-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  animation: slideDown 0.3s ease-out;
}

.thinking-card :deep(.n-card__content) {
  padding: 12px 16px;
}

.thinking-card :deep(.n-text) {
  color: white !important;
}

.thinking-card :deep(.n-button) {
  color: rgba(255, 255, 255, 0.8);
}

.thinking-card :deep(.n-button:hover) {
  color: white;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.progress-step {
  font-size: 13px;
  padding: 4px 0;
  transition: all 0.3s ease;
}

.progress-step.active {
  font-weight: 500;
}

.progress-step.completed {
  opacity: 0.8;
}

.step-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  font-size: 12px;
  color: white;
}

.step-icon span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
