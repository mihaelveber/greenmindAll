<template>
  <div class="version-content-display">
    <!-- TEXT content -->
    <div v-if="version.content.text" class="text-content">
      <div v-html="formatText(version.content.text)" class="markdown-content"></div>
    </div>
    
    <!-- CHART content -->
    <div v-else-if="version.content.type" class="chart-content">
      <n-card :title="version.content.title || 'Chart'" size="small">
        <ChartRenderer 
          :chart-data="version.content" 
          :width="400" 
          :height="300" 
        />
      </n-card>
    </div>
    
    <!-- IMAGE content -->
    <div v-else-if="version.content.image_base64 || version.content.url" class="image-content">
      <n-card :title="version.content.title || 'Image'" size="small">
        <img 
          :src="version.content.image_base64 ? `data:image/png;base64,${version.content.image_base64}` : version.content.url"
          alt="Version image"
          style="max-width: 100%; border-radius: 8px;"
        />
        <n-text v-if="version.content.prompt" depth="3" style="display: block; margin-top: 8px; font-style: italic;">
          Prompt: {{ version.content.prompt }}
        </n-text>
      </n-card>
    </div>
    
    <!-- TABLE content -->
    <div v-else-if="version.content.headers" class="table-content">
      <n-card :title="version.content.title || 'Table'" size="small">
        <n-data-table
          :columns="tableColumns"
          :data="tableData"
          :pagination="false"
          size="small"
        />
      </n-card>
    </div>
    
    <!-- Fallback -->
    <div v-else class="unknown-content">
      <n-alert type="info">
        <pre>{{ JSON.stringify(version.content, null, 2) }}</pre>
      </n-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NCard, NText, NDataTable, NAlert } from 'naive-ui'
import ChartRenderer from './ChartRenderer.vue'

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

const props = defineProps<Props>()

const formatText = (text: string): string => {
  if (!text) return ''
  
  // Basic markdown to HTML conversion
  let html = text
  
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  // Line breaks
  html = html.replace(/\n/g, '<br>')
  
  return html
}

const tableColumns = computed(() => {
  if (!props.version.content.headers) return []
  return props.version.content.headers.map((h: string) => ({
    title: h,
    key: h
  }))
})

const tableData = computed(() => {
  if (!props.version.content.rows || !props.version.content.headers) return []
  return props.version.content.rows.map((row: any[]) => {
    const obj: any = {}
    props.version.content.headers.forEach((h: string, i: number) => {
      obj[h] = row[i]
    })
    return obj
  })
})
</script>

<style scoped>
.version-content-display {
  width: 100%;
}

.text-content,
.chart-content,
.image-content,
.table-content,
.unknown-content {
  width: 100%;
}

.markdown-content {
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.85);
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  color: rgba(84, 217, 68, 0.9);
  margin-top: 16px;
  margin-bottom: 8px;
}

.markdown-content strong {
  color: rgba(255, 255, 255, 0.95);
}

.markdown-content em {
  color: rgba(255, 255, 255, 0.7);
}
</style>
