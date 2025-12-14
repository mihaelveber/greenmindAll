<template>
  <div class="callback-container">
    <n-spin size="large">
      <template #description>
        <p>Prijavljanje...</p>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'

const router = useRouter()
const message = useMessage()

onMounted(() => {
  // Get tokens from URL parameters
  const params = new URLSearchParams(window.location.search)
  const accessToken = params.get('access_token')
  const refreshToken = params.get('refresh_token')
  const error = params.get('error')

  if (error) {
    message.error('Prijava neuspešna')
    router.push('/login')
    return
  }

  if (accessToken && refreshToken) {
    // Store tokens
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    
    message.success('Uspešna prijava!')
    router.push('/dashboard')
  } else {
    message.error('Napaka pri OAuth avtentikaciji')
    router.push('/login')
  }
})
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
