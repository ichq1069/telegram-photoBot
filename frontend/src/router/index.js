import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { noAuth: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: 'bots',
        name: 'Bots',
        component: () => import('@/views/Bots.vue'),
        meta: { title: '机器人管理' },
      },
      {
        path: 'images',
        name: 'Images',
        component: () => import('@/views/Images.vue'),
        meta: { title: '图床管理' },
      },
      {
        path: 'messages',
        name: 'Messages',
        component: () => import('@/views/Messages.vue'),
        meta: { title: '消息管理' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, _, next) => {
  const token = localStorage.getItem('token')
  if (!to.meta.noAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
