<template>
  <div class="version-tree-wrapper">
    <n-tabs type="line" animated>
      <!-- Tree View Tab -->
      <n-tab-pane name="tree" tab="🌳 Version Tree">
        <n-spin :show="loading">
          <div v-if="!loading && treeData.length === 0" class="empty-state">
            <n-empty description="No versions yet">
              <template #icon>
                <n-icon :component="GitBranchOutline" size="48" />
              </template>
            </n-empty>
          </div>
          
          <div v-else class="version-tree">
            <!-- Root version -->
            <div v-for="rootVersion in rootVersions" :key="rootVersion.id" class="version-branch">
              <VersionNode 
                :version="rootVersion" 
                :selected-version-id="selectedVersionId"
                :children="getChildren(rootVersion.id)"
                @select="handleSelectVersion"
                @view="handleViewVersion"
                @delete="handleDeleteVersion"
              />
            </div>
          </div>
        </n-spin>
      </n-tab-pane>
      
      <!-- Comparison View Tab -->
      <n-tab-pane name="compare" tab="🔀 Compare Versions">
        <VersionComparison :versions="treeData" />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NSpin, NEmpty, NIcon, NTabs, NTabPane, useMessage } from 'naive-ui'
import { GitBranchOutline } from '@vicons/ionicons5'
import VersionNode from './VersionNode.vue'
import VersionComparison from './VersionComparison.vue'
import api from '../services/api'

interface Version {
  id: string
  version_number: number
  change_type: string
  change_description: string
  content: any
  is_selected: boolean
  created_at: string
  created_by_user: boolean
  parent_version_id: string | null
  conversation_id: string | null
}

interface Props {
  itemType: string
  itemId: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'version-selected', versionId: string): void
  (e: 'view-version', version: Version): void
}>()

const message = useMessage()
const loading = ref(false)
const treeData = ref<Version[]>([])
const selectedVersionId = ref<string | null>(null)

const rootVersions = computed(() => {
  return treeData.value.filter(v => !v.parent_version_id)
})

const getChildren = (parentId: string): Version[] => {
  return treeData.value.filter(v => v.parent_version_id === parentId)
}

const loadVersions = async () => {
  loading.value = true
  try {
    const response = await api.get(`/versions/${props.itemType}/${props.itemId}`)
    treeData.value = response.data.versions
    
    // Find selected version
    const selected = treeData.value.find(v => v.is_selected)
    if (selected) {
      selectedVersionId.value = selected.id
    }
  } catch (error: any) {
    console.error('Failed to load versions:', error)
    message.error('Failed to load version history')
  } finally {
    loading.value = false
  }
}

const handleSelectVersion = async (versionId: string) => {
  try {
    await api.post('/versions/select', {
      version_id: versionId
    })
    
    selectedVersionId.value = versionId
    
    // Update is_selected flag locally
    treeData.value.forEach(v => {
      v.is_selected = v.id === versionId
    })
    
    message.success('Version selected! 🎯')
    emit('version-selected', versionId)
  } catch (error: any) {
    console.error('Failed to select version:', error)
    message.error('Failed to select version')
  }
}

const handleViewVersion = (version: Version) => {
  emit('view-version', version)
}

const handleDeleteVersion = async (versionId: string) => {
  try {
    await api.delete(`/versions/${versionId}`)
    
    // Remove from local tree
    const index = treeData.value.findIndex(v => v.id === versionId)
    if (index !== -1) {
      treeData.value.splice(index, 1)
    }
    
    message.success('Version deleted! 🗑️')
  } catch (error: any) {
    console.error('Failed to delete version:', error)
    const errorMsg = error.response?.data?.message || 'Failed to delete version'
    message.error(errorMsg)
  }
}

onMounted(() => {
  loadVersions()
})

defineExpose({
  loadVersions
})
</script>

<style scoped>
.version-tree-wrapper {
  padding: 16px;
  min-height: 300px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 48px;
}

.version-tree {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.version-branch {
  position: relative;
}
</style>
