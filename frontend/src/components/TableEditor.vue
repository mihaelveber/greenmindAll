<template>
  <div class="table-editor-wrapper">
    <n-space vertical :size="16">
      <!-- Toolbar -->
      <n-space justify="space-between">
        <n-space>
          <n-button type="primary" @click="addRow" ghost>
            <template #icon>
              <n-icon :component="AddOutline" />
            </template>
            Add Row
          </n-button>
          <n-button type="primary" @click="addColumn" ghost>
            <template #icon>
              <n-icon :component="AddOutline" />
            </template>
            Add Column
          </n-button>
          <n-button @click="removeLastRow" :disabled="localData.length <= 1">
            Remove Last Row
          </n-button>
          <n-button @click="removeLastColumn" :disabled="columns.length <= 2">
            Remove Last Column
          </n-button>
        </n-space>
        <n-space>
          <n-button @click="exportCSV">
            <template #icon>
              <n-icon :component="DownloadOutline" />
            </template>
            Export CSV
          </n-button>
          <n-upload
            :custom-request="importCSV"
            :show-file-list="false"
            accept=".csv"
          >
            <n-button>
              <template #icon>
                <n-icon :component="CloudUploadOutline" />
              </template>
              Import CSV
            </n-button>
          </n-upload>
        </n-space>
      </n-space>

      <!-- Table -->
      <div class="table-container">
        <n-data-table
          :columns="editableColumns"
          :data="localData"
          :pagination="false"
          :max-height="500"
          :bordered="true"
          striped
          :row-key="(row: any) => row.id"
        />
      </div>

      <!-- Style Options -->
      <n-card title="🎨 Table Styling" size="small">
        <n-form label-placement="left" label-width="140px">
          <n-form-item label="Table Title">
            <n-input
              v-model:value="tableConfig.title"
              placeholder="Enter table title..."
            />
          </n-form-item>
          <n-form-item label="Show Borders">
            <n-switch v-model:value="tableConfig.bordered" />
          </n-form-item>
          <n-form-item label="Striped Rows">
            <n-switch v-model:value="tableConfig.striped" />
          </n-form-item>
          <n-form-item label="Compact Size">
            <n-switch v-model:value="tableConfig.compact" />
          </n-form-item>
        </n-form>
      </n-card>

      <!-- Actions -->
      <n-divider />
      <n-space justify="end">
        <n-button @click="handleCancel">
          Cancel
        </n-button>
        <n-button type="primary" @click="handleSave">
          💾 Save Table
        </n-button>
      </n-space>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { NInput, useMessage } from 'naive-ui'
import { AddOutline, DownloadOutline, CloudUploadOutline } from '@vicons/ionicons5'

interface TableConfig {
  title: string
  bordered: boolean
  striped: boolean
  compact: boolean
}

interface Props {
  tableData?: any
}

interface Emits {
  (e: 'save', data: any): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const message = useMessage()

// Local state
const localData = ref<any[]>([])
const columns = ref<string[]>(['Column 1', 'Column 2', 'Column 3'])
const tableConfig = ref<TableConfig>({
  title: 'Data Table',
  bordered: true,
  striped: true,
  compact: false
})

// Initialize from props
const initializeData = () => {
  if (props.tableData) {
    const { title, headers, rows } = props.tableData
    
    tableConfig.value.title = title || 'Data Table'
    
    if (headers && Array.isArray(headers)) {
      columns.value = headers
    }
    
    if (rows && Array.isArray(rows)) {
      localData.value = rows.map((row: any, idx: number) => ({
        id: idx + 1,
        ...row
      }))
    }
  } else {
    // Default data
    localData.value = [
      { id: 1, 'Column 1': 'Data 1', 'Column 2': 'Data 2', 'Column 3': 'Data 3' },
      { id: 2, 'Column 1': 'Data 4', 'Column 2': 'Data 5', 'Column 3': 'Data 6' },
      { id: 3, 'Column 1': 'Data 7', 'Column 2': 'Data 8', 'Column 3': 'Data 9' }
    ]
  }
}

initializeData()

// Editable columns
const editableColumns = computed(() => {
  return [
    {
      title: '#',
      key: 'id',
      width: 60,
      fixed: 'left' as const
    },
    ...columns.value.map((col, colIndex) => ({
      title: col,
      key: col,
      render: (row: any, rowIndex: number) => {
        return h(NInput, {
          value: row[col] || '',
          onUpdateValue: (val: string) => {
            localData.value[rowIndex][col] = val
          },
          placeholder: `Enter ${col.toLowerCase()}...`,
          size: tableConfig.value.compact ? 'small' : 'medium'
        })
      }
    }))
  ]
})

// Actions
const addRow = () => {
  const newId = Math.max(...localData.value.map(d => d.id), 0) + 1
  const newRow: any = { id: newId }
  
  columns.value.forEach(col => {
    newRow[col] = ''
  })
  
  localData.value.push(newRow)
  message.success('Row added')
}

const addColumn = () => {
  const newColName = `Column ${columns.value.length + 1}`
  columns.value.push(newColName)
  
  localData.value.forEach(row => {
    row[newColName] = ''
  })
  
  message.success('Column added')
}

const removeLastRow = () => {
  if (localData.value.length > 1) {
    localData.value.pop()
    message.success('Row removed')
  } else {
    message.warning('Table must have at least one row')
  }
}

const removeLastColumn = () => {
  if (columns.value.length > 1) {
    const removedCol = columns.value.pop()
    
    if (removedCol) {
      localData.value.forEach(row => {
        delete row[removedCol]
      })
    }
    
    message.success('Column removed')
  } else {
    message.warning('Table must have at least one column')
  }
}

const exportCSV = () => {
  try {
    // Create CSV content
    const headers = columns.value.join(',')
    const rows = localData.value.map(row => {
      return columns.value.map(col => {
        const value = row[col] || ''
        // Escape commas and quotes
        return `"${String(value).replace(/"/g, '""')}"`
      }).join(',')
    }).join('\n')
    
    const csv = headers + '\n' + rows
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `${tableConfig.value.title.replace(/\s+/g, '_')}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    message.success('CSV exported successfully')
  } catch (error) {
    console.error('Export failed:', error)
    message.error('Failed to export CSV')
  }
}

const importCSV = ({ file }: any) => {
  const reader = new FileReader()
  
  reader.onload = (e) => {
    try {
      const csv = e.target?.result as string
      const lines = csv.split('\n').filter(line => line.trim())
      
      if (lines.length < 2) {
        message.error('CSV file must have headers and at least one data row')
        return
      }
      
      // Parse headers
      const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
      columns.value = headers
      
      // Parse data
      const data = lines.slice(1).map((line, idx) => {
        const values = line.split(',').map(v => v.trim().replace(/^"|"$/g, ''))
        const row: any = { id: idx + 1 }
        
        headers.forEach((header, i) => {
          row[header] = values[i] || ''
        })
        
        return row
      })
      
      localData.value = data
      message.success(`CSV imported: ${data.length} rows, ${headers.length} columns`)
    } catch (error) {
      console.error('Import failed:', error)
      message.error('Failed to import CSV. Please check file format.')
    }
  }
  
  reader.readAsText(file.file)
}

const handleSave = () => {
  const tableData = {
    title: tableConfig.value.title,
    headers: columns.value,
    rows: localData.value.map(row => {
      const { id, ...data } = row
      return data
    }),
    config: {
      bordered: tableConfig.value.bordered,
      striped: tableConfig.value.striped,
      compact: tableConfig.value.compact
    }
  }
  
  emit('save', tableData)
  message.success('Table saved successfully')
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
.table-editor-wrapper {
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  min-height: 400px;
}

.table-container {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.n-data-table) {
  border-radius: 6px;
}

:deep(.n-data-table-th) {
  background: linear-gradient(135deg, rgba(84, 217, 68, 0.15) 0%, rgba(84, 217, 68, 0.25) 100%);
  font-weight: 600;
  color: #54d944;
  font-size: 13px;
}

:deep(.n-data-table-td) {
  transition: background 0.2s ease;
  padding: 8px 12px;
}

:deep(.n-data-table-tr:hover .n-data-table-td) {
  background: rgba(84, 217, 68, 0.05);
}

:deep(.n-input) {
  transition: all 0.2s ease;
}

:deep(.n-input:focus-within) {
  box-shadow: 0 0 0 2px rgba(84, 217, 68, 0.2);
}

:deep(.n-card__header) {
  background: linear-gradient(135deg, rgba(84, 217, 68, 0.05) 0%, rgba(84, 217, 68, 0.1) 100%);
  font-weight: 600;
  color: #54d944;
}

/* Animation */
.table-editor-wrapper {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Button hover effects */
:deep(.n-button) {
  transition: all 0.2s ease;
}

:deep(.n-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(84, 217, 68, 0.3);
}
</style>
