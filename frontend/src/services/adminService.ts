import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8090/api'

export interface TokenUsage {
  id: number
  user_email: string
  organization_email: string
  action_type: string
  model: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  cost_usd: number
  timestamp: string
  request_duration_ms?: number
  disclosure_code?: string
}

export interface UserTokenStats {
  user_id: number
  user_email: string
  role: string
  total_tokens: number
  total_cost_usd: number
  api_calls_count: number
  last_activity?: string
}

export interface OrganizationStats {
  organization_id: number
  organization_email: string
  company_type?: string
  total_users: number
  total_tokens: number
  total_cost_usd: number
  api_calls_count: number
  created_at: string
}

export interface DailyCost {
  date: string
  total_tokens: number
  total_cost_usd: number
  api_calls_count: number
  ai_answer_tokens: number
  conversation_tokens: number
  rag_search_tokens: number
}

export interface UserDetail {
  id: number
  email: string
  first_name: string
  last_name: string
  role: string
  company_type?: string
  wizard_completed: boolean
  is_active: boolean
  created_at: string
  last_login?: string
  total_tokens: number
  total_cost_usd: number
  completion_percentage: number
  team_members_count: number
}

class AdminService {
  private getAuthHeaders() {
    const token = localStorage.getItem('access_token')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  async getTokenUsage(params?: {
    user_id?: number
    organization_id?: number
    action_type?: string
    days?: number
    limit?: number
  }): Promise<TokenUsage[]> {
    const response = await axios.get(`${API_URL}/admin/token-usage`, {
      headers: this.getAuthHeaders(),
      params
    })
    return response.data
  }

  async getUsersWithStats(params?: {
    organization_id?: number
    days?: number
  }): Promise<UserTokenStats[]> {
    const response = await axios.get(`${API_URL}/admin/users/stats`, {
      headers: this.getAuthHeaders(),
      params
    })
    return response.data
  }

  async getOrganizationsWithStats(params?: {
    days?: number
  }): Promise<OrganizationStats[]> {
    const response = await axios.get(`${API_URL}/admin/organizations/stats`, {
      headers: this.getAuthHeaders(),
      params
    })
    return response.data
  }

  async getDailyCosts(params?: {
    organization_id?: number
    days?: number
  }): Promise<DailyCost[]> {
    const response = await axios.get(`${API_URL}/admin/costs/daily`, {
      headers: this.getAuthHeaders(),
      params
    })
    return response.data
  }

  async getAllUsers(): Promise<UserDetail[]> {
    const response = await axios.get(`${API_URL}/admin/users`, {
      headers: this.getAuthHeaders()
    })
    return response.data
  }
}

export const adminService = new AdminService()
export default adminService
