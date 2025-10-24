import { ofetch, type FetchOptions } from 'ofetch'

// Lock to JSON responses to avoid ResponseType mismatch
type JSONFetchOptions = Omit<FetchOptions<'json'>, 'headers'> & {
  headers?: HeadersInit
}

export interface ApiOptions extends JSONFetchOptions {
  /** Skip Authorization header for public endpoints */
  noAuth?: boolean
  /** Explicit HTTP method */
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
}

export const useApi = () => {
  const { accessToken, isAuthenticated } = useAuth()
  const { apiBase } = useRuntimeConfig().public

  const pending = useState<number>('api:pending', () => 0)
  const lastError = useState<Error | null>('api:lastError', () => null)
  const isApiLoading = computed(() => pending.value > 0)

  const client = useState('api:client', () =>
    ofetch.create({
      baseURL: apiBase,
      retry: 0,
      timeout: 20000,

      onRequest: async ({ options }) => {
        pending.value++
        lastError.value = null

        // Normalize headers (works whether headers started as object/array/Headers)
        const hdrs = new Headers(options.headers as HeadersInit | undefined)

        const noAuth = (options as ApiOptions).noAuth
        if (!noAuth && isAuthenticated.value && accessToken.value) {
          hdrs.set('Authorization', `Bearer ${accessToken.value}`)
        }

        options.headers = hdrs // ResolvedFetchOptions expects Headers
      },

      onResponse: () => {
        pending.value = Math.max(0, pending.value - 1)
      },

      onResponseError: async ({ error, response }) => {
        pending.value = Math.max(0, pending.value - 1)

        if (error) {
          lastError.value = error
          return
        }

        const status = response?.status ?? 'unknown'
        let detail = ''
        try {
          // ofetch stores parsed body on _data
          // @ts-ignore
          const data = await response?._data
          detail = typeof data === 'string' ? data : JSON.stringify(data ?? '')
        } catch {
          /* ignore */
        }

        lastError.value = new Error(`HTTP ${status}${detail ? `: ${detail}` : ''}`)
      },
    })
  ).value

  /**
   * Unified API call. Always pass method explicitly.
   * Example: $api<User[]>('/users', { method: 'GET' })
   */
  const $api = <T = unknown>(path: string, options: ApiOptions = {}) => client<T>(path, options as FetchOptions<'json'>) // lock responseType to 'json'

  return { $api, isApiLoading, lastError }
}

/*

const { $api, isApiLoading, lastError } = useApi()

// GET
const users = await $api<User[]>('/users', { method: 'GET' })

// POST
const created = await $api<User>('/users', {
  method: 'POST',
  body: { email: 'admin@corp.com', role: 'Admin' }
})

// PUT
await $api('/users/123', { method: 'PUT', body: { role: 'Editor' } })

// PATCH
await $api('/users/123', { method: 'PATCH', body: { active: false } })

// DELETE
await $api('/users/123', { method: 'DELETE' })

// Public GET (no token)
const ping = await $api<string>('/public/ping', { method: 'GET', noAuth: true })

 */
