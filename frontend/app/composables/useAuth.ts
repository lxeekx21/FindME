interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
  phone?: string
  profile_image_url?: string
  is_active: boolean
  created_at: string
  updated_at: string
  roles: Array<{
    id: number
    name: string
  }>
}

interface LoginRequest {
  email: string
  password: string
}

interface RegisterRequest {
  email: string
  password: string
  first_name?: string
  last_name?: string
}

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export const useAuth = () => {
  const { apiBase } = useRuntimeConfig().public
  
  // State
  const user = useState<User | null>('auth.user', () => null)
  const accessToken = useState<string | null>('auth.accessToken', () => null)
  const refreshToken = useState<string | null>('auth.refreshToken', () => null)
  const isLoading = useState<boolean>('auth.isLoading', () => false)
  
  // Computed
  const isAuthenticated = computed(() => !!user.value && !!accessToken.value)
  
  // Methods
  const login = async (credentials: LoginRequest): Promise<void> => {
    isLoading.value = true
    try {
      const response = await $fetch<TokenResponse>('/auth/login', {
        baseURL: apiBase,
        method: 'POST',
        body: credentials
      })
      
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      
      // Get user info
      await fetchUser()
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  const register = async (userData: RegisterRequest): Promise<void> => {
    isLoading.value = true
    try {
      const response = await $fetch<TokenResponse>('/auth/register', {
        baseURL: apiBase,
        method: 'POST',
        body: userData
      })
      
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      
      // Get user info
      await fetchUser()
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  const logout = async (): Promise<void> => {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    
    // Clear any stored tokens
    if (process.client) {
      localStorage.removeItem('auth.accessToken')
      localStorage.removeItem('auth.refreshToken')
    }
  }
  
  const fetchUser = async (): Promise<void> => {
    if (!accessToken.value) return
    
    try {
      const userData = await $fetch<User>('/auth/me', {
        baseURL: apiBase,
        headers: {
          Authorization: `Bearer ${accessToken.value}`
        }
      })
      user.value = userData
    } catch (error) {
      console.error('Failed to fetch user:', error)
      // If token is invalid, try to refresh
      if (refreshToken.value) {
        try {
          await refreshAccessToken()
          await fetchUser()
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError)
          await logout()
        }
      } else {
        await logout()
      }
    }
  }
  
  const refreshAccessToken = async (): Promise<void> => {
    if (!refreshToken.value) throw new Error('No refresh token available')
    
    try {
      const response = await $fetch<TokenResponse>('/auth/refresh', {
        baseURL: apiBase,
        method: 'POST',
        body: { refresh_token: refreshToken.value }
      })
      
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
    } catch (error) {
      console.error('Token refresh failed:', error)
      throw error
    }
  }
  
  // Initialize auth state from localStorage on client
  const initializeAuth = async (): Promise<void> => {
    if (process.server) return
    
    const storedAccessToken = localStorage.getItem('auth.accessToken')
    const storedRefreshToken = localStorage.getItem('auth.refreshToken')
    
    if (storedAccessToken && storedRefreshToken) {
      accessToken.value = storedAccessToken
      refreshToken.value = storedRefreshToken
      await fetchUser()
    }
  }
  
  // Persist tokens to localStorage
  watch([accessToken, refreshToken], ([newAccessToken, newRefreshToken]) => {
    if (process.client) {
      if (newAccessToken) {
        localStorage.setItem('auth.accessToken', newAccessToken)
      } else {
        localStorage.removeItem('auth.accessToken')
      }
      
      if (newRefreshToken) {
        localStorage.setItem('auth.refreshToken', newRefreshToken)
      } else {
        localStorage.removeItem('auth.refreshToken')
      }
    }
  })
  
  return {
    // State
    user: readonly(user),
    accessToken: readonly(accessToken),
    refreshToken: readonly(refreshToken),
    isLoading: readonly(isLoading),
    
    // Computed
    isAuthenticated,
    
    // Methods
    login,
    register,
    logout,
    fetchUser,
    refreshAccessToken,
    initializeAuth
  }
}
