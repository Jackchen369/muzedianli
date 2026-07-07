import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue') },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'partners', name: 'Partners', component: () => import('@/views/Partners.vue') },
      { path: 'projects', name: 'Projects', component: () => import('@/views/Projects.vue') },
      { path: 'projects/:id', name: 'ProjectDetail', component: () => import('@/views/ProjectDetail.vue') },
      { path: 'invoices', name: 'Invoices', component: () => import('@/views/Invoices.vue') },
      { path: 'finance', name: 'Finance', component: () => import('@/views/Finance.vue') },
      { path: 'taxes', name: 'Taxes', component: () => import('@/views/Taxes.vue') },
    { path: 'receipts', name: 'Receipts', component: () => import('@/views/Receipts.vue') },
    { path: 'labour', name: 'Labour', component: () => import('@/views/Labour.vue') },
    { path: 'archive', name: 'Archive', component: () => import('@/views/Archive.vue') },
    { path: 'reimbursement', name: 'Reimbursement', component: () => import('@/views/Reimbursement.vue') },
    { path: 'backup', name: 'Backup', component: () => import('@/views/Backup.vue') },
      { path: 'users', name: 'Users', component: () => import('@/views/Users.vue') },
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.name !== 'Login' && !token) next({ name: 'Login' })
  else next()
})

export default router
