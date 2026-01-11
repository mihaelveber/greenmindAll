<template>
  <div class="version-node-container">
    <div 
      class="version-node" 
      :class="{
        'selected': version.id === selectedVersionId,
        'manual': version.created_by_user,
        'ai': !version.created_by_user
      }"
    >
      <!-- Left: Version badge -->
      <div class="version-badge">
        <n-tag 
          :type="version.is_selected ? 'success' : 'default'" 
          size="small"
          :bordered="false"
        >
          v{{ version.version_number }}
        </n-tag>
      </div>
      
      <!-- Center: Content -->
      <div class="version-content">
        <div class="version-header">
          <n-space align="center" :size="8">
            <n-icon 
              :component="version.created_by_user ? PersonOutline : SparklesOutline" 
              :size="16"
              :color="version.created_by_user ? '#8B5CF6' : '#3B82F6'"
            />
            <n-text strong>{{ getChangeTypeLabel(version.change_type) }}</n-text>
            <n-text depth="3" style="font-size: 12px;">
              {{ formatTime(version.created_at) }}
            </n-text>
          </n-space>
        </div>
        
        <!-- User Attribution -->
        <div class="version-attribution" style="margin-top: 4px;">
          <n-text depth="3" style="font-size: 11px;">
            <span v-if="version.created_by_user">
              👤 Created by: <strong>{{ version.created_by_email || 'Unknown user' }}</strong>
            </span>
            <span v-else>
              🤖 AI Generated
            </span>
          </n-text>
        </div>
        
        <n-text v-if="version.change_description" class="version-description">
          {{ version.change_description }}
        </n-text>
        
        <!-- Show content preview -->
        <div class="content-preview">
          <ContentPreview :version="version" />
        </div>
      </div>
      
      <!-- Right: Actions -->
      <div class="version-actions">
        <n-space>
          <n-button 
            v-if="!version.is_selected"
            size="small" 
            type="primary"
            @click="$emit('select', version.id)"
          >
            <template #icon>
              <n-icon :component="CheckmarkCircleOutline" />
            </template>
            Use This
          </n-button>
          <n-tag v-else type="success" size="small" :bordered="false">
            <template #icon>
              <n-icon :component="CheckmarkCircleOutline" />
            </template>
            Active
          </n-tag>
          
          <n-button size="small" quaternary @click="$emit('view', version)">
            <template #icon>
              <n-icon :component="EyeOutline" />
            </template>
          </n-button>
          
          <n-button 
            v-if="!version.is_selected"
            size="small" 
            type="error"
            quaternary
            @click="$emit('delete', version.id)"
          >
            <template #icon>
              <n-icon :component="TrashOutline" />
            </template>
          </n-button>
        </n-space>
      </div>
    </div>
    
    <!-- Children (recursive) -->
    <div v-if="children.length > 0" class="version-children">
      <div class="branch-line"></div>
      <div class="children-container">
        <VersionNode
          v-for="child in children"
          :key="child.id"
          :version="child"
          :selected-version-id="selectedVersionId"
          :all-versions="allVersions"
          @select="$emit('select', $event)"
          @view="$emit('view', $event)"
          @delete="$emit('delete', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NTag, NButton, NSpace, NIcon, NText } from 'naive-ui'
import { 
  PersonOutline, 
  SparklesOutline, 
  CheckmarkCircleOutline, 
  EyeOutline,
  TrashOutline
} from '@vicons/ionicons5'
import ContentPreview from './ContentPreview.vue'

interface Version {
  id: string
  version_number: number
  change_type: string
  change_description: string
  content: any
  is_selected: boolean
  created_at: string
  created_by_user: boolean
  created_by_email?: string
  parent_version_id: string | null
  conversation_id: string | null
}

interface Props {
  version: Version
  selectedVersionId: string | null
  allVersions: Version[]
}

const props = defineProps<Props>()

defineEmits<{
  (e: 'select', versionId: string): void
  (e: 'view', version: Version): void
  (e: 'delete', versionId: string): void
}>()

const children = computed(() => {
  return props.allVersions.filter(v => v.parent_version_id === props.version.id)
})

const getChildrenOf = (parentId: string): Version[] => {
  return props.allVersions.filter(c => c.parent_version_id === parentId)
}

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
</script>

<style scoped>
.version-node-container {
  position: relative;
}

.version-node {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid rgba(84, 217, 68, 0.2);
  background: rgba(0, 0, 0, 0.3);
  transition: all 0.2s ease;
}

.version-node:hover {
  border-color: rgba(84, 217, 68, 0.5);
  background: rgba(0, 0, 0, 0.4);
  transform: translateX(4px);
}

.version-node.selected {
  border-color: rgba(84, 217, 68, 0.8);
  background: rgba(84, 217, 68, 0.1);
  box-shadow: 0 0 20px rgba(84, 217, 68, 0.3);
}

.version-node.manual {
  border-left: 4px solid #8B5CF6;
}

.version-node.ai {
  border-left: 4px solid #3B82F6;
}

.version-badge {
  flex-shrink: 0;
}

.version-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.version-header {
  display: flex;
  align-items: center;
}

.version-description {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  font-style: italic;
}

.content-preview {
  margin-top: 4px;
}

.version-actions {
  flex-shrink: 0;
}

.version-children {
  margin-left: 32px;
  margin-top: 12px;
  position: relative;
}

.branch-line {
  position: absolute;
  left: -16px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(
    to bottom,
    rgba(84, 217, 68, 0.5) 0%,
    rgba(84, 217, 68, 0.2) 100%
  );
}

.children-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Connector dot */
.version-children::before {
  content: '';
  position: absolute;
  left: -17px;
  top: 20px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(84, 217, 68, 0.8);
  box-shadow: 0 0 8px rgba(84, 217, 68, 0.5);
}
</style>
