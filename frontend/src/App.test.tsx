import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { AuthScreen, TaskModal } from './App'

vi.mock('./api', () => ({
  signup: vi.fn(),
  login: vi.fn(),
  getMe: vi.fn(),
  bootstrapSession: vi.fn(),
  logout: vi.fn(),
  getTasks: vi.fn(),
  createTask: vi.fn(),
  patchTask: vi.fn(),
  replaceTask: vi.fn(),
  deleteTask: vi.fn(),
  setAccessToken: vi.fn(),
  ApiError: class ApiError extends Error {
    status = 400
  },
}))

import * as api from './api'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('authentication UI', () => {
  it('submits login and reports the authenticated user', async () => {
    const user = userEvent.setup()
    const onAuthenticated = vi.fn()
    vi.mocked(api.login).mockResolvedValue(undefined)
    vi.mocked(api.getMe).mockResolvedValue({ id: 4, username: 'sample-user' })

    render(<AuthScreen onAuthenticated={onAuthenticated} />)
    await user.type(screen.getByLabelText('نام کاربری'), 'sample-user')
    await user.type(screen.getByLabelText('رمز عبور'), 'StrongPass123')
    await user.click(screen.getByRole('button', { name: /ورود به برنامه/ }))

    await waitFor(() => expect(onAuthenticated).toHaveBeenCalledWith({ id: 4, username: 'sample-user' }))
    expect(api.login).toHaveBeenCalledWith('sample-user', 'StrongPass123')
  })

  it('creates an account before logging in when signup mode is selected', async () => {
    const user = userEvent.setup()
    const onAuthenticated = vi.fn()
    vi.mocked(api.signup).mockResolvedValue({ id: 5, username: 'new-user' })
    vi.mocked(api.login).mockResolvedValue(undefined)
    vi.mocked(api.getMe).mockResolvedValue({ id: 5, username: 'new-user' })

    render(<AuthScreen onAuthenticated={onAuthenticated} />)
    await user.click(screen.getByRole('button', { name: 'ثبت‌نام کنید' }))
    await user.type(screen.getByLabelText('نام کاربری'), 'new-user')
    await user.type(screen.getByLabelText('رمز عبور'), 'StrongPass123')
    await user.click(screen.getByRole('button', { name: /ایجاد حساب/ }))

    await waitFor(() => expect(api.signup).toHaveBeenCalledWith('new-user', 'StrongPass123'))
    expect(api.login).toHaveBeenCalledWith('new-user', 'StrongPass123')
    expect(onAuthenticated).toHaveBeenCalledWith({ id: 5, username: 'new-user' })
  })
})

describe('task form', () => {
  it('submits a new task with a nullable description', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    render(<TaskModal mode="create" task={null} onClose={onClose} onSave={onSave} />)

    await user.type(screen.getByLabelText('عنوان وظیفه'), 'Prepare weekly report')
    await user.click(screen.getByRole('button', { name: /افزودن وظیفه/ }))

    await waitFor(() => expect(onSave).toHaveBeenCalledWith({
      title: 'Prepare weekly report',
      description: null,
      is_completed: false,
    }))
    expect(onClose).toHaveBeenCalled()
  })
})
