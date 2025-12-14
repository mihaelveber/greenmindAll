<template>
  <div class="admin-container">
    <n-card :bordered="false">
      <template #header>
        <div class="header-section">
          <n-space align="center" :size="16" style="width: 100%; justify-content: space-between;">
            <n-space align="center" :size="16">
              <n-button text @click="$router.push('/dashboard')" size="large">
                <template #icon>
                  <n-icon :component="ArrowBackOutline" size="24" />
                </template>
              </n-button>
              <div>
                <n-h2 style="margin: 0;">⚙️ Admin Dashboard</n-h2>
                <p class="subtitle">System management and configuration</p>
              </div>
            </n-space>
            <n-button type="primary" @click="$router.push('/admin-dashboard')">
              📊 New Analytics Dashboard
            </n-button>
          </n-space>
        </div>
      </template>

      <!-- Admin Navigation Tabs -->
      <n-tabs type="line" animated>
        <!-- Users & Companies Tab -->
        <n-tab-pane name="users" tab="👥 Users & Companies">
          <n-space vertical :size="16">
            <!-- Statistics Cards -->
            <n-grid :cols="4" :x-gap="16">
              <n-grid-item>
                <n-card title="Total Users" :bordered="true" size="small">
                  <n-statistic :value="statistics.total_users">
                    <template #prefix>
                      <n-icon :component="PeopleOutline" color="#52c41a" />
                    </template>
                  </n-statistic>
                </n-card>
              </n-grid-item>
              
              <n-grid-item>
                <n-card title="Active Companies" :bordered="true" size="small">
                  <n-statistic :value="statistics.total_companies">
                    <template #prefix>
                      <n-icon :component="BusinessOutline" color="#1890ff" />
                    </template>
                  </n-statistic>
                </n-card>
              </n-grid-item>
              
              <n-grid-item>
                <n-card title="AI Answers Generated" :bordered="true" size="small">
                  <n-statistic :value="statistics.total_ai_answers">
                    <template #prefix>
                      <n-icon :component="SparklesOutline" color="#faad14" />
                    </template>
                  </n-statistic>
                </n-card>
              </n-grid-item>
              
              <n-grid-item>
                <n-card title="Documents Uploaded" :bordered="true" size="small">
                  <n-statistic :value="statistics.total_documents">
                    <template #prefix>
                      <n-icon :component="DocumentTextOutline" color="#722ed1" />
                    </template>
                  </n-statistic>
                </n-card>
              </n-grid-item>
            </n-grid>

            <!-- Users Table -->
            <n-card title="All Users" :bordered="true">
              <n-data-table
                :columns="userColumns"
                :data="users"
                :loading="loadingUsers"
                :pagination="{ pageSize: 10 }"
                :bordered="false"
              />
            </n-card>
          </n-space>
        </n-tab-pane>

        <!-- Prompts Configuration Tab (Standard-level) -->
        <n-tab-pane name="prompts" tab="💬 Standard Prompts">
          <n-space vertical :size="16">
            <n-alert type="info" :bordered="false">
              Configure AI prompts for each ESRS standard. Changes will affect all disclosures within that standard.
            </n-alert>

            <!-- ESRS Standards List with Prompts -->
            <n-card 
              v-for="standard in esrsStandards" 
              :key="standard.id"
              :title="`${standard.code}: ${standard.name}`"
              :bordered="true"
              style="margin-bottom: 16px;"
            >
              <template #header-extra>
                <n-button 
                  type="primary" 
                  size="small"
                  @click="openEditPromptModal(standard)"
                >
                  <template #icon>
                    <n-icon :component="CreateOutline" />
                  </template>
                  Edit Prompt
                </n-button>
              </template>

              <n-space vertical :size="8">
                <n-text depth="3">{{ standard.description }}</n-text>
                
                <n-divider style="margin: 12px 0;" />
                
                <div>
                  <n-text strong>Current AI Prompt Template:</n-text>
                  <n-card 
                    :bordered="true" 
                    size="small" 
                    style="margin-top: 8px; background: rgba(255, 255, 255, 0.05);"
                  >
                    <n-text 
                      depth="2" 
                      style="white-space: pre-wrap; font-family: monospace; font-size: 13px;"
                    >
                      {{ standard.ai_prompt || 'No custom prompt configured. Using default system prompt.' }}
                    </n-text>
                  </n-card>
                </div>
              </n-space>
            </n-card>
          </n-space>
        </n-tab-pane>

        <!-- Disclosure Prompts Tab (Disclosure-level) -->
        <n-tab-pane name="disclosure-prompts" tab="📝 Disclosure Prompts">
          <n-space vertical :size="16">
            <n-alert type="info" :bordered="false">
              <strong>Per-Disclosure Custom Prompts:</strong> Configure unique AI prompts for individual disclosure requirements. 
              Custom prompts override the default requirement text during AI generation.
            </n-alert>

            <!-- Disclosure Selector -->
            <n-card title="Select Disclosure" :bordered="true">
              <n-select
                v-model:value="selectedDisclosureId"
                :options="allDisclosures.map(d => ({ label: d.display_label, value: d.id }))"
                placeholder="Select a disclosure to edit its prompt..."
                filterable
                @update:value="loadDisclosurePrompt"
              />
            </n-card>

            <!-- Prompt Editor (shows when disclosure selected) -->
            <n-card v-if="selectedDisclosureId && disclosurePromptData" title="AI Prompt Configuration" :bordered="true">
              <n-spin :show="loadingDisclosurePrompt">
                <n-space vertical :size="16">
                  <!-- Disclosure Info -->
                  <n-alert :type="disclosurePromptData.has_custom_prompt ? 'success' : 'default'" :bordered="false">
                    <strong>{{ disclosurePromptData.code }}</strong>: {{ disclosurePromptData.name }}
                    <n-tag 
                      v-if="disclosurePromptData.has_custom_prompt" 
                      type="success" 
                      size="small" 
                      style="margin-left: 8px;"
                    >
                      Custom Prompt Active
                    </n-tag>
                    <n-tag v-else type="default" size="small" style="margin-left: 8px;">
                      Using Default (Requirement Text)
                    </n-tag>
                  </n-alert>

                  <!-- Default Requirement Text (Read-only) -->
                  <div>
                    <n-text strong>Default Requirement Text (Read-only):</n-text>
                    <n-card size="small" style="margin-top: 8px; background: rgba(0, 0, 0, 0.05);" :bordered="true">
                      <n-text depth="2" style="white-space: pre-wrap;">
                        {{ disclosurePromptData.requirement_text }}
                      </n-text>
                    </n-card>
                  </div>

                  <n-divider />

                  <!-- Custom Prompt Editor -->
                  <div>
                    <n-space justify="space-between" align="center" style="margin-bottom: 8px;">
                      <n-text strong>Custom AI Prompt:</n-text>
                      <n-space>
                        <n-button 
                          size="small" 
                          @click="editingDisclosurePrompt = disclosurePromptData.requirement_text"
                        >
                          Copy Default
                        </n-button>
                        <n-button 
                          size="small" 
                          type="warning"
                          @click="resetDisclosurePrompt"
                          :loading="savingDisclosurePrompt"
                          v-if="disclosurePromptData.has_custom_prompt"
                        >
                          Reset to Default
                        </n-button>
                      </n-space>
                    </n-space>
                    
                    <n-input
                      v-model:value="editingDisclosurePrompt"
                      type="textarea"
                      placeholder="Enter custom AI prompt (leave empty to use default requirement text)..."
                      :rows="12"
                      style="font-family: monospace;"
                    />
                  </div>

                  <!-- Save Button -->
                  <n-space justify="end">
                    <n-button 
                      type="primary" 
                      @click="saveDisclosurePrompt"
                      :loading="savingDisclosurePrompt"
                    >
                      Save Custom Prompt
                    </n-button>
                  </n-space>

                  <!-- Help Text -->
                  <n-alert type="info" :bordered="false">
                    <strong>How it works:</strong>
                    <ul style="margin: 8px 0; padding-left: 20px;">
                      <li>If custom prompt is set, AI will use it instead of requirement_text</li>
                      <li>All linked documents will still be included automatically</li>
                      <li>User notes and manual answers are always included</li>
                      <li>Leave empty to use default requirement text</li>
                    </ul>
                  </n-alert>
                </n-space>
              </n-spin>
            </n-card>
          </n-space>
        </n-tab-pane>

        <!-- System Settings Tab -->
        <n-tab-pane name="settings" tab="⚙️ Settings">
          <n-space vertical :size="16">
            <n-card title="OpenAI Configuration" :bordered="true">
              <n-form label-placement="left" :label-width="200">
                <n-form-item label="Model">
                  <n-select
                    v-model:value="systemSettings.openai_model"
                    :options="[
                      { label: 'GPT-4', value: 'gpt-4' },
                      { label: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
                      { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
                    ]"
                  />
                </n-form-item>
                
                <n-form-item label="Temperature">
                  <n-slider 
                    v-model:value="systemSettings.temperature" 
                    :min="0" 
                    :max="1" 
                    :step="0.1"
                    :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                  />
                </n-form-item>
                
                <n-form-item label="Max Tokens">
                  <n-input-number 
                    v-model:value="systemSettings.max_tokens" 
                    :min="500" 
                    :max="4000" 
                    :step="100"
                  />
                </n-form-item>
              </n-form>
              
              <template #footer>
                <n-button type="primary" @click="saveSystemSettings">
                  Save Settings
                </n-button>
              </template>
            </n-card>
          </n-space>
        </n-tab-pane>

        <!-- RAG Metrics Tab -->
        <n-tab-pane name="rag" tab="🔍 RAG Metrics">
          <n-space vertical :size="16">
            <n-spin :show="loadingRAG">
              <!-- RAG Overview Cards -->
              <n-grid :cols="4" :x-gap="16" :y-gap="16">
                <n-grid-item>
                  <n-card title="Documents" :bordered="true" size="small">
                    <n-statistic :value="ragOverview.overview?.total_documents || 0">
                      <template #suffix>docs</template>
                    </n-statistic>
                    <div class="stat-meta">
                      {{ ragOverview.overview?.total_chunks || 0 }} chunks
                      ({{ ragOverview.overview?.avg_chunks_per_doc || 0 }} avg)
                    </div>
                  </n-card>
                </n-grid-item>

                <n-grid-item>
                  <n-card title="Hit Rate" :bordered="true" size="small">
                    <n-statistic :value="ragOverview.performance?.hit_rate || 0">
                      <template #suffix>%</template>
                    </n-statistic>
                    <div class="stat-meta">
                      MRR: {{ ragOverview.performance?.avg_mrr?.toFixed(3) || 0 }}
                    </div>
                  </n-card>
                </n-grid-item>

                <n-grid-item>
                  <n-card title="Avg Retrieval" :bordered="true" size="small">
                    <n-statistic :value="ragOverview.performance?.avg_retrieval_time_ms?.toFixed(1) || 0">
                      <template #suffix>ms</template>
                    </n-statistic>
                    <div class="stat-meta">
                      +{{ ragOverview.performance?.avg_reranking_time_ms?.toFixed(1) || 0 }}ms rerank
                    </div>
                  </n-card>
                </n-grid-item>

                <n-grid-item>
                  <n-card title="Context Quality" :bordered="true" size="small">
                    <n-statistic :value="((ragOverview.quality?.avg_context_relevance || 0) * 100).toFixed(1)">
                      <template #suffix>%</template>
                    </n-statistic>
                    <div class="stat-meta">
                      RAG Triad metric
                    </div>
                  </n-card>
                </n-grid-item>
              </n-grid>

              <!-- Embedding Models Table -->
              <n-card title="Embedding Models" :bordered="true">
                <n-data-table
                  :columns="embeddingColumns"
                  :data="embeddingModels"
                  :pagination="false"
                  size="small"
                />
              </n-card>

              <!-- RAG Quality Metrics -->
              <n-card title="RAG Triad Quality Metrics" :bordered="true">
                <n-space vertical :size="12">
                  <div>
                    <strong>Context Relevance:</strong> 
                    {{ ((ragOverview.quality?.avg_context_relevance || 0) * 100).toFixed(1) }}%
                    <n-progress
                      type="line"
                      :percentage="(ragOverview.quality?.avg_context_relevance || 0) * 100"
                      :show-indicator="false"
                      status="success"
                    />
                  </div>
                  <div>
                    <strong>Groundedness:</strong> 
                    {{ ((ragOverview.quality?.avg_groundedness || 0) * 100).toFixed(1) }}%
                    <n-progress
                      type="line"
                      :percentage="(ragOverview.quality?.avg_groundedness || 0) * 100"
                      :show-indicator="false"
                      status="info"
                    />
                  </div>
                  <div>
                    <strong>Answer Relevance:</strong> 
                    {{ ((ragOverview.quality?.avg_answer_relevance || 0) * 100).toFixed(1) }}%
                    <n-progress
                      type="line"
                      :percentage="(ragOverview.quality?.avg_answer_relevance || 0) * 100"
                      :show-indicator="false"
                      status="warning"
                    />
                  </div>
                </n-space>
              </n-card>
            </n-spin>
          </n-space>
        </n-tab-pane>

        <!-- User ESRS Progress Tab -->
        <n-tab-pane name="user-progress" tab="📊 User ESRS Progress">
          <n-space vertical :size="16">
            <n-card title="Select User" :bordered="true" size="small">
              <n-select
                v-model:value="selectedUserId"
                :options="userOptions"
                placeholder="Select a user to view ESRS progress"
                filterable
                @update:value="loadUserESRSProgress"
              />
            </n-card>

            <n-spin :show="loadingUserProgress">
              <div v-if="userESRSProgress">
                <!-- User Info -->
                <n-card title="User Information" :bordered="true" size="small">
                  <n-descriptions :column="3" bordered size="small">
                    <n-descriptions-item label="Email">
                      {{ userESRSProgress.user?.email }}
                    </n-descriptions-item>
                    <n-descriptions-item label="Company">
                      {{ userESRSProgress.user?.company_name || 'N/A' }}
                    </n-descriptions-item>
                    <n-descriptions-item label="Wizard">
                      <n-tag :type="userESRSProgress.user?.wizard_completed ? 'success' : 'warning'" size="small">
                        {{ userESRSProgress.user?.wizard_completed ? 'Completed' : 'Not Completed' }}
                      </n-tag>
                    </n-descriptions-item>
                  </n-descriptions>
                </n-card>

                <!-- Overall Progress -->
                <n-card title="Overall Progress" :bordered="true" style="margin-top: 16px;">
                  <n-space vertical :size="12">
                    <n-statistic label="Disclosures Answered" :value="userESRSProgress.overall?.total_answered || 0">
                      <template #suffix>/ {{ userESRSProgress.overall?.total_disclosures || 0 }}</template>
                    </n-statistic>
                    <n-progress
                      type="line"
                      :percentage="userESRSProgress.overall?.completion_percentage || 0"
                      status="success"
                    />
                    <div>
                      <strong>AI Usage:</strong> {{ userESRSProgress.overall?.total_ai_used || 0 }} 
                      ({{ userESRSProgress.overall?.ai_usage_percentage || 0 }}%)
                    </div>
                  </n-space>
                </n-card>

                <!-- By Standard -->
                <n-card title="Progress by ESRS Standard" :bordered="true" style="margin-top: 16px;">
                  <n-data-table
                    :columns="esrsStandardColumns"
                    :data="userESRSProgress.by_standard"
                    :pagination="false"
                    size="small"
                  />
                </n-card>

                <!-- Recent Activity -->
                <n-card title="Recent Activity" :bordered="true" style="margin-top: 16px;">
                  <n-timeline>
                    <n-timeline-item
                      v-for="(activity, idx) in userESRSProgress.recent_activity"
                      :key="idx"
                      :type="activity.has_ai_answer ? 'success' : 'info'"
                      :title="activity.disclosure__code"
                    >
                      {{ activity.disclosure__name_en?.substring(0, 80) }}{{ activity.disclosure__name_en?.length > 80 ? '...' : '' }}
                      <template #footer>
                        <n-space :size="4">
                          <n-tag size="small" v-if="activity.has_ai_answer" type="success">AI</n-tag>
                          <n-tag size="small" v-if="activity.has_manual_answer" type="info">Manual</n-tag>
                          <span class="text-muted">{{ formatDate(activity.updated_at) }}</span>
                        </n-space>
                      </template>
                    </n-timeline-item>
                  </n-timeline>
                </n-card>
              </div>
            </n-spin>
          </n-space>
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <!-- Edit Prompt Modal -->
    <n-modal
      v-model:show="showEditPromptModal"
      preset="card"
      title="Edit AI Prompt Template"
      :style="{ width: '900px' }"
      :bordered="false"
    >
      <n-space vertical :size="16" v-if="editingStandard">
        <n-alert type="warning" :bordered="false">
          ⚠️ Changes will affect all future AI answers for <strong>{{ editingStandard.code }}: {{ editingStandard.name }}</strong>
        </n-alert>

        <n-form-item label="Prompt Template">
          <n-input
            v-model:value="editingPrompt"
            type="textarea"
            placeholder="Enter custom AI prompt template..."
            :rows="15"
            style="font-family: monospace;"
          />
        </n-form-item>

        <n-alert type="info" :bordered="false">
          <strong>Available Variables:</strong>
          <ul style="margin: 8px 0; padding-left: 20px;">
            <li><code>{{"{{"}}DISCLOSURE_CODE{{"}}"}}</code> - Disclosure code (e.g., E1-1)</li>
            <li><code>{{"{{"}}DISCLOSURE_NAME{{"}}"}}</code> - Disclosure name</li>
            <li><code>{{"{{"}}REQUIREMENT_TEXT{{"}}"}}</code> - Full requirement text</li>
            <li><code>{{"{{"}}USER_NOTES{{"}}"}}</code> - User's notes</li>
            <li><code>{{"{{"}}MANUAL_ANSWER{{"}}"}}</code> - User's manual answer</li>
            <li><code>{{"{{"}}DOCUMENTS{{"}}"}}</code> - All document contents</li>
          </ul>
        </n-alert>
      </n-space>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showEditPromptModal = false">Cancel</n-button>
          <n-button type="primary" @click="savePrompt" :loading="savingPrompt">
            Save Prompt
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Add Standard to User Modal -->
    <n-modal
      v-model:show="showAddStandardModal"
      preset="dialog"
      title="Add Standard to User"
      positive-text="Add"
      negative-text="Cancel"
      @positive-click="addStandardToUser"
    >
      <n-space vertical :size="16">
        <n-alert type="info" :bordered="false">
          Add a compliance standard to <strong>{{ editingUser?.email }}</strong>
        </n-alert>
        
        <n-select
          v-model:value="selectedNewStandard"
          :options="availableStandards"
          placeholder="Select a standard"
        />
        
        <n-text depth="3" style="font-size: 12px;">
          Leave empty to allow all standards
        </n-text>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  useMessage,
  NCard,
  NH2,
  NButton,
  NIcon,
  NSpace,
  NTabs,
  NTabPane,
  NGrid,
  NGridItem,
  NStatistic,
  NDataTable,
  NAlert,
  NModal,
  NInput,
  NFormItem,
  NDivider,
  NText,
  NSelect,
  NSlider,
  NInputNumber,
  NForm,
  NTag,
  type DataTableColumns
} from 'naive-ui'
import {
  ArrowBackOutline,
  PeopleOutline,
  BusinessOutline,
  SparklesOutline,
  DocumentTextOutline,
  CreateOutline
} from '@vicons/ionicons5'
import api from '../services/api'

const message = useMessage()

// Statistics
const statistics = ref({
  total_users: 0,
  total_companies: 0,
  total_ai_answers: 0,
  total_documents: 0
})

// Users
const users = ref<any[]>([])
const loadingUsers = ref(false)

const userColumns: DataTableColumns<any> = [
  {
    title: 'Email',
    key: 'email'
  },
  {
    title: 'Company Type',
    key: 'company_type',
    render: (row) => {
      const typeMap: any = {
        'small': 'Small Company',
        'sme': 'SME',
        'large': 'Large Corporation'
      }
      return h(NTag, { type: 'info', size: 'small' }, { default: () => typeMap[row.company_type] || '-' })
    }
  },
  {
    title: 'Allowed Standards',
    key: 'allowed_standards',
    render: (row) => {
      const standards = row.allowed_standards || []
      if (standards.length === 0) {
        return h(NTag, { type: 'success', size: 'small' }, { default: () => 'All Standards' })
      }
      return h(NSpace, { size: 4 }, () => 
        standards.map((std: string) => 
          h(NTag, { 
            type: 'info', 
            size: 'small',
            closable: true,
            onClose: () => removeStandardFromUser(row.id, std)
          }, { 
            default: () => std === 'ESRS' ? '🌍 ESRS' : std === 'ISO9001' ? '🏆 ISO 9001' : std 
          })
        ).concat([
          h(NButton, {
            size: 'tiny',
            onClick: () => openAddStandardModal(row)
          }, { default: () => '+' })
        ])
      )
    }
  },
  {
    title: 'Wizard',
    key: 'wizard_completed',
    render: (row) => {
      return h(NTag, 
        { type: row.wizard_completed ? 'success' : 'warning', size: 'small' }, 
        { default: () => row.wizard_completed ? 'Completed' : 'Pending' }
      )
    }
  },
  {
    title: 'Documents',
    key: 'document_count',
    render: (row) => row.document_count || 0
  },
  {
    title: 'AI Answers',
    key: 'ai_answer_count',
    render: (row) => row.ai_answer_count || 0
  },
  {
    title: 'Joined',
    key: 'date_joined',
    render: (row) => new Date(row.date_joined).toLocaleDateString()
  }
]

// ESRS Standards & Prompts
const esrsStandards = ref<any[]>([])
const showEditPromptModal = ref(false)
const editingStandard = ref<any>(null)
const editingPrompt = ref('')
const savingPrompt = ref(false)

// Disclosure Prompts
const allDisclosures = ref<any[]>([])
const selectedDisclosureId = ref<number | null>(null)
const disclosurePromptData = ref<any>(null)
const editingDisclosurePrompt = ref('')
const savingDisclosurePrompt = ref(false)
const loadingDisclosurePrompt = ref(false)

// System Settings
const systemSettings = ref({
  openai_model: 'gpt-4',
  temperature: 0.7,
  max_tokens: 2000
})

// RAG Metrics
const loadingRAG = ref(false)
const ragOverview = ref<any>({})
const embeddingModels = ref<any[]>([])

// User Standards Management
const showAddStandardModal = ref(false)
const editingUser = ref<any>(null)
const availableStandards = [
  { value: 'ESRS', label: '🌍 ESRS Reporting' },
  { value: 'ISO9001', label: '🏆 ISO 9001:2015' }
]
const selectedNewStandard = ref<string | null>(null)

const embeddingColumns: DataTableColumns<any> = [
  {
    title: 'Name',
    key: 'name',
    render: (row) => h('div', {}, [
      h('div', { style: 'font-weight: 600' }, row.name),
      h('div', { style: 'font-size: 12px; color: #999' }, `${row.provider} • ${row.dimensions}D`)
    ])
  },
  {
    title: 'Cost/1M tokens',
    key: 'cost_per_million',
    render: (row) => `$${row.cost_per_million.toFixed(2)}`
  },
  {
    title: 'Performance',
    key: 'hit_rate',
    render: (row) => h('div', {}, [
      h('div', {}, `Hit Rate: ${(row.hit_rate * 100).toFixed(1)}%`),
      h('div', { style: 'font-size: 12px; color: #999' }, `${row.query_count} queries`)
    ])
  },
  {
    title: 'Status',
    key: 'is_active',
    render: (row) => {
      const isDefault = row.is_default
      return h(NSpace, {}, {
        default: () => [
          h(NTag, { 
            type: row.is_active ? 'success' : 'default', 
            size: 'small' 
          }, { default: () => row.is_active ? 'Active' : 'Inactive' }),
          isDefault ? h(NTag, { type: 'warning', size: 'small' }, { default: () => 'Default' }) : null
        ]
      })
    }
  },
  {
    title: 'Actions',
    key: 'actions',
    render: (row) => h(NSpace, {}, {
      default: () => [
        h(NButton, {
          size: 'small',
          type: row.is_active ? 'default' : 'primary',
          onClick: () => toggleModel(row.id)
        }, { default: () => row.is_active ? 'Deactivate' : 'Activate' }),
        !row.is_default ? h(NButton, {
          size: 'small',
          type: 'warning',
          onClick: () => setDefaultModel(row.id)
        }, { default: () => 'Set Default' }) : null
      ]
    })
  }
]

// User ESRS Progress
const selectedUserId = ref<number | null>(null)
const userOptions = ref<any[]>([])
const loadingUserProgress = ref(false)
const userESRSProgress = ref<any>(null)

const esrsStandardColumns: DataTableColumns<any> = [
  {
    title: 'Standard',
    key: 'standard_name',
    render: (row) => h('div', {}, [
      h('div', { style: 'font-weight: 600' }, row.standard_code),
      h('div', { style: 'font-size: 12px; color: #999' }, row.standard_name)
    ])
  },
  {
    title: 'Answered',
    key: 'answered_count',
    render: (row) => `${row.answered_count} / ${row.total_count}`
  },
  {
    title: 'Progress',
    key: 'completion_rate',
    render: (row) => h(NSpace, { vertical: true, size: 'small' }, {
      default: () => [
        h('div', { style: 'width: 200px; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden' }, [
          h('div', {
            style: `width: ${row.completion_rate}%; height: 100%; background: linear-gradient(90deg, #10b981, #34d399); transition: width 0.3s`
          })
        ]),
        h('div', { style: 'font-size: 12px; color: #666' }, `${row.completion_rate.toFixed(0)}%`)
      ]
    })
  },
  {
    title: 'AI Used',
    key: 'ai_used_count',
    render: (row) => h(NTag, { type: 'info', size: 'small' }, { default: () => row.ai_used_count })
  },
  {
    title: 'Manual Only',
    key: 'manual_only_count',
    render: (row) => h(NTag, { type: 'default', size: 'small' }, { default: () => row.manual_only_count })
  }
]

const loadStatistics = async () => {
  try {
    const response = await api.get('/admin/statistics')
    statistics.value = response.data
  } catch (error) {
    message.error('Failed to load statistics')
  }
}

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error) {
    message.error('Failed to load users')
  } finally {
    loadingUsers.value = false
  }
}

const loadESRSStandards = async () => {
  try {
    const response = await api.get('/esrs/standards')
    esrsStandards.value = response.data
  } catch (error) {
    message.error('Failed to load ESRS standards')
  }
}

const openEditPromptModal = (standard: any) => {
  editingStandard.value = standard
  editingPrompt.value = standard.ai_prompt || ''
  showEditPromptModal.value = true
}

const savePrompt = async () => {
  if (!editingStandard.value) return

  savingPrompt.value = true
  try {
    await api.post(`/admin/prompts/${editingStandard.value.id}`, {
      ai_prompt: editingPrompt.value
    })
    
    message.success('Prompt updated successfully')
    showEditPromptModal.value = false
    await loadESRSStandards()
  } catch (error) {
    message.error('Failed to save prompt')
  } finally {
    savingPrompt.value = false
  }
}

const saveSystemSettings = async () => {
  try {
    await api.post('/admin/settings', systemSettings.value)
    message.success('Settings saved successfully')
  } catch (error) {
    message.error('Failed to save settings')
  }
}

// Disclosure Prompt Functions
const loadAllDisclosures = async () => {
  try {
    // Load all categories and standards to get disclosures
    const response = await api.get('/esrs/structure')
    const categories = response.data
    
    const disclosures: any[] = []
    categories.forEach((category: any) => {
      category.standards.forEach((standard: any) => {
        standard.disclosures.forEach((disclosure: any) => {
          disclosures.push({
            ...disclosure,
            standard_code: standard.code,
            standard_name: standard.name,
            display_label: `${standard.code} - ${disclosure.code}: ${disclosure.name}`
          })
        })
      })
    })
    
    allDisclosures.value = disclosures
  } catch (error) {
    message.error('Failed to load disclosures')
  }
}

const loadDisclosurePrompt = async () => {
  if (!selectedDisclosureId.value) return
  
  loadingDisclosurePrompt.value = true
  try {
    const response = await api.get(`/admin/disclosure/${selectedDisclosureId.value}/prompt`)
    disclosurePromptData.value = response.data
    editingDisclosurePrompt.value = response.data.ai_prompt || response.data.requirement_text
  } catch (error) {
    message.error('Failed to load disclosure prompt')
  } finally {
    loadingDisclosurePrompt.value = false
  }
}

const saveDisclosurePrompt = async () => {
  if (!selectedDisclosureId.value) return
  
  savingDisclosurePrompt.value = true
  try {
    await api.put(`/admin/disclosure/${selectedDisclosureId.value}/prompt`, {
      ai_prompt: editingDisclosurePrompt.value
    })
    
    message.success('Disclosure prompt updated successfully')
    await loadDisclosurePrompt() // Reload to show updated status
  } catch (error) {
    message.error('Failed to save disclosure prompt')
  } finally {
    savingDisclosurePrompt.value = false
  }
}

const resetDisclosurePrompt = async () => {
  if (!selectedDisclosureId.value || !disclosurePromptData.value) return
  
  savingDisclosurePrompt.value = true
  try {
    await api.put(`/admin/disclosure/${selectedDisclosureId.value}/prompt`, {
      ai_prompt: '' // Empty string resets to default
    })
    
    message.success('Disclosure prompt reset to default')
    await loadDisclosurePrompt()
  } catch (error) {
    message.error('Failed to reset disclosure prompt')
  } finally {
    savingDisclosurePrompt.value = false
  }
}

// RAG Functions
const loadRAGOverview = async () => {
  loadingRAG.value = true
  try {
    const response = await api.get('/admin/rag/overview')
    ragOverview.value = response.data
  } catch (error) {
    message.error('Failed to load RAG overview')
  } finally {
    loadingRAG.value = false
  }
}

const loadEmbeddingModels = async () => {
  try {
    const response = await api.get('/admin/rag/embedding-models')
    embeddingModels.value = response.data
  } catch (error) {
    message.error('Failed to load embedding models')
  }
}

const toggleModel = async (modelId: number) => {
  try {
    await api.post(`/admin/rag/embedding-models/${modelId}/toggle`)
    message.success('Model status updated')
    await loadEmbeddingModels()
    await loadRAGOverview()
  } catch (error) {
    message.error('Failed to toggle model')
  }
}

const setDefaultModel = async (modelId: number) => {
  try {
    await api.post(`/admin/rag/embedding-models/${modelId}/set-default`)
    message.success('Default model updated')
    await loadEmbeddingModels()
    await loadRAGOverview()
  } catch (error) {
    message.error('Failed to set default model')
  }
}

// User ESRS Progress Functions
const loadUserESRSProgress = async (userId: number) => {
  if (!userId) return
  
  loadingUserProgress.value = true
  try {
    const response = await api.get(`/admin/users/${userId}/esrs-progress`)
    userESRSProgress.value = response.data
  } catch (error) {
    message.error('Failed to load user ESRS progress')
  } finally {
    loadingUserProgress.value = false
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

// User Standards Management Functions
const openAddStandardModal = (user: any) => {
  editingUser.value = user
  selectedNewStandard.value = null
  showAddStandardModal.value = true
}

const addStandardToUser = async () => {
  if (!editingUser.value || !selectedNewStandard.value) return
  
  const currentStandards = editingUser.value.allowed_standards || []
  if (currentStandards.includes(selectedNewStandard.value)) {
    message.warning('Standard already added')
    return
  }
  
  const updatedStandards = [...currentStandards, selectedNewStandard.value]
  
  try {
    await api.put(`/admin/users/${editingUser.value.id}/allowed-standards`, updatedStandards)
    message.success('Standard added successfully')
    showAddStandardModal.value = false
    await loadUsers() // Reload users
  } catch (error) {
    console.error('Failed to add standard:', error)
    message.error('Failed to add standard')
  }
}

const removeStandardFromUser = async (userId: number, standardToRemove: string) => {
  const user = users.value.find(u => u.id === userId)
  if (!user) return
  
  const updatedStandards = (user.allowed_standards || []).filter((s: string) => s !== standardToRemove)
  
  try {
    await api.put(`/admin/users/${userId}/allowed-standards`, updatedStandards)
    message.success('Standard removed successfully')
    await loadUsers() // Reload users
  } catch (error) {
    console.error('Failed to remove standard:', error)
    message.error('Failed to remove standard')
  }
}

onMounted(() => {
  loadStatistics()
  loadUsers()
  loadESRSStandards()
  loadAllDisclosures()
  loadRAGOverview()
  loadEmbeddingModels()
  
  // Load user options for dropdown
  loadUsers().then(() => {
    userOptions.value = users.value.map(u => ({
      label: u.email,
      value: u.id
    }))
  })
})
</script>

<style scoped>
.admin-container {
  padding: 24px;
  max-width: 1400px;
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

:deep(.n-statistic) {
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.n-statistic-value) {
  font-size: 32px;
  font-weight: bold;
}
</style>
