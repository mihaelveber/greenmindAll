import api from './api'

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  password_confirm: string
}

export interface User {
  id: number
  email: string
  username: string
  avatar?: string
  oauth_provider?: string
  wizard_completed?: boolean
  company_type?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post('/auth/login', credentials)
    return response.data
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me')
    return response.data
  },

  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },

  // OAuth2 URLs
  getGoogleAuthUrl(): string {
    return `${api.defaults.baseURL}/auth/google/login`
  },

  getAppleAuthUrl(): string {
    return `${api.defaults.baseURL}/auth/apple/login`
  },
}
