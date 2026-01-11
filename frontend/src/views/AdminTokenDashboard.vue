<template>
  <div class="admin-token-dashboard">
    <n-page-header
      title="Token Usage & Cost Dashboard"
      subtitle="Monitor API usage, costs, and system performance"
    >
      <template #extra>
        <n-space>
          <n-tag type="info">
            <template #icon>
              <n-icon :component="PersonOutline" />
            </template>
            {{ totalUsers }} Users
          </n-tag>
          <n-tag type="warning">
            <template #icon>
              <n-icon :component="Flash" />
            </template>
            {{ formatNumber(totalTokens) }} Tokens
          </n-tag>
          <n-tag type="success">
            <template #icon>
              <n-icon :component="CashOutline" />
            </template>
            ${{ totalCost.toFixed(2) }}
          </n-tag>
        </n-space>
      </template>
    </n-page-header>

    <n-spin :show="loading">
      <n-space vertical :size="24" class="dashboard-content">
        <!-- Filters -->
        <n-card title="Filters">
          <n-space align="center">
            <n-select
              v-model:value="dateRange"
              :options="dateRangeOptions"
              style="width: 200px"
              @update:value="loadData"
            />
            <n-button @click="loadData" type="primary">
              <template #icon>
                <n-icon :component="Refresh" />
              </template>
              Refresh
            </n-button>
          </n-space>
        </n-card>

        <!-- Provider Breakdown -->
        <n-card title="💰 Cost by AI Provider">
          <n-grid :cols="3" :x-gap="16">
            <n-grid-item>
              <n-statistic label="🟢 OpenAI" :value="providerStats.openai.cost">
                <template #prefix>$</template>
                <template #suffix>
                  <n-text depth="3" style="font-size: 12px;">
                    {{ formatNumber(providerStats.openai.tokens) }} tokens
                  </n-text>
                </template>
              </n-statistic>
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="🟣 Anthropic" :value="providerStats.anthropic.cost">
                <template #prefix>$</template>
                <template #suffix>
                  <n-text depth="3" style="font-size: 12px;">
                    {{ formatNumber(providerStats.anthropic.tokens) }} tokens
                  </n-text>
                </template>
              </n-statistic>
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="🔵 Google" :value="providerStats.google.cost">
                <template #prefix>$</template>
                <template #suffix>
                  <n-text depth="3" style="font-size: 12px;">
                    {{ formatNumber(providerStats.google.tokens) }} tokens
                  </n-text>
                </template>
              </n-statistic>
            </n-grid-item>
          </n-grid>
        </n-card>

        <!-- Daily Costs Chart -->
        <n-card title="Daily Token Usage & Costs (Last {{ dateRange }} days)">
          <div ref="costsChartRef" style="height: 400px"></div>
        </n-card>

        <!-- Organizations Stats -->
        <n-card title="Organizations">
          <n-data-table
            :columns="orgColumns"
            :data="organizations"
            :pagination="{ pageSize: 10 }"
            :bordered="false"
          />
        </n-card>

        <!-- Users Stats -->
        <n-card title="Users">
          <n-data-table
            :columns="userColumns"
            :data="users"
            :pagination="{ pageSize: 15 }"
            :bordered="false"
          />
        </n-card>

        <!-- Recent API Calls -->
        <n-card title="Recent API Calls">
          <n-data-table
            :columns="tokenUsageColumns"
            :data="recentUsage"
            :pagination="{ pageSize: 20 }"
            :bordered="false"
          />
        </n-card>
      </n-space>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { 
  NPageHeader, NSpace, NCard, NDataTable, NTag, NIcon, NButton, NSelect, NSpin, 
  NGrid, NGridItem, NStatistic, NText, useMessage 
} from 'naive-ui'
import { PersonOutline, Flash, CashOutline, Refresh } from '@vicons/ionicons5'
import * as echarts from 'echarts'
import type { EChartsType } from 'echarts'
import adminService from '../services/adminService'
import type { OrganizationStats, UserTokenStats, TokenUsage, DailyCost } from '../services/adminService'

const message = useMessage()
const loading = ref(false)

// Data
const organizations = ref<OrganizationStats[]>([])
const users = ref<UserTokenStats[]>([])
const recentUsage = ref<TokenUsage[]>([])
const dailyCosts = ref<DailyCost[]>([])
const dateRange = ref(30)
const costsChartRef = ref<HTMLElement>()
let costsChart: EChartsType | null = null

// Date range options
const dateRangeOptions = [
  { label: 'Last 7 days', value: 7 },
  { label: 'Last 30 days', value: 30 },
  { label: 'Last 90 days', value: 90 },
  { label: 'Last 365 days', value: 365 }
]

// Computed totals
const totalUsers = computed(() => users.value.length)
const totalTokens = computed(() => users.value.reduce((sum, u) => sum + u.total_tokens, 0))
const totalCost = computed(() => users.value.reduce((sum, u) => sum + u.total_cost_usd, 0))

// Provider breakdown
const providerStats = computed(() => {
  const stats = {
    openai: { tokens: 0, cost: '0.00', calls: 0 },
    anthropic: { tokens: 0, cost: '0.00', calls: 0 },
    google: { tokens: 0, cost: '0.00', calls: 0 }
  }
  
  recentUsage.value.forEach((usage: any) => {
    const provider = usage.model_provider || 'openai'
    if (stats[provider as keyof typeof stats]) {
      stats[provider as keyof typeof stats].tokens += usage.total_tokens
      stats[provider as keyof typeof stats].cost = (
        parseFloat(stats[provider as keyof typeof stats].cost) + usage.cost_usd
      ).toFixed(2)
      stats[provider as keyof typeof stats].calls++
    }
  })
  
  return stats
})

// Table columns
const orgColumns = [
  {
    title: 'Organization',
    key: 'organization_email',
    width: 250
  },
  {
    title: 'Type',
    key: 'company_type',
    width: 150,
    render: (row: OrganizationStats) => row.company_type || 'N/A'
  },
  {
    title: 'Users',
    key: 'total_users',
    width: 100,
    sorter: (a: OrganizationStats, b: OrganizationStats) => a.total_users - b.total_users
  },
  {
    title: 'Tokens',
    key: 'total_tokens',
    width: 150,
    render: (row: OrganizationStats) => formatNumber(row.total_tokens),
    sorter: (a: OrganizationStats, b: OrganizationStats) => a.total_tokens - b.total_tokens
  },
  {
    title: 'Cost',
    key: 'total_cost_usd',
    width: 120,
    render: (row: OrganizationStats) => `$${row.total_cost_usd.toFixed(2)}`,
    sorter: (a: OrganizationStats, b: OrganizationStats) => a.total_cost_usd - b.total_cost_usd
  },
  {
    title: 'API Calls',
    key: 'api_calls_count',
    width: 120,
    sorter: (a: OrganizationStats, b: OrganizationStats) => a.api_calls_count - b.api_calls_count
  },
  {
    title: 'Created',
    key: 'created_at',
    width: 180,
    render: (row: OrganizationStats) => new Date(row.created_at).toLocaleDateString()
  }
]

const userColumns = [
  {
    title: 'Email',
    key: 'user_email',
    width: 250
  },
  {
    title: 'Role',
    key: 'role',
    width: 100,
    render: (row: UserTokenStats) => {
      const typeMap: Record<string, string> = {
        owner: 'info',
        admin: 'warning',
        member: 'default'
      }
      return h(NTag, { type: typeMap[row.role] as any }, () => row.role)
    }
  },
  {
    title: 'Tokens',
    key: 'total_tokens',
    width: 150,
    render: (row: UserTokenStats) => formatNumber(row.total_tokens),
    sorter: (a: UserTokenStats, b: UserTokenStats) => a.total_tokens - b.total_tokens
  },
  {
    title: 'Cost',
    key: 'total_cost_usd',
    width: 120,
    render: (row: UserTokenStats) => `$${row.total_cost_usd.toFixed(2)}`,
    sorter: (a: UserTokenStats, b: UserTokenStats) => a.total_cost_usd - b.total_cost_usd
  },
  {
    title: 'API Calls',
    key: 'api_calls_count',
    width: 100,
    sorter: (a: UserTokenStats, b: UserTokenStats) => a.api_calls_count - b.api_calls_count
  },
  {
    title: 'Last Activity',
    key: 'last_activity',
    width: 180,
    render: (row: UserTokenStats) => row.last_activity ? new Date(row.last_activity).toLocaleString() : 'Never'
  }
]

const tokenUsageColumns = [
  {
    title: 'Time',
    key: 'timestamp',
    width: 180,
    render: (row: TokenUsage) => new Date(row.timestamp).toLocaleString()
  },
  {
    title: 'User',
    key: 'user_email',
    width: 200,
    ellipsis: true
  },
  {
    title: 'Action',
    key: 'action_type',
    width: 130,
    render: (row: TokenUsage) => {
      const typeMap: Record<string, string> = {
        ai_answer: 'info',
        conversation: 'success',
        rag_search: 'warning',
        embedding: 'default'
      }
      return h(NTag, { type: typeMap[row.action_type] as any, size: 'small' }, () => row.action_type)
    }
  },
  {
    title: 'Model',
    key: 'model',
    width: 180,
    ellipsis: true,
    render: (row: TokenUsage) => {
      // Show provider icon + model name
      const provider = (row as any).model_provider || 'openai'
      const icons: Record<string, string> = {
        openai: '🟢',
        anthropic: '🟣',
        google: '🔵'
      }
      return `${icons[provider] || '⚪'} ${row.model}`
    }
  },
  {
    title: 'Tokens',
    key: 'total_tokens',
    width: 100,
    render: (row: TokenUsage) => formatNumber(row.total_tokens)
  },
  {
    title: 'Cost',
    key: 'cost_usd',
    width: 100,
    render: (row: TokenUsage) => `$${row.cost_usd.toFixed(6)}`
  },
  {
    title: 'Duration',
    key: 'request_duration_ms',
    width: 100,
    render: (row: TokenUsage) => row.request_duration_ms ? `${row.request_duration_ms}ms` : 'N/A'
  }
]

// Utility functions
function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num)
}

// Load data
async function loadData() {
  loading.value = true
  try {
    // Load all data in parallel
    const [orgsData, usersData, usageData, costsData] = await Promise.all([
      adminService.getOrganizationsWithStats({ days: dateRange.value }),
      adminService.getUsersWithStats({ days: dateRange.value }),
      adminService.getTokenUsage({ days: dateRange.value, limit: 100 }),
      adminService.getDailyCosts({ days: dateRange.value })
    ])

    organizations.value = orgsData
    users.value = usersData
    recentUsage.value = usageData
    dailyCosts.value = costsData

    // Update chart
    updateCostsChart()
    
    message.success('Data loaded successfully')
  } catch (error: any) {
    message.error('Failed to load data: ' + (error.response?.data?.error || error.message))
    console.error('Error loading admin data:', error)
  } finally {
    loading.value = false
  }
}

// Update costs chart
function updateCostsChart() {
  if (!costsChart || !costsChartRef.value) return

  const dates = dailyCosts.value.map(d => d.date)
  const costs = dailyCosts.value.map(d => d.total_cost_usd)
  const tokens = dailyCosts.value.map(d => d.total_tokens / 1000) // Convert to thousands

  costsChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['Cost ($)', 'Tokens (k)']
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: 'Cost ($)',
        position: 'left',
        axisLabel: {
          formatter: '${value}'
        }
      },
      {
        type: 'value',
        name: 'Tokens (k)',
        position: 'right',
        axisLabel: {
          formatter: '{value}k'
        }
      }
    ],
    series: [
      {
        name: 'Cost ($)',
        type: 'line',
        data: costs,
        smooth: true,
        itemStyle: {
          color: '#18a058'
        },
        areaStyle: {
          color: 'rgba(24, 160, 88, 0.1)'
        }
      },
      {
        name: 'Tokens (k)',
        type: 'bar',
        yAxisIndex: 1,
        data: tokens,
        itemStyle: {
          color: '#2080f0'
        }
      }
    ]
  })
}

onMounted(() => {
  // Initialize chart
  if (costsChartRef.value) {
    costsChart = echarts.init(costsChartRef.value)
    window.addEventListener('resize', () => {
      costsChart?.resize()
    })
  }

  // Load initial data
  loadData()
})
</script>

<style scoped>
.admin-token-dashboard {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.dashboard-content {
  margin-top: 24px;
}
</style>
