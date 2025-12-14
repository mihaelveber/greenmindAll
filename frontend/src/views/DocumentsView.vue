<template>
  <div class="documents-container">
    <n-card :bordered="false">
      <template #header>
        <div class="header-section">
          <n-space align="center" :size="16">
            <n-button text @click="$router.push('/dashboard')" size="large">
              <template #icon>
                <n-icon :component="ArrowBackOutline" size="24" />
              </template>
            </n-button>
            <div>
              <n-h2 style="margin: 0;">📄 Documents</n-h2>
              <p class="subtitle" style="margin: 4px 0 0 0;">Manage your company documents</p>
            </div>
          </n-space>
          <n-space :size="12">
            <n-button type="success" size="large" @click="showAddWebsiteModal = true">
              <template #icon>
                <n-icon :component="GlobeOutline" />
              </template>
              Add Website
            </n-button>
            <n-button type="primary" size="large" @click="showUploadModal = true">
              <template #icon>
                <n-icon :component="AddOutline" />
              </template>
              Add Document
            </n-button>
          </n-space>
        </div>
      </template>

      <!-- Filter Section -->
      <div v-if="documents.length > 0" style="margin-bottom: 16px;">
        <n-space :size="12">
          <n-text strong>Filter by type:</n-text>
          <n-button-group>
            <n-button 
              :type="documentFilter === 'all' ? 'primary' : 'default'"
              @click="documentFilter = 'all'"
            >
              All ({{ documents.length }})
            </n-button>
            <n-button 
              :type="documentFilter === 'global' ? 'success' : 'default'"
              @click="documentFilter = 'global'"
            >
              🌐 Global ({{ globalDocuments.length }})
            </n-button>
            <n-button 
              :type="documentFilter === 'specific' ? 'warning' : 'default'"
              @click="documentFilter = 'specific'"
            >
              📎 Question-Specific ({{ specificDocuments.length }})
            </n-button>
          </n-button-group>
        </n-space>
      </div>

      <!-- Website Documents Cards -->
      <n-card 
        v-for="websiteDoc in websiteDocuments"
        :key="websiteDoc.id"
        :bordered="true" 
        style="margin-bottom: 16px; border: 2px solid rgba(84, 217, 68, 0.5); background: linear-gradient(135deg, rgba(84, 217, 68, 0.1) 0%, rgba(84, 217, 68, 0.05) 100%);"
      >
        <template #header>
          <n-space align="center" :size="12" justify="space-between">
            <n-space align="center" :size="12">
              <n-icon :component="GlobeOutline" size="32" color="#54d944" />
              <div>
                <n-h3 style="margin: 0;">🌐 {{ websiteDoc.file_name }}</n-h3>
                <n-text depth="3" style="font-size: 12px;">{{ extractUrlFromFilename(websiteDoc.file_name) }}</n-text>
              </div>
            </n-space>
            <n-popconfirm
              @positive-click="deleteDocument(websiteDoc.id)"
              positive-text="Delete"
              negative-text="Cancel"
            >
              <template #trigger>
                <n-button text type="error">
                  <template #icon>
                    <n-icon :component="TrashOutline" />
                  </template>
                </n-button>
              </template>
              Delete this website document?
            </n-popconfirm>
          </n-space>
        </template>
        
        <n-space vertical :size="12">
          <n-space :size="8">
            <n-tag type="success" :bordered="false">Global Document</n-tag>
            <n-tag :bordered="false">{{ formatFileSize(websiteDoc.file_size) }}</n-tag>
            <n-text depth="3" style="font-size: 12px;">Last updated: {{ formatDate(websiteDoc.uploaded_at) }}</n-text>
          </n-space>
          
          <n-alert type="info" :bordered="false">
            This document contains website content. AI uses it to provide context-aware answers for all ESRS questions.
          </n-alert>
          
          <n-space>
            <n-button type="primary" @click="openEditWebsiteModal(websiteDoc)">
              <template #icon>
                <n-icon :component="CreateOutline" />
              </template>
              Update URL
            </n-button>
            <n-button text type="info" @click="previewDocument(websiteDoc)">
              <template #icon>
                <n-icon :component="EyeOutline" />
              </template>
              View Content
            </n-button>
          </n-space>
        </n-space>
      </n-card>

      <!-- Documents List -->
      <n-spin :show="loading">
        <div v-if="documents.length === 0" class="empty-state">
          <n-empty
            description="No documents uploaded yet"
            size="large"
          >
            <template #icon>
              <n-icon :component="DocumentTextOutline" size="80" color="rgba(255,255,255,0.3)" />
            </template>
            <template #extra>
              <n-button type="primary" @click="showUploadModal = true">
                Upload your first document
              </n-button>
            </template>
          </n-empty>
        </div>

        <n-list v-if="filteredDocuments.length > 0" bordered>
          <n-list-item v-for="doc in filteredDocuments" :key="doc.id">
            <template #prefix>
              <n-icon :component="getFileIcon(doc.file_type)" size="32" color="#54d944" />
            </template>
            
            <n-thing :title="doc.file_name">
              <template #description>
                <n-space :size="8" style="flex-wrap: wrap;">
                  <!-- Document Type Badge -->
                  <n-tag 
                    size="small" 
                    :type="doc.is_global ? 'success' : 'warning'"
                    :bordered="false"
                  >
                    {{ doc.is_global ? '🌐 Global' : '📎 Question-Specific' }}
                  </n-tag>
                  
                  <!-- Linked Questions Count (if not global) -->
                  <n-tooltip v-if="!doc.is_global && doc.linked_disclosure_codes?.length > 0" trigger="hover">
                    <template #trigger>
                      <n-tag 
                        size="small" 
                        :bordered="false"
                        type="info"
                        style="cursor: help"
                      >
                        {{ doc.linked_questions_count }} question{{ doc.linked_questions_count > 1 ? 's' : '' }}
                      </n-tag>
                    </template>
                    <div style="max-width: 400px;">
                      <strong>Linked to questions:</strong><br/>
                      {{ doc.linked_disclosure_codes.join(', ') }}
                    </div>
                  </n-tooltip>
                  
                  <!-- No linked questions warning -->
                  <n-tag 
                    v-else-if="!doc.is_global && doc.linked_questions_count === 0"
                    size="small" 
                    :bordered="false"
                    type="warning"
                  >
                    ⚠️ Not linked to any question
                  </n-tag>
                  
                  <n-tag size="small" :bordered="false">
                    {{ formatFileSize(doc.file_size) }}
                  </n-tag>
                  <n-tag size="small" :bordered="false" type="info">
                    {{ doc.file_type }}
                  </n-tag>
                  <n-text depth="3" style="font-size: 12px">
                    Uploaded: {{ formatDate(doc.uploaded_at) }}
                  </n-text>
                </n-space>
              </template>
            </n-thing>

            <template #suffix>
              <n-space>
                <!-- Only show "Make Global" button if document is NOT global -->
                <n-button
                  v-if="!doc.is_global"
                  text
                  type="success"
                  @click="toggleGlobalStatus(doc)"
                  title="Mark as global - will auto-link to all questions"
                >
                  <template #icon>
                    <n-icon :component="GlobeOutline" />
                  </template>
                  Make Global
                </n-button>
                <n-button
                  text
                  type="info"
                  @click="previewDocument(doc)"
                >
                  <template #icon>
                    <n-icon :component="EyeOutline" />
                  </template>
                  Preview
                </n-button>
                <n-button
                  text
                  type="success"
                  @click="downloadDocument(doc)"
                >
                  <template #icon>
                    <n-icon :component="DownloadOutline" />
                  </template>
                  Download
                </n-button>
                <n-popconfirm
                  @positive-click="deleteDocument(doc.id)"
                  positive-text="Delete"
                  negative-text="Cancel"
                >
                  <template #trigger>
                    <n-button
                      text
                      type="error"
                    >
                      <template #icon>
                        <n-icon :component="TrashOutline" />
                      </template>
                      Delete
                    </n-button>
                  </template>
                  Are you sure you want to delete "{{ doc.file_name }}"?
                </n-popconfirm>
              </n-space>
            </template>
          </n-list-item>
        </n-list>
      </n-spin>
    </n-card>

    <!-- Upload Modal -->
    <n-modal
      v-model:show="showUploadModal"
      preset="card"
      title="Upload Document"
      :style="{ width: '600px' }"
      :bordered="false"
    >
      <n-upload
        multiple
        :max="10"
        :file-list="uploadFileList"
        @update:file-list="handleFileListUpdate"
        :custom-request="handleUpload"
        :show-file-list="true"
      >
        <n-upload-dragger>
          <div class="upload-content">
            <n-icon size="64" :component="CloudUploadOutline" color="#54d944" />
            <n-h3>Click or drag files to upload</n-h3>
            <p class="upload-hint">
              Support for PDF, Word, Excel, and other document formats
            </p>
          </div>
        </n-upload-dragger>
      </n-upload>

      <n-divider>OR</n-divider>

      <n-upload
        multiple
        :max="10"
        :custom-request="handleUpload"
        :show-file-list="false"
      >
        <n-button type="primary" size="large" block>
          <template #icon>
            <n-icon :component="CloudUploadOutline" />
          </template>
          Browse Files on Computer
        </n-button>
      </n-upload>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showUploadModal = false">Close</n-button>
          <n-button type="primary" @click="showUploadModal = false">Done</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- View Document Modal -->
    <n-modal
      v-model:show="showViewModal"
      preset="card"
      :title="selectedDocument?.file_name"
      :style="{ width: '800px' }"
      :bordered="false"
    >
      <n-descriptions bordered :column="1">
        <n-descriptions-item label="File Name">
          {{ selectedDocument?.file_name }}
        </n-descriptions-item>
        <n-descriptions-item label="File Type">
          {{ selectedDocument?.file_type }}
        </n-descriptions-item>
        <n-descriptions-item label="File Size">
          {{ formatFileSize(selectedDocument?.file_size || 0) }}
        </n-descriptions-item>
        <n-descriptions-item label="Uploaded">
          {{ formatDate(selectedDocument?.uploaded_at) }}
        </n-descriptions-item>
      </n-descriptions>

      <n-alert type="info" style="margin-top: 16px">
        Click "Preview" button to open PDF and images in a new tab. Click "Download" to download the file.
      </n-alert>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showViewModal = false">Close</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Edit Website Modal -->
    <n-modal
      v-model:show="showEditWebsiteModal"
      preset="card"
      title="🌐 Edit Company Website"
      :style="{ width: '600px' }"
      :bordered="false"
    >
      <n-space vertical :size="16">
        <n-alert type="info" :bordered="false">
          Update your company website URL. We'll automatically fetch and analyze the new content for better AI-generated answers.
        </n-alert>
        
        <n-form-item label="Website URL">
          <n-input
            v-model:value="editingWebsiteUrl"
            placeholder="https://www.your-company.com"
            size="large"
            clearable
          >
            <template #prefix>
              <n-icon :component="GlobeOutline" />
            </template>
          </n-input>
        </n-form-item>
        
        <n-alert type="warning" :bordered="false">
          ⚠️ This will delete the current website document and create a new one with fresh content.
        </n-alert>
      </n-space>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showEditWebsiteModal = false">Cancel</n-button>
          <n-button 
            type="primary" 
            :loading="updatingWebsite"
            @click="updateWebsite"
          >
            Update & Re-scrape
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Add Website Modal -->
    <n-modal
      v-model:show="showAddWebsiteModal"
      preset="card"
      title="🌐 Add Website Document"
      :style="{ width: '600px' }"
      :bordered="false"
    >
      <n-space vertical :size="16">
        <n-alert type="info" :bordered="false">
          Add a new website as a global document. We'll automatically fetch and analyze the content for AI-generated answers.
        </n-alert>
        
        <n-form-item label="Website URL">
          <n-input
            v-model:value="editingWebsiteUrl"
            placeholder="https://www.your-company.com"
            size="large"
            clearable
          >
            <template #prefix>
              <n-icon :component="GlobeOutline" />
            </template>
          </n-input>
        </n-form-item>
        
        <n-alert type="success" :bordered="false">
          ✅ The website will be added as a global document and used for all ESRS questions.
        </n-alert>
      </n-space>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddWebsiteModal = false">Cancel</n-button>
          <n-button 
            type="primary" 
            :loading="addingWebsite"
            @click="addNewWebsite"
          >
            Add Website
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  useMessage,
  NCard,
  NH2,
  NH3,
  NButton,
  NButtonGroup,
  NIcon,
  NSpin,
  NEmpty,
  NList,
  NListItem,
  NThing,
  NSpace,
  NTag,
  NText,
  NPopconfirm,
  NModal,
  NUpload,
  NUploadDragger,
  NDivider,
  NDescriptions,
  NDescriptionsItem,
  NAlert,
  NInput,
  NFormItem,
  NTooltip,
  type UploadFileInfo,
  type UploadCustomRequestOptions
} from 'naive-ui'
import { 
  DocumentTextOutline,
  AddOutline,
  CloudUploadOutline,
  TrashOutline,
  EyeOutline,
  DocumentOutline,
  ImageOutline,
  FileTrayFullOutline,
  DownloadOutline,
  ArrowBackOutline,
  GlobeOutline,
  CreateOutline
} from '@vicons/ionicons5'
import api from '../services/api'

interface Document {
  id: number
  file_name: string
  file_size: number
  file_type: string
  uploaded_at: string
  document_type: 'Global' | 'Question-Specific'
  linked_questions_count: number
  linked_disclosure_codes?: string[]  // ✅ NEW: List of disclosure codes
  is_global: boolean
}

const message = useMessage()
const loading = ref(false)
const documents = ref<Document[]>([])
const showUploadModal = ref(false)
const showViewModal = ref(false)
const uploadFileList = ref<UploadFileInfo[]>([])
const selectedDocument = ref<Document | null>(null)

// Website documents
const websiteUrl = ref<string>('')
const showEditWebsiteModal = ref(false)
const showAddWebsiteModal = ref(false)
const editingWebsiteUrl = ref('')
const editingDocumentId = ref<number | null>(null)
const updatingWebsite = ref(false)
const addingWebsite = ref(false)

// Document type filter
const documentFilter = ref<'all' | 'global' | 'specific'>('all')

const globalDocuments = computed(() => 
  documents.value.filter(d => d.is_global)
)

const specificDocuments = computed(() => 
  documents.value.filter(d => !d.is_global)
)

const filteredDocuments = computed(() => {
  // Exclude website document from regular list
  const regularDocs = documents.value.filter(d => !d.file_name.startsWith('Company Website:'))
  
  if (documentFilter.value === 'global') return regularDocs.filter(d => d.is_global)
  if (documentFilter.value === 'specific') return regularDocs.filter(d => !d.is_global)
  return regularDocs
})

// Website documents computed property (can be multiple)
const websiteDocuments = computed(() => 
  documents.value.filter(d => d.file_name.startsWith('Company Website:'))
)

const loadDocuments = async () => {
  loading.value = true
  try {
    const response = await api.get('/documents/list')
    documents.value = response.data
  } catch (error) {
    message.error('Failed to load documents')
  } finally {
    loading.value = false
  }
}

const loadUserProfile = async () => {
  try {
    const response = await api.get('/auth/me')
    websiteUrl.value = response.data.website_url || ''
  } catch (error) {
    console.error('Failed to load user profile')
  }
}

const extractUrlFromFilename = (filename: string) => {
  // Extract domain from "Company Website: example.com" format
  const match = filename.match(/Company Website: (.+)/)
  return match ? match[1] : filename
}

const openEditWebsiteModal = (doc: Document) => {
  editingWebsiteUrl.value = extractUrlFromFilename(doc.file_name)
  editingDocumentId.value = doc.id
  showEditWebsiteModal.value = true
}

const updateWebsite = async () => {
  if (!editingWebsiteUrl.value.trim()) {
    message.error('Please enter a valid URL')
    return
  }
  
  updatingWebsite.value = true
  try {
    await api.post('/profile/update-website', {
      website_url: editingWebsiteUrl.value,
      document_id: editingDocumentId.value // Send specific document to update
    })
    
    message.success('Website URL updated. Re-scraping content...')
    websiteUrl.value = editingWebsiteUrl.value
    showEditWebsiteModal.value = false
    
    // Reload documents after a delay to allow scraping to complete
    setTimeout(() => {
      loadDocuments()
    }, 3000)
  } catch (error) {
    message.error('Failed to update website URL')
  } finally {
    updatingWebsite.value = false
  }
}

const addNewWebsite = async () => {
  if (!editingWebsiteUrl.value.trim()) {
    message.error('Please enter a valid URL')
    return
  }
  
  addingWebsite.value = true
  try {
    await api.post('/documents/add-website', {
      website_url: editingWebsiteUrl.value
    })
    
    message.success('Website scraping started! Document will appear shortly...')
    editingWebsiteUrl.value = ''
    showAddWebsiteModal.value = false
    
    // Reload documents after a delay to allow scraping to complete
    setTimeout(() => {
      loadDocuments()
    }, 3000)
  } catch (error) {
    message.error('Failed to add website')
  } finally {
    addingWebsite.value = false
  }
}

const handleFileListUpdate = (files: UploadFileInfo[]) => {
  uploadFileList.value = files
}

const handleUpload = async (options: UploadCustomRequestOptions) => {
  const { file, onFinish, onError } = options
  
  try {
    const formData = new FormData()
    formData.append('file', file.file as File)

    await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    message.success(`${file.name} uploaded successfully`)
    onFinish()
    
    // Reload documents list
    await loadDocuments()
  } catch (error: any) {
    message.error(`Failed to upload ${file.name}`)
    onError()
  }
}

const deleteDocument = async (id: number) => {
  try {
    await api.delete(`/documents/delete/${id}`)
    message.success('Document deleted successfully')
    await loadDocuments()
  } catch (error) {
    message.error('Failed to delete document')
  }
}

const toggleGlobalStatus = async (doc: Document) => {
  try {
    const response = await api.put(`/documents/${doc.id}/toggle-global`)
    
    if (response.data.success) {
      message.success(response.data.message)
      await loadDocuments() // Reload to show updated status
    }
  } catch (error) {
    message.error('Failed to update document status')
  }
}

const previewDocument = (doc: Document) => {
  // Odpri dokument v novem browser tabu - browser bo odločil ali lahko prikaže ali ne
  const token = localStorage.getItem('access_token')
  const url = `http://localhost:8090/api/documents/download/${doc.id}?token=${token}`
  
  window.open(url, '_blank')
  message.info(`Opening ${doc.file_name}...`)
}

const downloadDocument = (doc: Document) => {
  // Isti URL kot preview - browser bo downloadal če ne more prikazati
  const token = localStorage.getItem('access_token')
  const url = `http://localhost:8090/api/documents/download/${doc.id}?token=${token}`
  
  window.open(url, '_blank')
  message.success(`Opening ${doc.file_name}...`)
}

const getFileIcon = (fileType: string) => {
  if (fileType.includes('pdf')) return DocumentTextOutline
  if (fileType.includes('image')) return ImageOutline
  if (fileType.includes('word') || fileType.includes('document')) return DocumentOutline
  return FileTrayFullOutline
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadDocuments()
  loadUserProfile()
})
</script>

<style scoped>
.documents-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.subtitle {
  color: rgba(255, 255, 255, 0.6);
  margin-top: 4px;
  font-size: 14px;
}

.empty-state {
  padding: 60px 20px;
}

.upload-content {
  padding: 40px;
  text-align: center;
}

.upload-hint {
  color: rgba(255, 255, 255, 0.6);
  margin-top: 12px;
}
</style>
