import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Login from '../views/Login.vue'
import AdminLayout from '../views/admin/Layout.vue'
import Dashboard from '../views/admin/Dashboard.vue'
import VMManagement from '../views/admin/VMs.vue'
import UserManagement from '../views/admin/Users.vue'
import UserLayout from '../views/user/Layout.vue'
import MyDesktop from '../views/user/MyDesktop.vue'
import VNCViewer from '../views/user/VNCViewer.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'vms',
        name: 'VMManagement',
        component: VMManagement
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: UserManagement
      }
    ]
  },
  {
    path: '/',
    component: UserLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'MyDesktop',
        component: MyDesktop
      },
      {
        path: 'vnc/:node/:vmid',
        name: 'VNCViewer',
        component: VNCViewer,
        props: true
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  if (authStore.isAuthenticated && !authStore.user) {
    try {
      await authStore.fetchUser()
    } catch {
      next('/login')
      return
    }
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')
    return
  }
  next()
})

export default router
