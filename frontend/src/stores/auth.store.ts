import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService, type User, type LoginCredentials, type RegisterData } from '../services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const loading = ref(false)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  async function login(credentials: LoginCredentials) {
    loading.value = true
    try {
      const response = await authService.login(credentials)
      
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      user.value = response.user

      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)

      return true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterData) {
    loading.value = true
    try {
      const response = await authService.register(data)
      
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      user.value = response.user

      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)

      return true
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    try {
      await authService.logout()
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      user.value = null
      accessToken.value = null
      refreshToken.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      loading.value = false
    }
  }

  async function fetchCurrentUser() {
    if (!accessToken.value) return

    loading.value = true
    try {
      user.value = await authService.getCurrentUser()
    } catch (error) {
      console.error('Failed to fetch user:', error)
      await logout()
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    fetchCurrentUser,
  }
})
