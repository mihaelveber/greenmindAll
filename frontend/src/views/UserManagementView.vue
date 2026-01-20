<template>
  <div class="user-management">
    <n-page-header class="page-header">
      <template #title>
        <h1>👥 Team Management</h1>
      </template>
      <template #subtitle>
        Manage team members, assign tasks, and track activity
      </template>
    </n-page-header>

    <!-- Statistics Cards -->
    <n-grid x-gap="16" y-gap="16" :cols="4" style="margin-bottom: 24px">
      <n-gi>
        <n-card :bordered="false" style="background: linear-gradient(135deg, #7A9E9F 0%, #427C89 100%)">
          <n-statistic label="Total Members" :value="teamMembers.length">
            <template #prefix>👥</template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card :bordered="false" style="background: linear-gradient(135deg, #68B3C8 0%, #3091B2 100%)">
          <n-statistic label="Active Assignments" :value="assignments.length">
            <template #prefix>📋</template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card :bordered="false" style="background: linear-gradient(135deg, #41B883 0%, #229863 100%)">
          <n-statistic
            label="Completion Rate"
            :value="completionRate"
            suffix="%"
          >
            <template #prefix>✅</template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card :bordered="false" style="background: linear-gradient(135deg, #F3BB45 0%, #BB992F 100%)">
          <n-statistic label="Pending Invites" :value="pendingInvitations.length">
            <template #prefix>📧</template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <n-tabs v-model:value="activeTab" type="line" animated>
      <!-- Team Members Tab -->
      <n-tab-pane name="members" tab="👥 Team Members">
        <n-space vertical :size="16">
          <!-- Search and Filters -->
          <n-card size="small">
            <n-space align="center" :size="12">
              <n-input
                v-model:value="memberSearchQuery"
                placeholder="🔍 Search by email..."
                clearable
                style="width: 300px"
              >
                <template #prefix>
                  <n-icon :component="SearchOutline" />
                </template>
              </n-input>
              <n-select
                v-model:value="memberRoleFilter"
                :options="[
                  { label: 'All Roles', value: 'all' },
                  { label: 'Admins Only', value: 'admin' },
                  { label: 'Members Only', value: 'member' }
                ]"
                placeholder="Filter by role"
                style="width: 160px"
                size="small"
              />
              <n-tag :bordered="false" type="info" size="small">
                {{ filteredMembers.length }} / {{ teamMembers.length }} members
              </n-tag>
            </n-space>
          </n-card>

          <n-card title="Active Team Members" class="section-card">
            <template #header-extra>
              <n-space>
                <n-button @click="fetchTeamMembers" :loading="loading" size="small">
                  🔄 Refresh
                </n-button>
                <n-button type="primary" @click="activeTab = 'invite'" size="small">
                  ➕ Invite Member
                </n-button>
              </n-space>
            </template>
            <n-data-table
              :columns="memberColumns"
              :data="filteredMembers"
              :loading="loading"
              :pagination="{ pageSize: 10 }"
              :row-key="(row: any) => row.id"
            />
          </n-card>

          <n-card title="📧 Pending Invitations" class="section-card">
            <template #header-extra>
              <n-button @click="fetchInvitations" :loading="loading" size="small">
                🔄 Refresh
              </n-button>
            </template>
            <n-data-table
              :columns="invitationColumns"
              :data="pendingInvitations"
              :loading="loading"
              :pagination="{ pageSize: 5 }"
              :row-key="(row: any) => row.id"
            />
            <n-empty
              v-if="pendingInvitations.length === 0 && !loading"
              description="No pending invitations"
              style="margin: 20px 0"
            />
          </n-card>
        </n-space>
      </n-tab-pane>

      <!-- Assignments Tab -->
      <n-tab-pane name="assignments" tab="📋 Assignments">
        <n-card title="Disclosure Assignments" class="section-card">
          <template #header-extra>
            <n-space>
              <n-input
                v-model:value="assignmentFilter"
                placeholder="Filter by user or code..."
                clearable
                style="width: 240px"
                size="small"
              >
                <template #prefix>
                  🔍
                </template>
              </n-input>
              <n-button @click="fetchAssignments" :loading="loading" size="small">
                🔄 Refresh
              </n-button>
              <n-button type="primary" @click="showAssignModal = true" size="small">
                ➕ New Assignment
              </n-button>
            </n-space>
          </template>
          <n-data-table
            :columns="assignmentColumns"
            :data="filteredAssignments"
            :loading="loading"
            :pagination="{ pageSize: 10 }"
            :row-key="(row: any) => row.id"
          />
          <n-empty
            v-if="filteredAssignments.length === 0 && !loading"
            description="No assignments found"
            style="margin: 20px 0"
          />
        </n-card>
      </n-tab-pane>

      <!-- Invite User Tab -->
      <n-tab-pane name="invite" tab="➕ Invite User">
        <n-card title="Invite New Team Member" class="section-card">
          <n-form ref="inviteFormRef" :model="inviteForm" :rules="inviteRules">
            <n-form-item label="Email Address" path="email">
              <n-input
                v-model:value="inviteForm.email"
                placeholder="user@example.com"
                @keydown.enter="handleInviteUser"
                size="large"
              />
            </n-form-item>
            <n-form-item label="Role" path="role">
              <n-select
                v-model:value="inviteForm.role"
                :options="roleOptions"
                placeholder="Select role"
                size="large"
              />
            </n-form-item>
            <n-form-item>
              <n-button
                type="primary"
                :loading="inviting"
                @click="handleInviteUser"
                size="large"
                block
              >
                📧 Send Invitation
              </n-button>
            </n-form-item>
          </n-form>

          <n-alert type="info" style="margin-top: 20px">
            <template #header>
              <n-space align="center">
                <n-icon size="20">💡</n-icon>
                <span>How Invitations Work</span>
              </n-space>
            </template>
            <n-space vertical :size="8" style="margin-top: 12px">
              <n-text>• User receives email with temporary password</n-text>
              <n-text>• They can log in immediately and change password</n-text>
              <n-text><strong>Admin:</strong> Full access, can invite users and assign tasks</n-text>
              <n-text><strong>Member:</strong> Can only work on assigned disclosures</n-text>
            </n-space>
          </n-alert>
        </n-card>
      </n-tab-pane>

      <!-- Activity Log Tab -->
      <n-tab-pane name="activity" tab="📊 Activity">
        <n-card title="Team Activity Log" class="section-card">
          <template #header-extra>
            <n-space>
              <n-select
                v-model:value="activityFilter"
                :options="activityFilterOptions"
                placeholder="Filter by action"
                clearable
                style="width: 200px"
                size="small"
              />
              <n-button @click="fetchActivity" :loading="loading" size="small">
                🔄 Refresh
              </n-button>
            </n-space>
          </template>
          
          <n-timeline v-if="filteredActivity.length > 0">
            <n-timeline-item
              v-for="(activity, idx) in filteredActivity"
              :key="idx"
              :type="getActivityType(activity.action)"
              :title="getActivityTitle(activity)"
              :time="formatDate(activity.timestamp)"
            >
              <n-space vertical :size="4">
                <n-text depth="3" style="font-size: 14px">
                  {{ getActivityDetails(activity) }}
                </n-text>
                <n-tag
                  v-if="activity.disclosure_code"
                  size="small"
                  type="info"
                  style="margin-top: 4px"
                >
                  {{ activity.disclosure_code }}
                </n-tag>
              </n-space>
            </n-timeline-item>
          </n-timeline>

          <n-empty
            v-if="filteredActivity.length === 0 && !loading"
            description="No activity recorded yet"
            style="margin: 40px 0"
          />
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <!-- Assignment Modal -->
    <n-modal v-model:show="showAssignModal" preset="card" title="📋 Assign Disclosure" style="width: 600px">
      <n-form ref="assignFormRef" :model="assignForm" :rules="assignRules">
        <n-form-item label="Disclosure Code" path="disclosure_code">
          <n-select
            v-model:value="assignForm.disclosure_code"
            :options="disclosureCodeOptions"
            placeholder="Select disclosure code"
            filterable
          />
        </n-form-item>
        <n-form-item label="Assign To" path="assigned_to_email">
          <n-select
            v-model:value="assignForm.assigned_to_email"
            :options="memberEmailOptions"
            placeholder="Select team member"
            filterable
          />
        </n-form-item>
        <n-form-item label="Notes (Optional)" path="notes">
          <n-input
            v-model:value="assignForm.notes"
            type="textarea"
            placeholder="Add instructions or deadline..."
            :rows="3"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAssignModal = false">Cancel</n-button>
          <n-button type="primary" @click="handleAssignTask" :loading="assigning">
            Assign Task
          </n-button>
      kov-Poglej   </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, useDialog } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { 
  NButton, 
  NTag, 
  NSpace,
  NTabs,
  NTabPane,
  NCard,
  NDataTable,
  NPageHeader,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NAlert,
  NTimeline,
  NTimelineItem,
  NEmpty,
  NGrid,
  NGi,
  NStatistic,
  NIcon,
  NText
} from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'
import api from '../services/api'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()

// State
const activeTab = ref('members')
const loading = ref(false)
const inviting = ref(false)
const assigning = ref(false)

// Data
const teamMembers = ref<any[]>([])
const pendingInvitations = ref<any[]>([])
const assignments = ref<any[]>([])
const activityLog = ref<any[]>([])

// Filters
const memberSearchQuery = ref('')
const memberRoleFilter = ref('all')
const assignmentFilter = ref('')
const activityFilter = ref('all')

const activityFilterOptions = [
  { label: 'All Actions', value: 'all' },
  { label: 'User Invited', value: 'user_invited' },
  { label: 'User Removed', value: 'user_removed' },
  { label: 'Role Changed', value: 'role_changed' },
  { label: 'Task Assigned', value: 'task_assigned' },
  { label: 'Task Unassigned', value: 'task_unassigned' }
]

// Computed
const completionRate = computed(() => {
  if (teamMembers.value.length === 0) return 0
  const totalTasks = teamMembers.value.reduce((sum, m) => sum + (m.assigned_tasks_count || 0), 0)
  const completedTasks = teamMembers.value.reduce((sum, m) => sum + (m.completed_assigned_tasks || 0), 0)
  if (totalTasks === 0) return 0
  return Math.round((completedTasks / totalTasks) * 100)
})

const filteredMembers = computed(() => {
  let filtered = teamMembers.value
  
  // Filter by search query
  if (memberSearchQuery.value) {
    const query = memberSearchQuery.value.toLowerCase()
    filtered = filtered.filter((m: any) => 
      m.email?.toLowerCase().includes(query)
    )
  }
  
  // Filter by role
  if (memberRoleFilter.value !== 'all') {
    filtered = filtered.filter((m: any) => m.role === memberRoleFilter.value)
  }
  
  return filtered
})

const filteredAssignments = computed(() => {
  if (!assignmentFilter.value) return assignments.value
  const filter = assignmentFilter.value.toLowerCase()
  return assignments.value.filter((a: any) => 
    a.disclosure_code?.toLowerCase().includes(filter) ||
    a.assigned_to_email?.toLowerCase().includes(filter) ||
    a.disclosure_name?.toLowerCase().includes(filter)
  )
})

const filteredActivity = computed(() => {
  if (activityFilter.value === 'all') return activityLog.value
  return activityLog.value.filter((log: any) => log.action === activityFilter.value)
})

// Forms
const inviteForm = ref({
  email: '',
  role: 'member'
})

const assignForm = ref({
  disclosure_code: '',
  assigned_to_email: '',
  notes: ''
})

const showAssignModal = ref(false)

// Options
const roleOptions = [
  { label: '👑 Admin - Full Access', value: 'admin' },
  { label: '👤 Member - Assigned Tasks Only', value: 'member' }
]

const memberEmailOptions = ref<any[]>([])
const disclosureCodeOptions = ref<any[]>([])

// Rules
const inviteRules = {
  email: [
    { required: true, message: 'Email is required', trigger: 'blur' },
    { type: 'email' as const, message: 'Invalid email format', trigger: 'blur' }
  ],
  role: [{ required: true, message: 'Role is required', trigger: 'change' }]
}

const assignRules = {
  disclosure_code: [{ required: true, message: 'Disclosure code is required', trigger: 'blur' }],
  assigned_to_email: [{ required: true, message: 'Please select a team member', trigger: 'change' }]
}

// Columns
const memberColumns: DataTableColumns<any> = [
  {
    title: 'Email',
    key: 'email',
    width: 250
  },
  {
    title: 'Role',
    key: 'role',
    width: 100,
    render: (row: any) => {
      return h(NTag, {
        type: row.role === 'admin' ? 'success' : 'info'
      }, { default: () => row.role === 'admin' ? '👑 Admin' : '👤 Member' })
    }
  },
  {
    title: 'Joined',
    key: 'joined_at',
    width: 150,
    render: (row: any) => formatDate(row.joined_at)
  },
  {
    title: 'Statistics',
    key: 'stats',
    render: (row: any) => {
      return h('div', [
        h('div', `📋 Assigned: ${row.assigned_tasks_count || 0}`),
        h('div', `✅ Completed: ${row.completed_assigned_tasks || 0} (${row.assigned_completion_percentage || 0}%)`)
      ])
    }
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 200,
    render: (row: any) => {
      return h(NSpace, {}, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'error',
            onClick: () => handleRemoveMember(row.id),
            disabled: row.is_organization_owner
          }, { default: () => '🗑️ Remove' }),
          h(NButton, {
            size: 'small',
            onClick: () => handleChangeRole(row.id, row.role === 'admin' ? 'member' : 'admin'),
            disabled: row.is_organization_owner
          }, { default: () => row.role === 'admin' ? '⬇️ Demote' : '⬆️ Promote' })
        ]
      })
    }
  }
]

const invitationColumns: DataTableColumns<any> = [
  { title: 'Email', key: 'email' },
  {
    title: 'Role',
    key: 'role',
    render: (row: any) => {
      return h(NTag, {
        type: row.role === 'admin' ? 'success' : 'info'
      }, { default: () => row.role })
    }
  },
  { title: 'Invited At', key: 'invited_at', render: (row: any) => formatDate(row.invited_at) },
  {
    title: 'Status',
    key: 'status',
    render: (row: any) => {
      return h(NTag, {
        type: row.status === 'pending' ? 'warning' : row.status === 'accepted' ? 'success' : 'error'
      }, { default: () => row.status })
    }
  },
  {
    title: 'Actions',
    key: 'actions',
    render: (row: any) => {
      return h(NButton, {
        size: 'small',
        type: 'error',
        onClick: () => handleCancelInvitation(row.id)
      }, { default: () => '❌ Cancel' })
    }
  }
]

const assignmentColumns: DataTableColumns<any> = [
  { title: 'Code', key: 'disclosure_code', width: 100 },
  { title: 'Title', key: 'disclosure_title', ellipsis: { tooltip: true } },
  { title: 'Assigned To', key: 'assigned_to_email', width: 200 },
  { title: 'Assigned By', key: 'assigned_by_email', width: 200 },
  { title: 'Date', key: 'assigned_at', width: 150, render: (row: any) => formatDate(row.assigned_at) },
  {
    title: 'Actions',
    key: 'actions',
    width: 120,
    render: (row: any) => {
      return h(NButton, {
        size: 'small',
        type: 'error',
        onClick: () => handleRemoveAssignment(row.id)
      }, { default: () => '🗑️ Remove' })
    }
  }
]

// Methods
async function fetchTeamMembers() {
  loading.value = true
  try {
    console.log('[UserManagement] Fetching team members...')
    const response = await api.get('/team/members')
    console.log('[UserManagement] Team members response:', response.data)
    teamMembers.value = response.data
    memberEmailOptions.value = teamMembers.value.map(m => ({
      label: `${m.email} (${m.role})`,
      value: m.email
    }))
  } catch (error: any) {
    console.error('[UserManagement] Error fetching team members:', error)
    message.error(error.response?.data?.message || 'Failed to fetch team members')
  } finally {
    loading.value = false
  }
}

async function fetchInvitations() {
  try {
    const response = await api.get('/team/invitations')
    pendingInvitations.value = response.data
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to fetch invitations')
  }
}

async function fetchAssignments() {
  try {
    const response = await api.get('/team/assignments')
    assignments.value = response.data
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to fetch assignments')
  }
}

async function fetchActivity() {
  loading.value = true
  try {
    const response = await api.get('/team/activity?limit=50')
    activityLog.value = response.data
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to fetch activity')
  } finally {
    loading.value = false
  }
}

async function fetchDisclosureCodes() {
  try {
    const response = await api.get('/esrs/disclosure-codes')
    // API now returns {value, label, standard} objects
    disclosureCodeOptions.value = response.data.map((item: any) => ({ 
      label: item.label, 
      value: item.value 
    }))
    console.log('Loaded disclosure codes:', response.data.length)
  } catch (error: any) {
    console.error('Failed to fetch disclosure codes:', error)
  }
}

async function handleInviteUser() {
  inviting.value = true
  try {
    await api.post('/team/invite', inviteForm.value)
    message.success(`Invitation sent to ${inviteForm.value.email}`)
    inviteForm.value = { email: '', role: 'member' }
    await fetchInvitations()
    await fetchTeamMembers()
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to invite user')
  } finally {
    inviting.value = false
  }
}

async function handleCancelInvitation(id: number) {
  try {
    await api.delete(`/team/invitations/${id}`)
    message.success('Invitation cancelled')
    await fetchInvitations()
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to cancel invitation')
  }
}

async function handleRemoveMember(id: number) {
  try {
    await api.delete(`/team/members/${id}`)
    message.success('Member removed')
    await fetchTeamMembers()
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to remove member')
  }
}

async function handleChangeRole(id: number, newRole: string) {
  const member = teamMembers.value.find((m: any) => m.id === id)
  if (!member) return
  
  const currentRole = member.role
  const memberEmail = member.email
  
  // Prepare dialog content based on role change
  let dialogContent = ''
  if (currentRole === 'admin' && newRole === 'member') {
    dialogContent = `Are you sure you want to demote ${memberEmail} from Admin to Member?\n\n` +
      `This will:\n` +
      `• Remove full access to all disclosures\n` +
      `• Restrict visibility to only assigned disclosures\n` +
      `• Remove ability to manage team members\n` +
      `• Remove ability to assign/unassign disclosures`
  } else if (currentRole === 'member' && newRole === 'admin') {
    dialogContent = `Are you sure you want to promote ${memberEmail} from Member to Admin?\n\n` +
      `This will grant:\n` +
      `• Full access to ALL disclosures\n` +
      `• Ability to manage team members (invite, remove, change roles)\n` +
      `• Ability to assign/unassign disclosures to any member\n` +
      `• Access to all documents and AI features`
  }
  
  dialog.warning({
    title: 'Confirm Role Change',
    content: dialogContent,
    positiveText: 'Yes, Change Role',
    negativeText: 'Cancel',
    onPositiveClick: async () => {
      try {
        await api.put(`/team/members/${id}/role?role=${newRole}`)
        message.success(`Role changed to ${newRole}`)
        await fetchTeamMembers()
      } catch (error: any) {
        message.error(error.response?.data?.message || 'Failed to change role')
      }
    }
  })
}

async function handleAssignTask() {
  assigning.value = true
  try {
    await api.post('/team/assign', assignForm.value)
    message.success('Task assigned successfully')
    assignForm.value = { disclosure_code: '', assigned_to_email: '', notes: '' }
    showAssignModal.value = false
    await fetchAssignments()
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to assign task')
  } finally {
    assigning.value = false
  }
}

async function handleRemoveAssignment(id: number) {
  try {
    await api.delete(`/team/assignments/${id}`)
    message.success('Assignment removed')
    await fetchAssignments()
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to remove assignment')
  }
}

function formatDate(dateString: string) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('sl-SI', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getActivityType(action: string) {
  const typeMap: Record<string, any> = {
    user_invite: 'info',
    user_remove: 'error',
    role_change: 'warning',
    assignment_change: 'success',
    ai_answer: 'info',
    manual_edit: 'default'
  }
  return typeMap[action] || 'default'
}

function getActivityTitle(activity: any) {
  const titleMap: Record<string, string> = {
    user_invite: '📧 User Invited',
    user_remove: '🗑️ User Removed',
    role_change: '🔄 Role Changed',
    assignment_change: '📋 Assignment Changed',
    ai_answer: '🤖 AI Answer Generated',
    manual_edit: '✏️ Manual Edit'
  }
  return `${titleMap[activity.action] || activity.action} by ${activity.user_email}`
}

function getActivityDetails(activity: any) {
  if (!activity.details) return 'No additional details'
  
  const details = activity.details
  
  // AI Answer details
  if (activity.action === 'ai_answer') {
    const parts = []
    if (details.confidence_score) parts.push(`Confidence: ${details.confidence_score}%`)
    if (details.chunks_used) parts.push(`Chunks: ${details.chunks_used}`)
    if (details.temperature) parts.push(`Temp: ${details.temperature}`)
    return parts.length > 0 ? parts.join(' • ') : 'AI answer generated'
  }
  
  // Assignment details
  if (activity.action === 'assignment_change') {
    if (details.action === 'created') return `Assigned to ${details.assigned_to}`
    if (details.action === 'updated') return `Reassigned to ${details.assigned_to}`
    if (details.action === 'removed') return `Assignment removed from ${details.assigned_to}`
  }
  
  // Role change details
  if (activity.action === 'role_change') {
    return `Changed from ${details.old_role} to ${details.new_role}`
  }
  
  // User invitation details
  if (activity.action === 'user_invite') {
    if (details.action === 'removed') return `Removed ${details.email}`
    if (details.action === 'role_changed') return `${details.email}: ${details.old_role} → ${details.new_role}`
    return `Invited ${details.email} as ${details.role}`
  }
  
  // Default: show disclosure code if available
  if (activity.disclosure_code) return `Disclosure: ${activity.disclosure_code}`
  
  return 'Action completed'
}

// Lifecycle
onMounted(() => {
  fetchTeamMembers()
  fetchInvitations()
  fetchAssignments()
  fetchActivity()
  fetchDisclosureCodes()
})
</script>

<style scoped lang="scss">
@import '../assets/sass/paper/variables';

.user-management {
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.section-card {
  margin-bottom: 20px;
}

h1 {
  font-size: 32px;
  font-weight: 300;
  color: $font-color;
  margin: 0;
}

// Style cards
:deep(.n-card) {
  background: $white-background-color;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
  border-radius: 20px;
  border: none;

  .n-card-header {
    padding: 20px 24px;
    border-bottom: 1px solid $medium-gray;

    .n-card-header__main {
      font-size: 18px;
      font-weight: 300;
      color: $font-color;
    }
  }

  .n-card__content {
    padding: 20px 24px;
  }
}

// Style statistic cards with gradients
:deep(.n-statistic) {
  .n-statistic-value {
    color: $white-color;
    font-size: 32px;
    font-weight: 300;
  }

  .n-statistic-value__prefix,
  .n-statistic-value__suffix {
    color: $white-color;
  }

  .n-statistic__label {
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
    font-weight: 500;
  }
}

// Style data tables
:deep(.n-data-table) {
  .n-data-table-th {
    background: $smoke-bg;
    color: $font-color;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    padding: 12px 16px;
  }

  .n-data-table-td {
    padding: 12px 16px;
    border-bottom: 1px solid $medium-gray;
  }

  .n-data-table-tr:hover {
    background: rgba(0, 0, 0, 0.02);
  }
}

// Style tabs
:deep(.n-tabs) {
  .n-tabs-nav {
    padding-left: 0;
  }

  .n-tabs-tab {
    font-size: 14px;
    font-weight: 600;
    padding: 12px 20px;
  }
}

// Style timeline
:deep(.n-timeline) {
  .n-timeline-item-timeline__line {
    background: $medium-gray;
  }

  .n-timeline-item-content__title {
    font-weight: 600;
    color: $font-color;
  }
}
</style>
