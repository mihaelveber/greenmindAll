import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.store'
import LoginView from '../views/LoginView.vue'
import DashboardLayout from '../layout/DashboardLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresGuest: true }
    },
    {
      path: '/oauth/callback',
      name: 'oauth-callback',
      component: () => import('../views/OAuthCallbackView.vue')
    },
    {
      path: '/wizard',
      name: 'wizard',
      component: () => import('../views/WizardView.vue'),
      meta: { requiresAuth: true }
    },
    // All authenticated routes use DashboardLayout wrapper
    {
      path: '/',
      component: DashboardLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/DashboardContentView.vue')
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('../views/DocumentsView.vue')
        },
        {
          path: 'bulk-processing',
          name: 'bulk-processing',
          component: () => import('../views/BulkProcessingView.vue')
        },
        {
          path: 'standards/:standardType',
          name: 'standards',
          component: () => import('../views/StandardView.vue')
        },
        {
          path: 'team',
          name: 'team',
          component: () => import('../views/UserManagementView.vue')
        }
      ]
    },
    {
      path: '/esrs',
      redirect: '/standards/ESRS'
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // If we have a token but no user (e.g., after page refresh), fetch the user
  if (authStore.accessToken && !authStore.user) {
    try {
      await authStore.fetchCurrentUser()
    } catch (error) {
      // If fetching user fails, clear tokens and redirect to login
      console.error('Failed to restore user session:', error)
      await authStore.logout()
      if (to.meta.requiresAuth) {
        next('/login')
        return
      }
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresAdmin && !authStore.user?.is_superuser) {
    // Redirect non-admin users trying to access admin pages
    next('/dashboard')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    // Check if wizard is completed
    if (authStore.user && !authStore.user.wizard_completed && to.name !== 'wizard') {
      next('/wizard')
    } else {
      next('/dashboard')
    }
  } else if (authStore.isAuthenticated && to.name !== 'wizard' && to.name !== 'login') {
    // Check if user needs to complete wizard
    if (authStore.user && !authStore.user.wizard_completed && to.name !== 'wizard') {
      next('/wizard')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
