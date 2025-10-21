export default defineNuxtRouteMiddleware(async (to) => {
  if (process.server) return

  // Allow public pages
  const publicPaths = new Set(['/login', '/register', '/forgot-password', '/reset-password', '/'])
  if (publicPaths.has(to.path) || to.meta.auth === 'public') return

  const { isAuthenticated, isLoading, initializeAuth, user } = useAuth()
  
  // Initialize auth state if not already done
  if (!isAuthenticated.value && !isLoading.value) {
    await initializeAuth()
  }
  
  if (isLoading.value) return

  if (!isAuthenticated.value) {
    return navigateTo('/login')
  }

  // Redirect bare /dashboard to role-appropriate default
  if (to.path === '/dashboard') {
    const userRoles = (user.value?.roles || []).map(r => (r.name || '').toLowerCase())
    const isAdmin = userRoles.includes('admin') || userRoles.includes('admission')
    return navigateTo(isAdmin ? '/dashboard/submissions' : '/dashboard/my-submissions')
  }

  // Role-based authorization if route requires roles
  const requiredRoles = (to.meta?.roles as string[] | undefined)?.map(r => r.toLowerCase())
  if (requiredRoles && requiredRoles.length) {
    const userRoles = (user.value?.roles || []).map(r => (r.name || '').toLowerCase())
    const hasAccess = userRoles.some(r => requiredRoles.includes(r))
    if (!hasAccess) {
      // If accessing a dashboard route without permission, send to dashboard root
      if (to.path.startsWith('/dashboard')) {
        const isAdmin = userRoles.includes('admin') || userRoles.includes('admission')
        const fallback = isAdmin ? '/dashboard/submissions' : '/dashboard/my-submissions'
        return navigateTo(fallback)
      }
      return navigateTo('/')
    }
  }
})
