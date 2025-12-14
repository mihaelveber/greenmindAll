<template>
  <div class="version-comparison-wrapper">
    <n-spin :show="loading">
      <!-- Header: Version selectors -->
      <div class="comparison-header">
        <n-space justify="space-between" align="center">
          <div class="version-selector">
            <n-text strong>Compare:</n-text>
            <n-select
              v-model:value="selectedVersion1"
              :options="versionOptions"
              placeholder="Select version 1"
              style="width: 200px; margin-left: 12px;"
            />
          </div>
          
          <n-icon :component="ArrowForwardOutline" size="24" />
          
          <div class="version-selector">
            <n-text strong>With:</n-text>
            <n-select
              v-model:value="selectedVersion2"
              :options="versionOptions"
              placeholder="Select version 2"
              style="width: 200px; margin-left: 12px;"
            />
          </div>
        </n-space>
      </div>
      
      <n-divider />
      
      <!-- Comparison content -->
      <div v-if="version1 && version2" class="comparison-content">
        <div class="comparison-grid">
          <!-- Left: Version 1 -->
          <div class="version-panel version-1">
            <div class="panel-header">
              <n-tag type="info" size="small" :bordered="false">
                v{{ version1.version_number }}
              </n-tag>
              <n-text depth="3" style="font-size: 12px; margin-left: 8px;">
                {{ formatTime(version1.created_at) }}
              </n-text>
            </div>
            <div class="panel-content">
              <VersionContent :version="version1" />
            </div>
          </div>
          
          <!-- Right: Version 2 -->
          <div class="version-panel version-2">
            <div class="panel-header">
              <n-tag type="success" size="small" :bordered="false">
                v{{ version2.version_number }}
              </n-tag>
              <n-text depth="3" style="font-size: 12px; margin-left: 8px;">
                {{ formatTime(version2.created_at) }}
              </n-text>
            </div>
            <div class="panel-content">
              <VersionContent :version="version2" />
            </div>
          </div>
        </div>
        
        <!-- Diff summary -->
        <n-card title="📊 Changes Summary" size="small" style="margin-top: 16px;">
          <n-space vertical :size="8">
            <n-text v-if="version2.change_description">
              <strong>What changed:</strong> {{ version2.change_description }}
            </n-text>
            <n-text depth="3">
              <strong>Change type:</strong> {{ getChangeTypeLabel(version2.change_type) }}
            </n-text>
            <n-text depth="3">
              <strong>Modified by:</strong> {{ version2.created_by_user ? '👤 Manual Edit' : '🤖 AI' }}
            </n-text>
          </n-space>
        </n-card>
      </div>
      
      <!-- Empty state -->
      <div v-else class="empty-state">
        <n-empty description="Select two versions to compare">
          <template #icon>
            <n-icon :component="GitCompareOutline" size="48" />
          </template>
        </n-empty>
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { NSpin, NEmpty, NIcon, NSpace, NText, NSelect, NDivider, NCard, NTag } from 'naive-ui'
import { ArrowForwardOutline, GitCompareOutline } from '@vicons/ionicons5'
import VersionContent from './VersionContent.vue'

interface Version {
  id: string
  version_number: number
  change_type: string
  change_description: string
  content: any
  is_selected: boolean
  created_at: string
  created_by_user: boolean
  parent_version_id: string | null
  conversation_id: string | null
}

interface Props {
  versions: Version[]
}

const props = defineProps<Props>()

const loading = ref(false)
const selectedVersion1 = ref<string | null>(null)
const selectedVersion2 = ref<string | null>(null)

const versionOptions = computed(() => {
  return props.versions.map(v => ({
    label: `v${v.version_number} - ${v.change_type} (${formatTime(v.created_at)})`,
    value: v.id
  }))
})

const version1 = computed(() => {
  if (!selectedVersion1.value) return null
  return props.versions.find(v => v.id === selectedVersion1.value) || null
})

const version2 = computed(() => {
  if (!selectedVersion2.value) return null
  return props.versions.find(v => v.id === selectedVersion2.value) || null
})

const getChangeTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    'INITIAL': 'Initial Version',
    'AI_REFINEMENT': 'AI Refined',
    'MANUAL_EDIT': 'Manually Edited'
  }
  return labels[type] || type
}

const formatTime = (isoDate: string): string => {
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}d ago`
  
  return date.toLocaleDateString()
}

// Auto-select first two versions if available
watch(() => props.versions, (newVersions) => {
  if (newVersions.length >= 2 && !selectedVersion1.value && !selectedVersion2.value) {
    selectedVersion1.value = newVersions[1].id // Older version
    selectedVersion2.value = newVersions[0].id // Newer version
  }
}, { immediate: true })
</script>

<style scoped>
.version-comparison-wrapper {
  padding: 16px;
  min-height: 400px;
}

.comparison-header {
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.version-selector {
  display: flex;
  align-items: center;
}

.comparison-content {
  margin-top: 16px;
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.version-panel {
  border-radius: 8px;
  overflow: hidden;
}

.version-1 {
  border: 2px solid rgba(59, 130, 246, 0.5);
}

.version-2 {
  border: 2px solid rgba(34, 197, 94, 0.5);
}

.panel-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
}

.version-1 .panel-header {
  background: rgba(59, 130, 246, 0.1);
  border-bottom: 2px solid rgba(59, 130, 246, 0.3);
}

.version-2 .panel-header {
  background: rgba(34, 197, 94, 0.1);
  border-bottom: 2px solid rgba(34, 197, 94, 0.3);
}

.panel-content {
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  min-height: 300px;
  max-height: 500px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 64px;
}

@media (max-width: 768px) {
  .comparison-grid {
    grid-template-columns: 1fr;
  }
}
</style>
