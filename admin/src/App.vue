<template>
  <n-config-provider :theme="darkTheme">
    <n-message-provider>
      <n-notification-provider>
        <div class="admin-container">
          <n-layout has-sider>
            <n-layout-sider bordered :width="240" class="sidebar">
              <div class="logo">
                <n-gradient-text :size="24" type="success">
                  Greenmind Admin
                </n-gradient-text>
              </div>
              <n-menu
                v-model:value="activeKey"
                :options="menuOptions"
                @update:value="handleMenuUpdate"
              />
            </n-layout-sider>

            <n-layout>
              <n-layout-header bordered class="header">
                <n-h2>{{ pageTitle }}</n-h2>
              </n-layout-header>

              <n-layout-content content-style="padding: 24px;">
                <!-- Users Page -->
                <div v-if="activeKey === 'users'">
                  <n-card title="👥 User Management" :bordered="false">
                    <n-space vertical :size="16">
                      <n-input
                        v-model:value="searchQuery"
                        placeholder="Search users..."
                        clearable
                      >
                        <template #prefix>
                          <n-icon :component="SearchOutline" />
                        </template>
                      </n-input>
                      
                      <n-data-table
                        :columns="userColumns"
                        :data="filteredUsers"
                        :loading="loadingUsers"
                        :pagination="{ pageSize: 20 }"
                        striped
                      />
                    </n-space>
                  </n-card>
                </div>

                <!-- Analytics Page -->
                <div v-if="activeKey === 'analytics'">
                  <n-grid :cols="3" :x-gap="24" :y-gap="24">
                    <n-gi>
                      <n-card title="💰 Total Cost" :bordered="false">
                        <n-statistic :value="analytics.totalCost">
                          <template #prefix>$</template>
                        </n-statistic>
                      </n-card>
                    </n-gi>
                    <n-gi>
                      <n-card title="🔢 Total Tokens" :bordered="false">
                        <n-statistic :value="analytics.totalTokens" />
                      </n-card>
                    </n-gi>
                    <n-gi>
                      <n-card title="👥 Active Users" :bordered="false">
                        <n-statistic :value="analytics.activeUsers" />
                      </n-card>
                    </n-gi>
                  </n-grid>

                  <n-grid :cols="2" :x-gap="24" :y-gap="24" style="margin-top: 24px;">
                    <n-gi>
                      <n-card title="📈 Token Usage Over Time" :bordered="false">
                        <div style="height: 300px;">
                          <Line :data="lineChartData" :options="lineChartOptions" />
                        </div>
                      </n-card>
                    </n-gi>
                    <n-gi>
                      <n-card title="🥧 Usage by Model" :bordered="false">
                        <div style="height: 300px;">
                          <Pie :data="pieChartData" :options="pieChartOptions" />
                        </div>
                      </n-card>
                    </n-gi>
                  </n-grid>
                </div>
              </n-layout-content>
            </n-layout>
          </n-layout>

          <!-- Permissions Modal -->
          <n-modal
            v-model:show="showPermissionsModal"
            preset="card"
            title="📄 Manage Document Access"
            style="width: 600px;"
          >
            <template v-if="selectedUser">
              <n-alert type="info" :bordered="false" style="margin-bottom: 16px;">
                Managing document permissions for: <strong>{{ selectedUser.email }}</strong>
              </n-alert>
              
              <n-form>
                <n-form-item label="Allowed Standards">
                  <n-checkbox-group v-model:value="userPermissions">
                    <n-space vertical>
                      <n-checkbox
                        v-for="standard in availableStandards"
                        :key="standard.code"
                        :value="standard.code"
                        :label="`${standard.code} - ${standard.label.split(' - ')[1]}`"
                      />
                    </n-space>
                  </n-checkbox-group>
                </n-form-item>
                
                <n-alert type="warning" :bordered="false" style="margin-top: 16px;">
                  ⚠️ If no standards are selected, user will have access to ALL standards.
                </n-alert>
              </n-form>
            </template>

            <template #footer>
              <n-space justify="end">
                <n-button @click="showPermissionsModal = false">Cancel</n-button>
                <n-button type="primary" @click="savePermissions" :loading="savingPermissions">
                  Save Permissions
                </n-button>
              </n-space>
            </template>
          </n-modal>
        </div>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import {
  NConfigProvider,
  NMessageProvider,
  NNotificationProvider,
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NCard,
  NDataTable,
  NInput,
  NSpace,
  NGradientText,
  NH2,
  NIcon,
  NText,
  NTag,
  NStatistic,
  NGrid,
  NGi,
  NButton,
  NModal,
  NForm,
  NFormItem,
  NCheckbox,
  NCheckboxGroup,
  NAlert,
  createDiscreteApi,
  darkTheme,
  type MenuOption,
  type DataTableColumns
} from 'naive-ui'
import { PeopleOutline, BarChartOutline, SearchOutline } from '@vicons/ionicons5'
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line, Pie } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

const activeKey = ref('users')
const searchQuery = ref('')
const loadingUsers = ref(false)
const users = ref<any[]>([])
const analytics = ref({
  totalCost: 0,
  totalTokens: 0,
  activeUsers: 0
})

// Create discrete API for messages (works outside provider tree)
const { message } = createDiscreteApi(['message'], {
  configProviderProps: { theme: darkTheme }
})

// Permissions modal state
const showPermissionsModal = ref(false)
const selectedUser = ref<any>(null)
const userPermissions = ref<string[]>([])
const availableStandards = ref<any[]>([])
const savingPermissions = ref(false)
const dailyCosts = ref<any[]>([])
const modelUsage = ref<any[]>([])

const pageTitle = computed(() => {
  return activeKey.value === 'users' ? 'User Management' : 'Token Analytics'
})

const menuOptions: MenuOption[] = [
  {
    label: 'Users',
    key: 'users',
    icon: () => h(NIcon, { component: PeopleOutline })
  },
  {
    label: 'Analytics',
    key: 'analytics',
    icon: () => h(NIcon, { component: BarChartOutline })
  }
]

const userColumns: DataTableColumns<any> = [
  {
    title: 'ID',
    key: 'id',
    width: 60
  },
  {
    title: 'Email',
    key: 'email',
    width: 220
  },
  {
    title: 'Username',
    key: 'username',
    width: 120
  },
  {
    title: 'Company Type',
    key: 'company_type',
    width: 120,
    render: (row) => {
      const typeMap: any = {
        small: 'Small',
        sme: 'SME',
        large: 'Large'
      }
      return h(NTag, { type: 'info', size: 'small' }, { default: () => typeMap[row.company_type] || 'N/A' })
    }
  },
  {
    title: 'Wizard',
    key: 'wizard_completed',
    width: 80,
    render: (row) => h(NTag, { 
      type: row.wizard_completed ? 'success' : 'warning',
      size: 'small'
    }, { default: () => row.wizard_completed ? '✓' : '...' })
  },
  {
    title: 'Docs',
    key: 'document_count',
    width: 70,
    render: (row) => row.document_count || 0
  },
  {
    title: 'AI Answers',
    key: 'ai_answer_count',
    width: 90,
    render: (row) => row.ai_answer_count || 0
  },
  {
    title: 'Versions',
    key: 'version_count',
    width: 80,
    render: (row) => row.version_count || 0
  },
  {
    title: 'Created',
    key: 'date_joined',
    width: 160,
    render: (row) => row.date_joined ? new Date(row.date_joined).toLocaleDateString() : 'N/A'
  },
  {
    title: 'Active',
    key: 'is_active',
    width: 70,
    render: (row) => h(NTag, {
      type: row.is_active ? 'success' : 'error',
      size: 'small'
    }, { default: () => row.is_active ? '✓' : '✗' })
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 120,
    render: (row) => h(NButton, {
      size: 'small',
      type: 'primary',
      onClick: () => openPermissionsModal(row)
    }, { default: () => '📄 Manage Docs' })
  }
]

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(u => 
    u.email.toLowerCase().includes(query) || 
    (u.username && u.username.toLowerCase().includes(query))
  )
})

// Chart data
const lineChartData = computed(() => ({
  labels: dailyCosts.value.map(d => new Date(d.date).toLocaleDateString()),
  datasets: [{
    label: 'Daily Cost ($)',
    data: dailyCosts.value.map(d => d.total_cost_usd),
    borderColor: '#18a058',
    backgroundColor: 'rgba(24, 160, 88, 0.1)',
    tension: 0.4,
    fill: true
  }]
}))

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    title: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: any) => '$' + value.toFixed(2)
      }
    }
  }
}

const pieChartData = computed(() => ({
  labels: modelUsage.value.map(m => m.model_name),
  datasets: [{
    data: modelUsage.value.map(m => m.tokens),
    backgroundColor: [
      '#18a058',
      '#2080f0',
      '#f0a020',
      '#d03050',
      '#9333ea',
      '#06b6d4'
    ]
  }]
}))

const pieChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const
    }
  }
}

const handleMenuUpdate = (key: string) => {
  activeKey.value = key
}

const fetchUsers = async () => {
  loadingUsers.value = true
  try {
    const response = await axios.get('/api/admin/users')
    users.value = response.data
  } catch (error) {
    console.error('Error fetching users:', error)
    users.value = []
  } finally {
    loadingUsers.value = false
  }
}

const fetchAnalytics = async () => {
  try {
    const response = await axios.get('/api/admin/analytics/summary')
    analytics.value = {
      totalCost: response.data.total_cost_usd,
      totalTokens: response.data.total_tokens_used,
      activeUsers: response.data.active_users_30d
    }
  } catch (error) {
    console.error('Error fetching analytics:', error)
  }
}

const fetchDailyCosts = async () => {
  try {
    const response = await axios.get('/api/admin/costs/daily?days=30')
    dailyCosts.value = response.data
  } catch (error) {
    console.error('Error fetching daily costs:', error)
    dailyCosts.value = []
  }
}

const fetchModelUsage = async () => {
  try {
    const response = await axios.get('/api/admin/token-usage?days=30')
    // Aggregate by model
    const modelStats: any = {}
    response.data.forEach((usage: any) => {
      const model = usage.model
      if (!modelStats[model]) {
        modelStats[model] = { model_name: model, tokens: 0, cost: 0 }
      }
      modelStats[model].tokens += usage.total_tokens
      modelStats[model].cost += usage.cost_usd
    })
    modelUsage.value = Object.values(modelStats)
  } catch (error) {
    console.error('Error fetching model usage:', error)
    modelUsage.value = []
  }
}

// Permissions management functions
const fetchStandardTypes = async () => {
  try {
    const response = await axios.get('/api/admin/standard-types')
    availableStandards.value = response.data
  } catch (error) {
    console.error('Error fetching standard types:', error)
    message.error('Failed to load standard types')
  }
}

const openPermissionsModal = async (user: any) => {
  selectedUser.value = user
  showPermissionsModal.value = true
  
  // Fetch available standards if not loaded
  if (availableStandards.value.length === 0) {
    await fetchStandardTypes()
  }
  
  // Fetch user's current permissions
  try {
    const response = await axios.get(`/api/admin/users/${user.id}/permissions`)
    userPermissions.value = response.data.allowed_standards || []
  } catch (error) {
    console.error('Error fetching user permissions:', error)
    message.error('Failed to load user permissions')
    userPermissions.value = []
  }
}

const savePermissions = async () => {
  if (!selectedUser.value) return
  
  savingPermissions.value = true
  try {
    await axios.put(`/api/admin/users/${selectedUser.value.id}/permissions`, {
      allowed_standards: userPermissions.value
    })
    
    message.success(`Permissions updated for ${selectedUser.value.email}`)
    showPermissionsModal.value = false
    
    // Refresh users list to show updated permissions
    await fetchUsers()
  } catch (error) {
    console.error('Error saving permissions:', error)
    message.error('Failed to save permissions')
  } finally {
    savingPermissions.value = false
  }
}

onMounted(() => {
  fetchUsers()
  fetchAnalytics()
  fetchDailyCosts()
  fetchModelUsage()
})
</script>

<style scoped>
.admin-container {
  height: 100vh;
  background: #1a1a1a;
}

.sidebar {
  background: #1e1e1e;
  padding-top: 16px;
}

.logo {
  padding: 16px 24px;
  text-align: center;
  margin-bottom: 24px;
}

.header {
  padding: 16px 24px;
  background: #1e1e1e;
  display: flex;
  align-items: center;
}
</style>
