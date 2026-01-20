import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.store'
import LoginView from '../views/LoginView.vue'

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
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
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
    {
      path: '/documents',
      name: 'documents',
      component: () => import('../views/DocumentsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/standards/:standardType',
      name: 'standards',
      component: () => import('../views/StandardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/esrs',
      redirect: '/standards/ESRS'
    },
    {
      path: '/team',
      name: 'team',
      component: () => import('../views/UserManagementView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
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
