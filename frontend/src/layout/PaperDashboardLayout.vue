<template>
  <div class="wrapper" :class="{ 'nav-open': showSidebar }">
    <side-bar
      :background-color="sidebarBackground"
      :active-color="sidebarActiveColor"
    >
      <template #links>
        <sidebar-link to="/dashboard" name="Dashboard" icon="ti-panel" />
        <sidebar-link
          v-for="standard in standardTypes"
          :key="standard.type"
          :to="`/standards/${standard.type}`"
          :name="`${standard.icon} ${standard.name}`"
          icon="ti-clipboard"
        />
        <sidebar-link to="/documents" name="Documents" icon="ti-folder" />
        <sidebar-link v-if="canManageTeam" to="/team" name="Team" icon="ti-user" />
      </template>
    </side-bar>
    <div class="main-panel">
      <top-navbar
        @toggle-sidebar="toggleSidebar"
        :user="authStore.user"
      >
        <template #actions>
          <LanguageSelector />
          <n-dropdown :options="userDropdownOptions" @select="handleUserAction">
            <n-button text>
              <template #icon>
                <div style="font-size: 28px; line-height: 32px;">
                  {{ getAvatarEmoji(selectedAvatar) }}
                </div>
              </template>
              {{ authStore.user?.username }}
            </n-button>
          </n-dropdown>
        </template>
      </top-navbar>

      <div class="content" @click="closeSidebar">
        <div class="container-fluid">
          <transition name="fade" mode="out-in">
            <router-view></router-view>
          </transition>
        </div>
      </div>

      <content-footer></content-footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { NDropdown, NButton, useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth.store'
import SideBar from '@/components/paper/SidebarPlugin/SideBar.vue'
import SidebarLink from '@/components/paper/SidebarPlugin/SidebarLink.vue'
import TopNavbar from './dashboard/TopNavbar.vue'
import ContentFooter from './dashboard/ContentFooter.vue'
import LanguageSelector from '@/components/LanguageSelector.vue'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

const showSidebar = ref(false)
const sidebarBackground = ref('black')
const sidebarActiveColor = ref('success')
const standardTypes = ref<any[]>([])
const selectedAvatar = ref(localStorage.getItem('userAvatar') || 'default')

const canManageTeam = computed(() =>
  authStore.user?.is_staff || authStore.user?.is_organization_owner
)

const userDropdownOptions = computed(() => [
  {
    label: '👤 Profile',
    key: 'profile'
  },
  {
    label: '⚙️ Settings',
    key: 'settings'
  },
  {
    label: '🚪 Logout',
    key: 'logout'
  }
])

const getAvatarEmoji = (avatar: string) => {
  const avatarMap: Record<string, string> = {
    default: '👤',
    leaf: '🌿',
    earth: '🌍',
    recycle: '♻️',
    seedling: '🌱',
    tree: '🌳',
    heart: '💚',
    energy: '⚡',
    factory: '🏭',
    chart: '📊'
  }
  return avatarMap[avatar] || '👤'
}

const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
}

const closeSidebar = () => {
  if (showSidebar.value) {
    showSidebar.value = false
  }
}

const handleUserAction = async (key: string) => {
  if (key === 'logout') {
    await authStore.logout()
    router.push('/login')
  } else if (key === 'profile' || key === 'settings') {
    router.push('/dashboard')
  }
}

const fetchStandardTypes = async () => {
  try {
    const token = localStorage.getItem('access_token')
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/standard-types`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    standardTypes.value = response.data
  } catch (error) {
    console.error('Failed to fetch standard types:', error)
  }
}

onMounted(() => {
  fetchStandardTypes()
})
</script>

<style lang="scss">
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.1s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
