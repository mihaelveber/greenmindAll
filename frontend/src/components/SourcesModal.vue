<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    title="📚 AI References & Sources"
    :style="{ width: '900px', maxHeight: '80vh' }"
    :bordered="false"
    size="huge"
    :segmented="{ content: true, footer: 'soft' }"
  >
    <n-scrollbar style="max-height: 60vh;">
      <n-space vertical :size="16">
        <!-- Summary -->
        <n-alert v-if="sources && sources.cited_documents" type="info" title="Source Summary">
          <n-text>AI analyzed {{ sources.cited_documents.length }} document sections from {{ groupedDocuments.length }} documents to generate this answer.</n-text>
          <br />
          <n-text depth="3">Confidence: {{ sources.confidence_score || 0 }}%</n-text>
        </n-alert>

        <!-- No sources available -->
        <n-alert v-if="!sources || !sources.cited_documents || sources.cited_documents.length === 0" type="warning">
          <n-text>No source references available for this answer.</n-text>
        </n-alert>

        <!-- Cited Documents with Chunks (Grouped) -->
        <div v-if="groupedDocuments.length > 0">
          <n-text strong style="font-size: 16px; margin-bottom: 12px; display: block;">
            📖 Source Documents & Excerpts
          </n-text>

          <n-space vertical :size="12">
            <n-card
              v-for="(group, idx) in groupedDocuments"
              :key="idx"
              size="small"
              :bordered="true"
              hoverable
              style="border-left: 3px solid #18a058;"
            >
              <template #header>
                <n-space align="center" justify="space-between" style="cursor: pointer;" @click="toggleDocument(idx)">
                  <n-space align="center">
                    <n-icon :component="DocumentTextOutline" size="20" color="#18a058" />
                    <n-text strong>{{ group.documentName }}</n-text>
                    <n-tag size="tiny" type="info">{{ group.chunks.length }} section{{ group.chunks.length > 1 ? 's' : '' }}</n-tag>
                  </n-space>
                  <n-space align="center">
                    <n-tag v-if="group.avgRelevance" type="success" size="small">
                      Avg Relevance: {{ Math.round(group.avgRelevance * 100) }}%
                    </n-tag>
                    <n-icon 
                      :component="expandedDocuments.has(idx) ? ChevronUpOutline : ChevronDownOutline" 
                      size="20" 
                    />
                  </n-space>
                </n-space>
              </template>

              <!-- Expandable chunks -->
              <n-collapse-transition :show="expandedDocuments.has(idx)">
                <n-space vertical :size="12" style="margin-top: 12px;">
                  <div
                    v-for="(chunk, chunkIdx) in group.chunks"
                    :key="chunkIdx"
                    style="
                      background: #f7f9fc;
                      padding: 12px;
                      border-radius: 4px;
                      border-left: 3px solid #18a058;
                    "
                  >
                    <!-- Chunk text with relevance badge -->
                    <div style="margin-bottom: 6px;">
                      <n-space align="center">
                        <n-tag v-if="chunk.relevance_score" size="tiny" type="success">
                          {{ Math.round(chunk.relevance_score * 100) }}% relevant
                        </n-tag>
                        <n-text depth="3" style="font-size: 11px;">
                          {{ chunk.uploaded_at ? new Date(chunk.uploaded_at).toLocaleDateString() : '' }}
                        </n-text>
                      </n-space>
                    </div>

                    <!-- Chunk text -->
                    <div
                      style="
                        font-family: 'Georgia', serif;
                        line-height: 1.6;
                        white-space: pre-wrap;
                        max-height: 300px;
                        overflow-y: auto;
                        padding: 8px;
                        background: white;
                        border-radius: 4px;
                        color: #333;
                      "
                    >
                      <n-text style="color: #333;">{{ chunk.full_chunk_text || chunk.chunk_text }}</n-text>
                    </div>
                  </div>
                </n-space>
              </n-collapse-transition>

              <!-- Show preview when collapsed -->
              <div v-if="!expandedDocuments.has(idx) && group.chunks.length > 0" style="margin-top: 8px;">
                <n-text depth="3" style="font-size: 12px; font-style: italic;">
                  Click to view {{ group.chunks.length }} excerpt{{ group.chunks.length > 1 ? 's' : '' }} from this document...
                </n-text>
              </div>
            </n-card>
          </n-space>
        </div>

        <!-- Linked Documents (if different from cited) -->
        <div v-if="sources && sources.linked_documents && sources.linked_documents.length > 0">
          <n-divider />
          <n-text strong style="font-size: 14px; margin-bottom: 8px; display: block;">
            🔗 All Linked Documents
          </n-text>
          <n-space>
            <n-tag
              v-for="doc in sources.linked_documents"
              :key="doc.id"
              type="default"
              size="small"
              :bordered="true"
            >
              {{ doc.file_name }}
              <n-icon v-if="doc.is_global" :component="GlobeOutline" size="14" style="margin-left: 4px;" />
            </n-tag>
          </n-space>
        </div>
      </n-space>
    </n-scrollbar>

    <template #footer>
      <n-space justify="end">
        <n-button @click="closeModal">Close</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  NModal, 
  NScrollbar, 
  NSpace, 
  NAlert, 
  NText, 
  NCard, 
  NTag, 
  NIcon, 
  NButton, 
  NDivider,
  NCollapseTransition
} from 'naive-ui'
import { DocumentTextOutline, GlobeOutline, ChevronDownOutline, ChevronUpOutline } from '@vicons/ionicons5'

interface Source {
  document_id?: number
  document_name?: string
  file_name?: string
  file_type?: string
  chunk_text?: string
  full_chunk_text?: string
  chunk_index?: number
  relevance_score?: number
  uploaded_at?: string
  is_global?: boolean
}

interface SourcesData {
  cited_documents?: Source[]
  linked_documents?: Source[]
  confidence_score?: number
  method?: string
}

interface GroupedDocument {
  documentName: string
  documentId?: number
  chunks: Source[]
  avgRelevance?: number
}

const props = defineProps<{
  show: boolean
  sources: SourcesData | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const showModal = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value)
})

const expandedDocuments = ref(new Set<number>())

// Group chunks by document
const groupedDocuments = computed<GroupedDocument[]>(() => {
  if (!props.sources?.cited_documents) return []
  
  const groups = new Map<string, GroupedDocument>()
  
  for (const chunk of props.sources.cited_documents) {
    const docName = chunk.document_name || chunk.file_name || 'Unknown Document'
    
    if (!groups.has(docName)) {
      groups.set(docName, {
        documentName: docName,
        documentId: chunk.document_id,
        chunks: [],
        avgRelevance: 0
      })
    }
    
    groups.get(docName)!.chunks.push(chunk)
  }
  
  // Sort chunks within each document by chunk_index (if available)
  for (const group of groups.values()) {
    group.chunks.sort((a, b) => {
      const aIndex = a.chunk_index !== undefined && a.chunk_index !== null ? a.chunk_index : 999999
      const bIndex = b.chunk_index !== undefined && b.chunk_index !== null ? b.chunk_index : 999999
      return aIndex - bIndex
    })
    
    // Calculate average relevance
    const relevanceScores = group.chunks
      .map(c => c.relevance_score)
      .filter((r): r is number => r !== undefined)
    
    if (relevanceScores.length > 0) {
      group.avgRelevance = relevanceScores.reduce((a, b) => a + b, 0) / relevanceScores.length
    }
  }
  
  // Convert to array and sort by average relevance (highest first)
  return Array.from(groups.values()).sort((a, b) => (b.avgRelevance || 0) - (a.avgRelevance || 0))
})

const toggleDocument = (idx: number) => {
  if (expandedDocuments.value.has(idx)) {
    expandedDocuments.value.delete(idx)
  } else {
    expandedDocuments.value.add(idx)
  }
}

const closeModal = () => {
  showModal.value = false
  expandedDocuments.value.clear()
}
</script>

<style scoped>
/* Smooth animations */
.n-card {
  transition: all 0.2s ease;
}

.n-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
