<template>
  <div class="content-preview-wrapper">
    <!-- TEXT preview -->
    <div v-if="version.content.text" class="text-preview">
      <n-text depth="2" style="font-size: 13px;">
        {{ truncateText(version.content.text, 150) }}
      </n-text>
    </div>
    
    <!-- CHART preview -->
    <div v-else-if="version.content.type" class="chart-preview">
      <n-space align="center" :size="8">
        <n-icon :component="BarChartOutline" :size="16" />
        <n-text depth="2" style="font-size: 13px;">
          {{ version.content.title || 'Chart' }} ({{ version.content.type }})
        </n-text>
      </n-space>
    </div>
    
    <!-- IMAGE preview -->
    <div v-else-if="version.content.image_base64 || version.content.url" class="image-preview">
      <n-space align="center" :size="8">
        <n-icon :component="ImageOutline" :size="16" />
        <n-text depth="2" style="font-size: 13px;">
          Image: {{ truncateText(version.content.prompt || 'Generated image', 80) }}
        </n-text>
      </n-space>
    </div>
    
    <!-- TABLE preview -->
    <div v-else-if="version.content.headers" class="table-preview">
      <n-space align="center" :size="8">
        <n-icon :component="GridOutline" :size="16" />
        <n-text depth="2" style="font-size: 13px;">
          Table: {{ version.content.title || 'Data Table' }} 
          ({{ version.content.headers?.length }} cols × {{ version.content.rows?.length }} rows)
        </n-text>
      </n-space>
    </div>
    
    <!-- Fallback -->
    <div v-else class="unknown-preview">
      <n-text depth="3" style="font-size: 12px;">
        Content available
      </n-text>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NText, NSpace, NIcon } from 'naive-ui'
import { BarChartOutline, ImageOutline, GridOutline } from '@vicons/ionicons5'

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
  version: Version
}

defineProps<Props>()

const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.content-preview-wrapper {
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  border-left: 3px solid rgba(84, 217, 68, 0.3);
}

.text-preview,
.chart-preview,
.image-preview,
.table-preview,
.unknown-preview {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
