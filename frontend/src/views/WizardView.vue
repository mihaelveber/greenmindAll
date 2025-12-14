<template>
  <div class="wizard-container">
    <n-card class="wizard-card" :bordered="false">
      <n-steps :current="currentStep" :status="currentStatus">
        <n-step title="Tip podjetja" description="Izberite velikost vašega podjetja" />
        <n-step title="Dokumenti" description="Naložite potrebne dokumente" />
        <n-step title="Zaključek" description="Dokončajte nastavitev" />
      </n-steps>

      <div class="wizard-content">
        <!-- Step 1: Company Type Selection -->
        <div v-if="currentStep === 1" class="step-container">
          <div class="welcome-header">
            <n-gradient-text :size="36" type="info">
              Welcome! 👋
            </n-gradient-text>
            <p class="subtitle">Let's set up your ESRS compliance profile</p>
          </div>

          <n-h2 class="section-title">Select Your Company Type</n-h2>
          <p class="section-description">This determines which ESRS requirements apply to you</p>

          <n-grid :cols="3" :x-gap="24" responsive="screen" class="company-types">
            <n-gi>
              <n-card
                :class="['company-card', { selected: selectedCompanyType === 'small' }]"
                hoverable
                @click="selectCompanyType('small')"
              >
                <div class="card-icon">🏢</div>
                <n-h3 class="card-title">Small Company</n-h3>
                <p class="card-subtitle">Fewer than 50 employees and limited reporting requirements</p>
                
                <n-divider />
                
                <n-space vertical :size="8" class="features">
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Simplified disclosures</span>
                  </div>
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Essential metrics only</span>
                  </div>
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Reduced compliance burden</span>
                  </div>
                </n-space>
              </n-card>
            </n-gi>

            <n-gi>
              <n-card
                :class="['company-card', { selected: selectedCompanyType === 'sme' }]"
                hoverable
                @click="selectCompanyType('sme')"
              >
                <div class="card-icon">🏭</div>
                <n-h3 class="card-title">SME (Medium Enterprise)</n-h3>
                <p class="card-subtitle">50-250 employees with standard ESRS framework</p>
                
                <n-divider />
                
                <n-space vertical :size="8" class="features">
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Standard disclosures</span>
                  </div>
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Materiality assessment</span>
                  </div>
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Stakeholder engagement</span>
                  </div>
                </n-space>
              </n-card>
            </n-gi>

            <n-gi>
              <n-card
                :class="['company-card', { selected: selectedCompanyType === 'large' }]"
                hoverable
                @click="selectCompanyType('large')"
              >
                <div class="card-icon">🏬</div>
                <n-h3 class="card-title">Large Corporation</n-h3>
                <p class="card-subtitle">Over 250 employees with comprehensive requirements</p>
                
                <n-divider />
                
                <n-space vertical :size="8" class="features">
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Full ESRS compliance</span>
                  </div>
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Value chain reporting</span>
                  </div>
                  <div class="feature-item">
                    <n-icon :component="CheckmarkCircle" color="#54d944" />
                    <span>Detailed governance</span>
                  </div>
                </n-space>
              </n-card>
            </n-gi>
          </n-grid>

          <n-divider style="margin: 32px 0;" />

          <!-- Company Website URL -->
          <n-h2 class="section-title">Company Website (Optional)</n-h2>
          <p class="section-description">We'll analyze your website to better understand your company's sustainability initiatives</p>
          
          <n-card :bordered="true" style="max-width: 600px; margin: 0 auto;">
            <n-form-item label="Website URL" :show-feedback="false">
              <n-input
                v-model:value="companyWebsite"
                placeholder="https://www.your-company.com"
                size="large"
                clearable
              >
                <template #prefix>
                  🌐
                </template>
              </n-input>
            </n-form-item>
            <n-alert v-if="companyWebsite" type="info" style="margin-top: 12px;">
              <template #icon>
                <n-icon :component="CheckmarkCircle" />
              </template>
              We'll fetch and analyze your website content to provide better AI-generated answers based on your company's actual practices and policies.
            </n-alert>
          </n-card>

          <div class="actions">
            <n-button
              type="primary"
              size="large"
              :disabled="!selectedCompanyType"
              @click="nextStep"
            >
              Continue to Dashboard
            </n-button>
          </div>
        </div>

        <!-- Step 2: Document Upload -->
        <div v-if="currentStep === 2" class="step-container">
          <div class="welcome-header">
            <n-gradient-text :size="36" type="info">
              Upload Documents 📄
            </n-gradient-text>
            <p class="subtitle">Add your company documents for compliance</p>
          </div>

          <n-card :bordered="false" class="upload-card">
            <n-upload
              multiple
              directory-dnd
              :max="10"
              :file-list="fileList"
              @update:file-list="handleFileListUpdate"
              :custom-request="handleUpload"
            >
              <n-upload-dragger>
                <div class="upload-content">
                  <n-icon size="64" :component="CloudUploadOutline" color="#54d944" />
                  <n-h3>Click or drag files to this area to upload</n-h3>
                  <p class="upload-hint">
                    Support for PDF, Word, Excel, and other document formats.
                    You can upload multiple files at once.
                  </p>
                </div>
              </n-upload-dragger>
            </n-upload>

            <n-divider />

            <div v-if="fileList.length > 0" class="file-list">
              <n-h4>Uploaded Files ({{ fileList.length }})</n-h4>
              <n-list bordered>
                <n-list-item v-for="file in fileList" :key="file.id">
                  <template #prefix>
                    <n-icon :component="DocumentTextOutline" size="24" />
                  </template>
                  <n-thing :title="file.name">
                    <template #description>
                      {{ formatFileSize(file.file?.size || 0) }}
                    </template>
                  </n-thing>
                  <template #suffix>
                    <n-button
                      text
                      type="error"
                      @click="removeFile(file)"
                    >
                      <template #icon>
                        <n-icon :component="TrashOutline" />
                      </template>
                    </n-button>
                  </template>
                </n-list-item>
              </n-list>
            </div>
          </n-card>

          <div class="actions">
            <n-button size="large" @click="prevStep">
              Back
            </n-button>
            <n-button
              type="primary"
              size="large"
              @click="nextStep"
            >
              Continue
            </n-button>
          </div>
        </div>

        <!-- Step 3: Completion -->
        <div v-if="currentStep === 3" class="step-container completion">
          <n-result
            status="success"
            title="Setup Complete!"
            description="Your Greenmind AI profile has been configured successfully."
          >
            <template #icon>
              <n-icon :component="CheckmarkCircle" color="#54d944" size="80" />
            </template>
            <template #footer>
              <n-space vertical :size="16">
                <n-card :bordered="false" class="summary-card">
                  <n-descriptions bordered :column="1">
                    <n-descriptions-item label="Company Type">
                      {{ getCompanyTypeLabel(selectedCompanyType) }}
                    </n-descriptions-item>
                    <n-descriptions-item label="Documents Uploaded">
                      {{ uploadedFiles.length }} files
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>
                
                <n-button
                  type="primary"
                  size="large"
                  @click="goToDashboard"
                  :loading="completing"
                >
                  Next
                </n-button>
              </n-space>
            </template>
          </n-result>
        </div>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  useMessage,
  NCard,
  NSteps,
  NStep,
  NGradientText,
  NH2,
  NH3,
  NH4,
  NGrid,
  NGi,
  NDivider,
  NSpace,
  NIcon,
  NButton,
  NUpload,
  NUploadDragger,
  NList,
  NListItem,
  NThing,
  NResult,
  NDescriptions,
  NDescriptionsItem,
  NInput,
  NFormItem,
  NAlert,
  type UploadFileInfo,
  type UploadCustomRequestOptions
} from 'naive-ui'
import { 
  CheckmarkCircle, 
  CloudUploadOutline, 
  DocumentTextOutline,
  TrashOutline
} from '@vicons/ionicons5'
import { useAuthStore } from '../stores/auth.store'
import api from '../services/api'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const currentStep = ref(1)
const currentStatus = ref<'process' | 'finish' | 'error' | 'wait'>('process')
const selectedCompanyType = ref<'small' | 'sme' | 'large' | null>(null)
const companyWebsite = ref('')
const fileList = ref<UploadFileInfo[]>([])
const uploadedFiles = ref<string[]>([])
const completing = ref(false)

const selectCompanyType = (type: 'small' | 'sme' | 'large') => {
  selectedCompanyType.value = type
}

const getCompanyTypeLabel = (type: string | null) => {
  const labels = {
    small: 'Small Company (< 50 employees)',
    sme: 'SME - Medium Enterprise (50-250 employees)',
    large: 'Large Corporation (> 250 employees)'
  }
  return type ? labels[type as keyof typeof labels] : 'Not selected'
}

const handleFileListUpdate = (files: UploadFileInfo[]) => {
  fileList.value = files
}

const handleUpload = async (options: UploadCustomRequestOptions) => {
  const { file, onFinish, onError } = options
  
  try {
    const formData = new FormData()
    formData.append('file', file.file as File)
    formData.append('company_type', selectedCompanyType.value || '')

    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    uploadedFiles.value.push(response.data.file_id)
    message.success(`${file.name} uploaded successfully`)
    onFinish()
  } catch (error: any) {
    message.error(`Failed to upload ${file.name}`)
    onError()
  }
}

const removeFile = (file: UploadFileInfo) => {
  const index = fileList.value.findIndex(f => f.id === file.id)
  if (index > -1) {
    fileList.value.splice(index, 1)
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const nextStep = async () => {
  if (currentStep.value === 1) {
    // Save company type and website
    try {
      await api.post('/profile/company-type', {
        company_type: selectedCompanyType.value,
        website_url: companyWebsite.value || null
      })
      
      // If website URL provided, trigger scraping task
      if (companyWebsite.value) {
        try {
          await api.post('/profile/scrape-website', {
            website_url: companyWebsite.value
          })
          message.success('Website scraping started! We\'ll analyze your website content.')
        } catch (error) {
          console.error('Failed to start website scraping:', error)
          message.warning('Website saved but scraping failed. You can retry later.')
        }
      }
      
      currentStep.value = 2
    } catch (error) {
      message.error('Failed to save company type')
    }
  } else if (currentStep.value === 2) {
    currentStep.value = 3
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const goToDashboard = async () => {
  completing.value = true
  try {
    // Mark wizard as complete
    await api.post('/profile/complete-wizard')
    
    // Refresh user data in store
    await authStore.fetchCurrentUser()
    
    message.success('Setup completed successfully!')
    router.push('/dashboard')
  } catch (error) {
    message.error('Failed to complete setup')
  } finally {
    completing.value = false
  }
}
</script>

<style scoped>
.wizard-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.wizard-card {
  width: 100%;
  max-width: 1200px;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  padding: 40px;
}

.wizard-content {
  margin-top: 40px;
}

.step-container {
  min-height: 500px;
}

.welcome-header {
  text-align: center;
  margin-bottom: 48px;
}

.subtitle {
  color: rgba(255, 255, 255, 0.7);
  margin-top: 12px;
  font-size: 18px;
}

.section-title {
  text-align: center;
  margin-bottom: 12px;
}

.section-description {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 40px;
  font-size: 16px;
}

.company-types {
  margin-bottom: 40px;
}

.company-card {
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.03);
  border: 2px solid rgba(255, 255, 255, 0.1);
  height: 100%;
}

.company-card:hover {
  transform: translateY(-4px);
  border-color: rgba(84, 217, 68, 0.4);
  box-shadow: 0 8px 24px rgba(84, 217, 68, 0.2);
}

.company-card.selected {
  border-color: #54d944;
  background: rgba(84, 217, 68, 0.1);
  box-shadow: 0 8px 24px rgba(84, 217, 68, 0.3);
}

.card-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 16px;
}

.card-title {
  text-align: center;
  margin-bottom: 8px;
  font-size: 20px;
}

.card-subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  min-height: 40px;
}

.features {
  margin-top: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 40px;
}

.upload-card {
  background: rgba(255, 255, 255, 0.03);
  margin-bottom: 24px;
}

.upload-content {
  padding: 40px;
  text-align: center;
}

.upload-hint {
  color: rgba(255, 255, 255, 0.6);
  margin-top: 12px;
}

.file-list {
  margin-top: 24px;
}

.completion {
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-card {
  background: rgba(255, 255, 255, 0.03);
  max-width: 500px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .wizard-card {
    padding: 24px;
  }
  
  .company-types {
    grid-template-columns: 1fr !important;
  }
}
</style>
