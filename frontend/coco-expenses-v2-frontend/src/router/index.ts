import { createRouter, createWebHistory } from 'vue-router'
import LoginPage from '@/views/LoginPage.vue'
import RegisterPage from '@/views/RegisterPage.vue'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/expenses',
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('@/views/AboutView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage,
      meta: { isOpen: true },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterPage,
      meta: { isOpen: true },
    },
    {
      path: '/expenses',
      name: 'expenses',
      component: () => import('@/views/ExpensesView.vue'),
    },
    {
      path: '/recurring-expenses',
      name: 'recurring-expenses',
      component: () => import('@/views/RecurringExpensesView.vue'),
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: () => import('@/views/StatisticsView.vue'),
    },
    {
      path: '/trips',
      name: 'trips',
      component: () => import('@/views/TripsView.vue'),
    },
    {
      path: '/categories',
      name: 'categories',
      component: () => import('@/views/CategoriesView.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
    },
    {
      path: '/import-expenses-from-csv',
      name: 'import-expenses-from-csv',
      component: () => import('@/views/ImportExpensesFromCsv.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const user = useUserStore()

  await user.checkAuthStatus()

  // If the route requires auth and user is not logged in
  if (!to.meta.isOpen && !user.isLoggedIn) {
    return {
      name: 'login',
      // Optional: Save the location they were trying to go to
      query: { redirect: to.fullPath },
    }
  }
})

export default router
