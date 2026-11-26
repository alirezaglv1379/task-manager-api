import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import {
  Activity, ArrowDownUp, ArrowLeft, ArrowRight, Bell, CalendarDays, Check,
  CheckCircle2, ChevronDown, Circle, ClipboardList, Clock3, LayoutDashboard,
  ListTodo, LogOut, Menu, MoreHorizontal, Pencil, Plus, Search, ShieldCheck,
  Sparkles, Trash2, X,
} from 'lucide-react'
import {
  ApiError, bootstrapSession, createTask, deleteTask, getMe, getTasks, login,
  logout, patchTask, replaceTask, signup,
  type SortBy, type SortOrder, type Task, type TaskPage, type User,
} from './api'

const PAGE_SIZE = 20

type Filter = 'all' | 'open' | 'completed'
type ModalMode = 'create' | 'edit' | null

function formatDate(value: string) {
  return new Intl.DateTimeFormat('fa-IR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'مشکلی پیش آمد. دوباره تلاش کنید.'
}

export function AuthScreen({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (mode === 'signup') await signup(username.trim(), password)
      await login(username.trim(), password)
      const user = await getMe()
      onAuthenticated(user)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-art">
        <div className="art-orb orb-one" /><div className="art-orb orb-two" />
        <div className="art-content">
          <div className="brand-mark large"><CheckCircle2 size={25} /></div>
          <span className="eyebrow light">FOCUS · PLAN · FINISH</span>
          <h1>کارهای مهمت،<br /><span>با تمرکز بیشتر.</span></h1>
          <p>یک فضای ساده و امن برای نظم‌دادن به کارهای روزانه و پیگیری پیشرفتت.</p>
          <div className="art-mini-card">
            <div className="mini-check"><Check size={15} /></div>
            <div><strong>قدم‌به‌قدم جلو برو</strong><small>هر کار تمام‌شده، یک پیشرفت واقعی است.</small></div>
            <Sparkles size={19} className="mini-spark" />
          </div>
        </div>
        <div className="art-footer">TASK MANAGER <span>نسخه ۲٫۰</span></div>
      </section>

      <section className="auth-panel">
        <div className="auth-top"><div className="brand-inline"><span className="brand-mark"><CheckCircle2 size={19} /></span><strong>تسک‌منیجر</strong></div><span className="secure-label"><ShieldCheck size={15} /> اتصال امن</span></div>
        <div className="auth-form-wrap">
          <span className="eyebrow">خوش آمدید</span>
          <h2>{mode === 'login' ? 'ورود به حساب' : 'ساخت حساب جدید'}</h2>
          <p className="muted">{mode === 'login' ? 'برای ادامه، اطلاعات حساب خود را وارد کنید.' : 'برای شروع مدیریت کارهایتان، حساب بسازید.'}</p>
          <form onSubmit={submit} className="auth-form">
            <label>نام کاربری<input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} minLength={3} maxLength={30} required placeholder="نام کاربری خود را وارد کنید" /></label>
            <label>رمز عبور<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required placeholder="حداقل ۸ کاراکتر" /></label>
            {error && <div className="alert error-alert">{error}</div>}
            <button className="primary-button full-button" disabled={busy}>{busy ? <span className="spinner" /> : mode === 'login' ? 'ورود به برنامه' : 'ایجاد حساب'}<ArrowLeft size={17} /></button>
          </form>
          <div className="auth-switch">{mode === 'login' ? 'حساب کاربری ندارید؟' : 'قبلاً حساب ساخته‌اید؟'} <button onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError('') }}>{mode === 'login' ? 'ثبت‌نام کنید' : 'وارد شوید'}</button></div>
        </div>
        <div className="auth-bottom"><span>© ۲۰۲۶ Task Manager</span><span>مدیریت کارها، ساده و مطمئن</span></div>
      </section>
    </main>
  )
}

export function TaskModal({ mode, task, onClose, onSave }: {
  mode: Exclude<ModalMode, null>
  task: Task | null
  onClose: () => void
  onSave: (data: { title: string; description: string | null; is_completed?: boolean }) => Promise<void>
}) {
  const [title, setTitle] = useState(task?.title ?? '')
  const [description, setDescription] = useState(task?.description ?? '')
  const [completed, setCompleted] = useState(task?.is_completed ?? false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true); setError('')
    try {
      await onSave({ title: title.trim(), description: description.trim() || null, is_completed: completed })
      onClose()
    } catch (err) { setError(errorMessage(err)) }
    finally { setBusy(false) }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="task-modal-title">
        <div className="modal-head"><div><span className="eyebrow">{mode === 'create' ? 'وظیفه جدید' : 'ویرایش وظیفه'}</span><h3 id="task-modal-title">{mode === 'create' ? 'چه کاری در پیش داری؟' : 'جزئیات وظیفه'}</h3></div><button className="icon-button" onClick={onClose} aria-label="بستن"><X size={19} /></button></div>
        <form onSubmit={submit} className="task-form">
          <label>عنوان وظیفه<input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} required placeholder="مثلاً: آماده‌کردن گزارش هفتگی" /></label>
          <label>توضیحات <span className="optional">اختیاری</span><textarea value={description} onChange={(e) => setDescription(e.target.value)} maxLength={2000} rows={4} placeholder="جزئیات بیشتری اضافه کن..." /></label>
          {mode === 'edit' && <label className="check-row"><input type="checkbox" checked={completed} onChange={(e) => setCompleted(e.target.checked)} /> این وظیفه انجام شده است</label>}
          {error && <div className="alert error-alert">{error}</div>}
          <div className="modal-actions"><button type="button" className="secondary-button" onClick={onClose}>انصراف</button><button className="primary-button" disabled={busy || !title.trim()}>{busy ? <span className="spinner" /> : mode === 'create' ? 'افزودن وظیفه' : 'ذخیره تغییرات'}<Check size={16} /></button></div>
        </form>
      </section>
    </div>
  )
}

function Dashboard({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [filter, setFilter] = useState<Filter>('all')
  const [sortBy, setSortBy] = useState<SortBy>('created_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [page, setPage] = useState(1)
  const [taskPage, setTaskPage] = useState<TaskPage | null>(null)
  const [counts, setCounts] = useState({ total: 0, open: 0, completed: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modal, setModal] = useState<ModalMode>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [search, setSearch] = useState('')
  const [mobileNav, setMobileNav] = useState(false)
  const [actionBusy, setActionBusy] = useState<number | null>(null)

  const loadTasks = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const completed = filter === 'all' ? undefined : filter === 'completed'
      const [current, openCount, completedCount] = await Promise.all([
        getTasks({ page, page_size: PAGE_SIZE, sort_by: sortBy, order: sortOrder, is_completed: completed }),
        getTasks({ page: 1, page_size: 1, is_completed: false }),
        getTasks({ page: 1, page_size: 1, is_completed: true }),
      ])
      setTaskPage(current)
      setCounts({ total: openCount.total + completedCount.total, open: openCount.total, completed: completedCount.total })
    } catch (err) { setError(errorMessage(err)) }
    finally { setLoading(false) }
  }, [filter, page, sortBy, sortOrder])

  useEffect(() => { void loadTasks() }, [loadTasks])

  const visibleTasks = useMemo(() => {
    const items = taskPage?.items ?? []
    const term = search.trim().toLocaleLowerCase('fa')
    if (!term) return items
    return items.filter((task) => `${task.title} ${task.description ?? ''}`.toLocaleLowerCase('fa').includes(term))
  }, [taskPage, search])

  async function saveTask(data: { title: string; description: string | null; is_completed?: boolean }) {
    if (modal === 'create') await createTask({ title: data.title, description: data.description })
    else if (selectedTask) await replaceTask(selectedTask.id, { title: data.title, description: data.description, is_completed: Boolean(data.is_completed) })
    setPage(1)
    await loadTasks()
  }

  async function toggleTask(task: Task) {
    setActionBusy(task.id)
    try { await patchTask(task.id, { is_completed: !task.is_completed }); await loadTasks() }
    catch (err) { setError(errorMessage(err)) }
    finally { setActionBusy(null) }
  }

  async function removeTask(task: Task) {
    if (!window.confirm(`وظیفه «${task.title}» حذف شود؟`)) return
    setActionBusy(task.id)
    try { await deleteTask(task.id); if (taskPage && taskPage.items.length === 1 && page > 1) setPage(page - 1); else await loadTasks() }
    catch (err) { setError(errorMessage(err)) }
    finally { setActionBusy(null) }
  }

  async function signOut() {
    await onLogout()
  }

  const firstName = user.username

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
        <div className="sidebar-brand"><span className="brand-mark"><CheckCircle2 size={20} /></span><div><strong>تسک‌منیجر</strong><small>TASK MANAGER</small></div><button className="icon-button sidebar-close" onClick={() => setMobileNav(false)}><X size={18} /></button></div>
        <div className="workspace-label">فضای کاری</div>
        <nav className="side-nav"><button className="nav-item active"><LayoutDashboard size={18} /><span>نمای کلی</span></button><button className="nav-item" onClick={() => { setFilter('all'); setPage(1); setMobileNav(false) }}><ListTodo size={18} /><span>همه وظایف</span><span className="nav-count">{counts.total}</span></button><button className="nav-item" onClick={() => { setFilter('open'); setPage(1); setMobileNav(false) }}><Circle size={18} /><span>در انتظار انجام</span></button><button className="nav-item" onClick={() => { setFilter('completed'); setPage(1); setMobileNav(false) }}><CheckCircle2 size={18} /><span>انجام‌شده‌ها</span></button></nav>
        <div className="sidebar-spacer" />
        <div className="sidebar-tip"><div className="tip-icon"><Sparkles size={17} /></div><strong>یک قدم کوچک</strong><p>هر روز یک کار مهم را کامل کن. استمرار از سرعت مهم‌تر است.</p></div>
        <div className="sidebar-user"><div className="avatar">{user.username.slice(0, 1).toUpperCase()}</div><div className="user-meta"><strong>{user.username}</strong><small>حساب شخصی</small></div><button className="icon-button logout-button" title="خروج" onClick={signOut}><LogOut size={17} /></button></div>
      </aside>
      {mobileNav && <button className="mobile-scrim" onClick={() => setMobileNav(false)} aria-label="بستن منو" />}

      <main className="main-content">
        <header className="topbar"><div className="topbar-title"><button className="icon-button mobile-menu" onClick={() => setMobileNav(true)}><Menu size={20} /></button><div><span className="eyebrow">فضای شخصی شما</span><h1>نمای کلی</h1></div></div><div className="topbar-actions"><div className="today-chip"><CalendarDays size={16} />{new Intl.DateTimeFormat('fa-IR', { dateStyle: 'full' }).format(new Date())}</div><button className="icon-button notification-button" title="اعلان‌ها"><Bell size={18} /><i /></button><div className="top-avatar">{user.username.slice(0, 1).toUpperCase()}</div></div></header>

        <section className="welcome-row"><div><h2>سلام، {firstName} <span className="wave">✦</span></h2><p>برای امروز چه برنامه‌ای داری؟ کارهایت را مرتب کن و قدم‌به‌قدم جلو برو.</p></div><button className="primary-button add-main" onClick={() => { setSelectedTask(null); setModal('create') }}><Plus size={18} /> وظیفه جدید</button></section>

        <section className="stats-grid">
          <article className="stat-card"><div className="stat-icon indigo"><ClipboardList size={19} /></div><div className="stat-copy"><span>مجموع وظایف</span><strong>{counts.total.toLocaleString('fa-IR')}</strong><small>تمام کارهای ثبت‌شده</small></div><div className="stat-mark"><Activity size={24} /></div></article>
          <article className="stat-card"><div className="stat-icon amber"><Clock3 size={19} /></div><div className="stat-copy"><span>در انتظار انجام</span><strong>{counts.open.toLocaleString('fa-IR')}</strong><small>کارهایی که باقی مانده‌اند</small></div><div className="stat-mark amber-mark"><Activity size={24} /></div></article>
          <article className="stat-card"><div className="stat-icon green"><CheckCircle2 size={19} /></div><div className="stat-copy"><span>انجام‌شده</span><strong>{counts.completed.toLocaleString('fa-IR')}</strong><small>قدم‌هایی که برداشته‌ای</small></div><div className="stat-mark green-mark"><CheckCircle2 size={24} /></div></article>
        </section>

        <section className="tasks-panel">
          <div className="panel-heading"><div><span className="eyebrow">برنامه‌ریزی روزانه</span><h3>وظایف من</h3></div><button className="text-button" onClick={() => { setFilter('all'); setPage(1) }}>مشاهده همه <ArrowLeft size={15} /></button></div>
          <div className="toolbar"><div className="filter-tabs"><button className={filter === 'all' ? 'selected' : ''} onClick={() => { setFilter('all'); setPage(1) }}>همه <span>{counts.total.toLocaleString('fa-IR')}</span></button><button className={filter === 'open' ? 'selected' : ''} onClick={() => { setFilter('open'); setPage(1) }}>در انتظار</button><button className={filter === 'completed' ? 'selected' : ''} onClick={() => { setFilter('completed'); setPage(1) }}>انجام‌شده</button></div><div className="toolbar-tools"><label className="search-box"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="جست‌وجو در این صفحه..." /></label><label className="sort-select"><ArrowDownUp size={15} /><select value={`${sortBy}:${sortOrder}`} onChange={(e) => { const [field, order] = e.target.value.split(':') as [SortBy, SortOrder]; setSortBy(field); setSortOrder(order); setPage(1) }}><option value="created_at:desc">جدیدترین</option><option value="created_at:asc">قدیمی‌ترین</option><option value="title:asc">عنوان (الف تا ی)</option><option value="title:desc">عنوان (ی تا الف)</option></select><ChevronDown size={14} /></label></div></div>

          {error && <div className="alert error-alert panel-alert">{error}<button onClick={() => void loadTasks()}>تلاش دوباره</button></div>}
          {loading ? <div className="loading-state"><span className="spinner dark-spinner" /><span>در حال دریافت وظایف...</span></div> : visibleTasks.length === 0 ? <div className="empty-state"><div className="empty-icon"><ListTodo size={27} /></div><h4>{search ? 'نتیجه‌ای پیدا نشد' : 'هنوز وظیفه‌ای ثبت نشده'}</h4><p>{search ? 'عبارت دیگری را جست‌وجو کن.' : 'اولین وظیفه‌ات را اضافه کن تا برنامه‌ریزی را شروع کنیم.'}</p>{!search && <button className="primary-button" onClick={() => { setSelectedTask(null); setModal('create') }}><Plus size={17} /> افزودن اولین وظیفه</button>}</div> : <div className="task-list">{visibleTasks.map((task) => <article className={`task-row ${task.is_completed ? 'task-done' : ''}`} key={task.id}><button className={`task-check ${task.is_completed ? 'checked' : ''}`} onClick={() => void toggleTask(task)} disabled={actionBusy === task.id} aria-label={task.is_completed ? 'علامت‌گذاری به‌عنوان انجام‌نشده' : 'علامت‌گذاری به‌عنوان انجام‌شده'}>{task.is_completed ? <Check size={15} /> : <span />}</button><div className="task-content"><div className="task-title-line"><h4>{task.title}</h4>{task.is_completed && <span className="done-pill">انجام شد</span>}</div>{task.description && <p>{task.description}</p>}<div className="task-meta"><span><CalendarDays size={13} />{formatDate(task.created_at)}</span><span className="task-id">شناسه #{task.id.toLocaleString('fa-IR')}</span></div></div><div className="task-actions"><button className="icon-button" title="ویرایش" onClick={() => { setSelectedTask(task); setModal('edit') }}><Pencil size={16} /></button><button className="icon-button danger-hover" title="حذف" onClick={() => void removeTask(task)} disabled={actionBusy === task.id}><Trash2 size={16} /></button><button className="icon-button more-button" title="بیشتر"><MoreHorizontal size={17} /></button></div></article>)}</div>}

          {taskPage && taskPage.total_pages > 1 && <div className="pagination"><span>نمایش {((page - 1) * PAGE_SIZE + 1).toLocaleString('fa-IR')} تا {Math.min(page * PAGE_SIZE, taskPage.total).toLocaleString('fa-IR')} از {taskPage.total.toLocaleString('fa-IR')} وظیفه</span><div className="page-controls"><button className="page-button" disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}><ArrowRight size={16} /> قبلی</button><span className="page-number">{page.toLocaleString('fa-IR')} / {taskPage.total_pages.toLocaleString('fa-IR')}</span><button className="page-button" disabled={page >= taskPage.total_pages} onClick={() => setPage((value) => Math.min(taskPage.total_pages, value + 1))}>بعدی <ArrowLeft size={16} /></button></div></div>}
        </section>
        <footer className="page-footer"><span>ساخته‌شده برای تمرکز بیشتر</span><span>Task Manager <b>·</b> v2.0</span></footer>
      </main>

      {modal && <TaskModal mode={modal} task={selectedTask} onClose={() => setModal(null)} onSave={saveTask} />}
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [booting, setBooting] = useState(true)

  useEffect(() => {
    let active = true
    const handleExpired = () => {
      void logout().catch(() => undefined).finally(() => setUser(null))
    }
    window.addEventListener('task-manager:unauthorized', handleExpired)
    bootstrapSession().then((currentUser) => { if (active) setUser(currentUser) }).finally(() => { if (active) setBooting(false) })
    return () => {
      active = false
      window.removeEventListener('task-manager:unauthorized', handleExpired)
    }
  }, [])

  const handleLogout = useCallback(async () => {
    try { await logout() } catch { /* Local session state is cleared even if the API is unreachable. */ }
    finally { setUser(null) }
  }, [])

  if (booting) return <div className="boot-screen"><span className="spinner dark-spinner" /><strong>در حال آماده‌سازی فضای کاری...</strong></div>
  if (!user) return <AuthScreen onAuthenticated={setUser} />
  return <Dashboard user={user} onLogout={handleLogout} />
}
