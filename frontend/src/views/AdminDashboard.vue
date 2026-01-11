<template>
  <div class="admin-dashboard">
    <n-page-header @back="handleBack">
      <template #title>
        <n-text type="primary">{{ t('admin.dashboard.title') }}</n-text>
      </template>
      <template #subtitle>
        {{ t('admin.dashboard.subtitle') }}
      </template>
    </n-page-header>

    <n-space vertical :size="24" style="margin-top: 24px">
      <!-- System Statistics -->
      <n-card :title="t('admin.statistics.title')">
        <n-spin :show="loadingStats">
          <n-grid x-gap="12" y-gap="12" cols="2 s:3 m:4 l:5" responsive="screen">
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.totalUsers')" :value="stats.total_users || 0" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.totalCompanies')" :value="stats.total_companies || 0" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.totalDocuments')" :value="stats.total_documents || 0" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.totalAiAnswers')" :value="stats.total_ai_answers || 0" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.totalVersions')" :value="stats.total_versions || 0" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.aiRefinements')" :value="stats.ai_refinements || 0">
                <template #suffix>
                  <n-text depth="3" style="font-size: 14px">AI</n-text>
                </template>
              </n-statistic>
            </n-grid-item>
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.manualEdits')" :value="stats.manual_edits || 0">
                <template #suffix>
                  <n-text depth="3" style="font-size: 14px">Manual</n-text>
                </template>
              </n-statistic>
            </n-grid-item>
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.totalConversations')" :value="stats.total_conversations || 0" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic :label="t('admin.statistics.activeUsers7Days')" :value="stats.active_users_7_days || 0">
                <template #suffix>
                  <n-text type="success" style="font-size: 14px">active</n-text>
                </template>
              </n-statistic>
            </n-grid-item>
          </n-grid>
        </n-spin>
      </n-card>

      <!-- Users Table -->
      <n-card :title="t('admin.users.title')">
        <n-spin :show="loadingUsers">
          <n-data-table
            :columns="userColumns"
            :data="users"
            :pagination="pagination"
            :row-key="(row) => row.id"
            striped
          />
        </n-spin>
      </n-card>

      <!-- User Details Modal -->
      <n-modal
        v-model:show="showUserDetails"
        preset="card"
        :title="selectedUser?.email || ''"
        style="width: 90%; max-width: 1200px"
        :segmented="{ content: 'soft' }"
      >
        <n-tabs type="line" animated v-if="selectedUser">
          <n-tab-pane name="ai-usage" :tab="t('admin.userDetails.aiUsage')">
            <n-spin :show="loadingUserDetails">
              <n-space vertical :size="16" v-if="userAiUsage">
                <n-grid x-gap="12" y-gap="12" cols="2 s:3 m:4" responsive="screen">
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.aiRefinementsTotal')" :value="userAiUsage.ai_refinements_total || 0" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.totalConversations')" :value="userAiUsage.total_conversations || 0" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.totalMessages')" :value="userAiUsage.total_messages || 0" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.estimatedTokens')" :value="userAiUsage.estimated_tokens || 0" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.estimatedCost')" :value="`$${userAiUsage.estimated_cost_usd || 0}`" />
                  </n-grid-item>
                </n-grid>

                <n-divider />

                <n-text strong>{{ t('admin.userDetails.refinementsByType') }}</n-text>
                <n-grid x-gap="12" y-gap="12" cols="2 s:4" responsive="screen">
                  <n-grid-item v-for="(count, type) in userAiUsage.refinements_by_type" :key="type">
                    <n-statistic :label="type" :value="String(count)" />
                  </n-grid-item>
                </n-grid>
              </n-space>
            </n-spin>
          </n-tab-pane>

          <n-tab-pane name="versions" :tab="t('admin.userDetails.versionStats')">
            <n-spin :show="loadingUserDetails">
              <n-space vertical :size="16" v-if="userVersionStats">
                <n-grid x-gap="12" y-gap="12" cols="2 s:3 m:4" responsive="screen">
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.totalVersions')" :value="userVersionStats.total_versions || 0" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.manualEdits')" :value="userVersionStats.manual_edits || 0" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.aiGenerated')" :value="userVersionStats.ai_generated || 0" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.itemsWithVersions')" :value="userVersionStats.items_with_versions || 0" />
                  </n-grid-item>
                  <n-grid-item>
                    <n-statistic :label="t('admin.userDetails.avgVersionsPerItem')" :value="userVersionStats.avg_versions_per_item || 0" />
                  </n-grid-item>
                </n-grid>

                <n-divider />

                <n-text strong>{{ t('admin.userDetails.versionsByType') }}</n-text>
                <n-grid x-gap="12" y-gap="12" cols="2 s:4" responsive="screen">
                  <n-grid-item v-for="(count, type) in userVersionStats.by_item_type" :key="type">
                    <n-statistic :label="type" :value="String(count)" />
                  </n-grid-item>
                </n-grid>

                <n-divider />

                <n-text strong>{{ t('admin.userDetails.versionsByChangeType') }}</n-text>
                <n-grid x-gap="12" y-gap="12" cols="2 s:3" responsive="screen">
                  <n-grid-item v-for="(count, type) in userVersionStats.by_change_type" :key="type">
                    <n-statistic :label="type" :value="String(count)" />
                  </n-grid-item>
                </n-grid>
              </n-space>
            </n-spin>
          </n-tab-pane>

          <n-tab-pane name="activity" :tab="t('admin.userDetails.activityTimeline')">
            <n-spin :show="loadingUserDetails">
              <div v-if="userActivity">
                <n-space vertical :size="12">
                  <n-text depth="3">
                    {{ t('admin.userDetails.showingLast') }} {{ userActivity.date_range.days }} {{ t('admin.userDetails.days') }}
                  </n-text>

                  <n-timeline>
                    <n-timeline-item
                      v-for="(item, index) in userActivity.timeline"
                      :key="index"
                      :type="getActivityType(item.type)"
                      :title="formatActivityTitle(item)"
                      :time="formatActivityTime(item.timestamp)"
                    >
                      <n-text depth="3" style="font-size: 13px">
                        {{ formatActivityDetails(item) }}
                      </n-text>
                    </n-timeline-item>
                  </n-timeline>

                  <n-empty v-if="userActivity.timeline.length === 0" :description="t('admin.userDetails.noActivity')" />
                </n-space>
              </div>
            </n-spin>
          </n-tab-pane>
        </n-tabs>
      </n-modal>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NPageHeader,
  NCard,
  NSpace,
  NSpin,
  NGrid,
  NGridItem,
  NStatistic,
  NText,
  NDataTable,
  NModal,
  NTabs,
  NTabPane,
  NDivider,
  NTimeline,
  NTimelineItem,
  NEmpty,
  NButton,
  NTag,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import api from '../services/api'

const { t } = useI18n()
const router = useRouter()
const message = useMessage()

const loadingStats = ref(false)
const loadingUsers = ref(false)
const loadingUserDetails = ref(false)

const stats = ref<any>({})
const users = ref<any[]>([])

const showUserDetails = ref(false)
const selectedUser = ref<any>(null)
const userAiUsage = ref<any>(null)
const userVersionStats = ref<any>(null)
const userActivity = ref<any>(null)

const pagination = ref({
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100]
})

const userColumns: DataTableColumns<any> = [
  {
    title: t('admin.users.email'),
    key: 'email',
    fixed: 'left' as const,
    width: 250
  },
  {
    title: t('admin.users.companyType'),
    key: 'company_type',
    width: 150,
    render: (row) => row.company_type || '-'
  },
  {
    title: t('admin.users.wizardCompleted'),
    key: 'wizard_completed',
    width: 120,
    render: (row) => h(NTag, { 
      type: row.wizard_completed ? 'success' : 'default',
      size: 'small'
    }, { default: () => row.wizard_completed ? 'Yes' : 'No' })
  },
  {
    title: t('admin.users.isActive'),
    key: 'is_active',
    width: 100,
    render: (row) => h(NTag, { 
      type: row.is_active ? 'success' : 'error',
      size: 'small'
    }, { default: () => row.is_active ? 'Active' : 'Inactive' })
  },
  {
    title: t('admin.users.documents'),
    key: 'document_count',
    width: 100,
    sorter: (a, b) => a.document_count - b.document_count
  },
  {
    title: t('admin.users.aiAnswers'),
    key: 'ai_answer_count',
    width: 100,
    sorter: (a, b) => a.ai_answer_count - b.ai_answer_count
  },
  {
    title: t('admin.users.versions'),
    key: 'version_count',
    width: 100,
    sorter: (a, b) => a.version_count - b.version_count
  },
  {
    title: t('admin.users.aiRefinements'),
    key: 'ai_refinement_count',
    width: 120,
    sorter: (a, b) => a.ai_refinement_count - b.ai_refinement_count
  },
  {
    title: t('admin.users.joinedAt'),
    key: 'date_joined',
    width: 180,
    render: (row) => new Date(row.date_joined).toLocaleString()
  },
  {
    title: t('admin.users.actions'),
    key: 'actions',
    fixed: 'right' as const,
    width: 120,
    render: (row) => h(
      NButton,
      {
        size: 'small',
        onClick: () => viewUserDetails(row)
      },
      { default: () => t('admin.users.viewDetails') }
    )
  }
]

const handleBack = () => {
  router.push('/reports')
}

const loadStatistics = async () => {
  loadingStats.value = true
  try {
    const response = await api.get('/admin/statistics')
    stats.value = response.data
  } catch (error: any) {
    console.error('Error loading statistics:', error)
    message.error(t('admin.errors.loadStatistics'))
  } finally {
    loadingStats.value = false
  }
}

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error: any) {
    console.error('Error loading users:', error)
    message.error(t('admin.errors.loadUsers'))
  } finally {
    loadingUsers.value = false
  }
}

const viewUserDetails = async (user: any) => {
  selectedUser.value = user
  showUserDetails.value = true
  
  loadingUserDetails.value = true
  try {
    // Load all user details in parallel
    const [aiUsageRes, versionStatsRes, activityRes] = await Promise.all([
      api.get(`/admin/users/${user.id}/ai-usage`),
      api.get(`/admin/users/${user.id}/version-stats`),
      api.get(`/admin/users/${user.id}/activity-timeline?days=30`)
    ])
    
    userAiUsage.value = aiUsageRes.data
    userVersionStats.value = versionStatsRes.data
    userActivity.value = activityRes.data
  } catch (error: any) {
    console.error('Error loading user details:', error)
    message.error(t('admin.errors.loadUserDetails'))
  } finally {
    loadingUserDetails.value = false
  }
}

const getActivityType = (type: string) => {
  switch (type) {
    case 'version': return 'info'
    case 'response': return 'success'
    case 'document': return 'warning'
    default: return 'default'
  }
}

const formatActivityTitle = (item: any) => {
  switch (item.type) {
    case 'version':
      return `${item.data.change_type} - ${item.data.item_type}`
    case 'response':
      return `Response: ${item.data.disclosure_code}`
    case 'document':
      return `Document: ${item.data.file_name}`
    default:
      return item.type
  }
}

const formatActivityDetails = (item: any) => {
  switch (item.type) {
    case 'version':
      return `v${item.data.version_number} by ${item.data.created_by}`
    case 'response':
      const parts = []
      if (item.data.has_ai_answer) parts.push('AI')
      if (item.data.has_manual_answer) parts.push('Manual')
      return parts.join(' + ')
    case 'document':
      return 'Uploaded'
    default:
      return ''
  }
}

const formatActivityTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

onMounted(() => {
  loadStatistics()
  loadUsers()
})
</script>

<style scoped>
.admin-dashboard {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

:deep(.n-data-table) {
  font-size: 13px;
}

:deep(.n-statistic .n-statistic-value__content) {
  font-size: 24px;
}
</style>
