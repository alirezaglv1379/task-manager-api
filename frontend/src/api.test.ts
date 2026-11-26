// @vitest-environment node

import { afterEach, describe, expect, it, vi } from 'vitest'

import { getTasks, setAccessToken } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
  setAccessToken(null)
})

describe('API client', () => {
  it('sends the false completion filter instead of dropping it', async () => {
    const data = { items: [], total: 0, page: 1, page_size: 20, total_pages: 0 }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => data,
    } as Response)
    vi.stubGlobal('fetch', fetchMock)

    await getTasks({ page: 1, page_size: 20, is_completed: false })
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/tasks?page=1&page_size=20&is_completed=false',
      expect.objectContaining({ credentials: 'same-origin' }),
    )
  })
})
