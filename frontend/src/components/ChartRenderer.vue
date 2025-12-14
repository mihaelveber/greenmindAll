<template>
  <div class="chart-renderer">
    <div v-if="chartData.type === 'bar'" class="chart-container">
      <Bar :data="barChartData" :options="barChartOptions" />
    </div>

    <div v-else-if="chartData.type === 'pie'" class="chart-container">
      <Pie :data="pieChartData" :options="pieChartOptions" />
    </div>

    <div v-else-if="chartData.type === 'line'" class="chart-container">
      <Line :data="lineChartData" :options="lineChartOptions" />
    </div>

    <div v-else class="chart-error">
      <n-alert type="error" title="Unknown Chart Type">
        Chart type "{{ chartData.type }}" is not supported.
      </n-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NAlert } from 'naive-ui'
import { Bar, Pie, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  LineElement,
  PointElement
} from 'chart.js'

// Register Chart.js components
ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  LineElement,
  PointElement
)

interface ChartDataPoint {
  label: string
  value: number
  color: string
}

interface ChartConfig {
  xlabel?: string
  ylabel?: string
  show_legend?: boolean
  show_values?: boolean
  colors?: string[]
}

interface ChartData {
  id: string
  type: 'bar' | 'pie' | 'line'
  category: string
  title: string
  data: ChartDataPoint[]
  config: ChartConfig
  selected_for_report: boolean
}

interface Props {
  chartData: ChartData
  width?: number
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  width: 600,
  height: 400
})

// Ensure data is array
const chartDataArray = computed(() => {
  const data = props.chartData.data
  if (!data) return []
  if (Array.isArray(data)) return data
  // If it's an object, convert to array
  if (typeof data === 'object') {
    return Object.entries(data).map(([label, value]) => ({
      label,
      value: typeof value === 'number' ? value : parseFloat(value as string) || 0,
      color: props.chartData.config?.colors?.[0] || '#8884d8'
    }))
  }
  return []
})

// Bar chart configuration
const barChartData = computed(() => ({
  labels: chartDataArray.value.map(d => d.label),
  datasets: [{
    label: props.chartData.title,
    data: chartDataArray.value.map(d => d.value),
    backgroundColor: chartDataArray.value.map(d => d.color || props.chartData.config?.colors?.[0] || '#8884d8')
  }]
}))

const barChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: props.chartData.config?.show_legend !== false
    },
    title: {
      display: true,
      text: props.chartData.title
    }
  },
  scales: {
    x: {
      title: {
        display: !!props.chartData.config?.xlabel,
        text: props.chartData.config?.xlabel || ''
      }
    },
    y: {
      title: {
        display: !!props.chartData.config?.ylabel,
        text: props.chartData.config?.ylabel || ''
      }
    }
  }
}))

// Pie chart configuration
const pieChartData = computed(() => ({
  labels: chartDataArray.value.map(d => d.label),
  datasets: [{
    data: chartDataArray.value.map(d => d.value),
    backgroundColor: chartDataArray.value.map(d => d.color || props.chartData.config?.colors?.[0] || '#8884d8')
  }]
}))

const pieChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: props.chartData.config?.show_legend !== false,
      position: 'right' as const
    },
    title: {
      display: true,
      text: props.chartData.title
    }
  }
}))

// Line chart configuration
const lineChartData = computed(() => ({
  labels: chartDataArray.value.map(d => d.label),
  datasets: [{
    label: props.chartData.title,
    data: chartDataArray.value.map(d => d.value),
    borderColor: props.chartData.config?.colors?.[0] || '#8884d8',
    backgroundColor: (props.chartData.config?.colors?.[0] || '#8884d8') + '33', // Add transparency
    tension: 0.4
  }]
}))

const lineChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: props.chartData.config?.show_legend !== false
    },
    title: {
      display: true,
      text: props.chartData.title
    }
  },
  scales: {
    x: {
      title: {
        display: !!props.chartData.config?.xlabel,
        text: props.chartData.config?.xlabel || ''
      }
    },
    y: {
      title: {
        display: !!props.chartData.config?.ylabel,
        text: props.chartData.config?.ylabel || ''
      }
    }
  }
}))
</script>

<style scoped>
.chart-renderer {
  width: 100%;
  padding: 1rem;
}

.chart-container {
  width: 100%;
  height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.chart-error {
  padding: 20px;
}
</style>
