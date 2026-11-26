export type User = { id: number; username: string }
export type Task = {
  id: number
  title: string
  description: string | null
  is_completed: boolean
  created_at: string
  owner_id: number
}
export type TaskPage = {
  items: Task[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
export type SortBy = 'created_at' | 'title' | 'is_completed' | 'id'
export type SortOrder = 'asc' | 'desc'
export type TaskQuery = {
  page?: number
  page_size?: number
  sort_by?: SortBy
  order?: SortOrder
  is_completed?: boolean
}

type TokenResponse = { access_token: string; token_type: 'bearer' }

let accessToken: string | null = null
let refreshPromise: Promise<boolean> | null = null

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export function setAccessToken(token: string | null) {
  accessToken = token
}

async function readError(response: Response): Promise<ApiError> {
  let message = 'خطایی در ارتباط با سرور رخ داد.'
  try {
    const data = await response.json() as { detail?: string | Array<{ msg?: string }> }
    if (typeof data.detail === 'string') message = data.detail
    else if (Array.isArray(data.detail)) message = data.detail.map((item) => item.msg).filter(Boolean).join('، ')
  } catch {
    // Keep the generic message when the server did not return JSON.
  }
  return new ApiError(response.status, message)
}

async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise
  const pending = (async () => {
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      })
      if (!response.ok) {
        accessToken = null
        return false
      }
      const data = await response.json() as TokenResponse
      accessToken = data.access_token
      return true
    } catch {
      accessToken = null
      return false
    } finally {
      refreshPromise = null
    }
  })()
  refreshPromise = pending
  return pending
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`/api${path}`, {
    ...init,
    headers,
    credentials: 'same-origin',
  })

  const noRefreshPaths = ['/login', '/signup', '/auth/refresh', '/auth/logout']
  if (response.status === 401 && retry && !noRefreshPaths.includes(path)) {
    const refreshed = await refreshAccessToken()
    if (refreshed) return request<T>(path, init, false)
    accessToken = null
    window.dispatchEvent(new Event('task-manager:unauthorized'))
  }

  if (!response.ok) throw await readError(response)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function signup(username: string, password: string): Promise<User> {
  return request<User>('/signup', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function login(username: string, password: string): Promise<void> {
  const form = new URLSearchParams({ username, password })
  const data = await request<TokenResponse>('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  })
  accessToken = data.access_token
}

export async function bootstrapSession(): Promise<User | null> {
  const refreshed = await refreshAccessToken()
  if (!refreshed) return null
  try {
    return await request<User>('/users/me')
  } catch {
    accessToken = null
    return null
  }
}

export async function logout(): Promise<void> {
  try {
    await request<void>('/auth/logout', { method: 'POST' }, false)
  } finally {
    accessToken = null
  }
}

export function getMe(): Promise<User> {
  return request<User>('/users/me')
}

export function getTasks(query: TaskQuery = {}): Promise<TaskPage> {
  const params = new URLSearchParams()
  if (query.page !== undefined) params.set('page', String(query.page))
  if (query.page_size !== undefined) params.set('page_size', String(query.page_size))
  if (query.sort_by) params.set('sort_by', query.sort_by)
  if (query.order) params.set('order', query.order)
  if (query.is_completed !== undefined) params.set('is_completed', String(query.is_completed))
  return request<TaskPage>(`/tasks?${params.toString()}`)
}

export function createTask(data: { title: string; description: string | null }): Promise<Task> {
  return request<Task>('/tasks', { method: 'POST', body: JSON.stringify(data) })
}

export function patchTask(id: number, data: Partial<Pick<Task, 'title' | 'description' | 'is_completed'>>): Promise<Task> {
  return request<Task>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
}

export function replaceTask(id: number, data: Pick<Task, 'title' | 'description' | 'is_completed'>): Promise<Task> {
  return request<Task>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) })
}

export function deleteTask(id: number): Promise<void> {
  return request<void>(`/tasks/${id}`, { method: 'DELETE' })
}
