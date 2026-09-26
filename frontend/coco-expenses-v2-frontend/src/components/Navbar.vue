<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import { useRoute, useRouter } from 'vue-router'
import { computed, watch, type Component } from 'vue'
import IconBell from '@/components/icons/IconBell.vue'

const userStore = useUserStore()
const notificationStore = useNotificationStore()
const router = useRouter()
const route = useRoute()

interface NavElement {
  text: string
  link?: string
  action?: () => void
  // Shown instead of the text in the desktop menu
  icon?: Component
  hasDot?: boolean
}

const navElements = computed<NavElement[]>(() => {
  return [
    { text: 'Expenses', link: '/expenses' },
    { text: 'Recurring Expenses', link: '/recurring-expenses' },
    { text: 'Categories', link: '/categories' },
    { text: 'Trips', link: '/trips' },
    { text: 'Statistics', link: '/statistics' },
    { text: 'Sharing', link: '/sharing' },
    ...(userStore.isLoggedIn
      ? [
          { text: 'Profile', link: '/profile' },
          {
            text: 'Notifications',
            link: '/notifications',
            icon: IconBell,
            hasDot: notificationStore.unreadCount > 0,
          },
          { text: 'Logout', action: handleLogout },
        ]
      : [
          { text: 'Login', link: '/login' },
          { text: 'Register', link: '/register' },
        ]),
  ]
})

watch(
  [() => route.fullPath, () => userStore.isLoggedIn],
  () => {
    if (userStore.isLoggedIn) {
      notificationStore.refreshUnreadCount()
    }
  },
  { immediate: true },
)

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="navbar bg-base-100 shadow-sm">
    <div class="navbar-start">
      <div class="dropdown">
        <div tabindex="0" role="button" class="btn btn-ghost lg:hidden">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h8m-8 6h16"
            />
          </svg>
        </div>
        <ul
          tabindex="0"
          class="menu menu-sm dropdown-content bg-base-100 rounded-box z-[1] mt-3 w-52 p-2 shadow"
        >
          <template v-for="navElement in navElements" :key="navElement.text">
            <li v-if="navElement.link">
              <router-link :to="navElement.link" active-class="active">
                {{ navElement.text }}
                <span v-if="navElement.hasDot" class="status status-error"></span>
              </router-link>
            </li>
            <li v-else-if="navElement.action">
              <a @click.prevent="navElement.action">{{ navElement.text }}</a>
            </li>
          </template>
        </ul>
      </div>
      <router-link to="/" class="btn btn-ghost text-xl">CocoExpenses</router-link>
    </div>
    <div class="navbar-end hidden lg:flex">
      <ul class="menu menu-horizontal px-1">
        <template v-for="navElement in navElements" :key="navElement.text">
          <li v-if="navElement.link">
            <router-link
              :to="navElement.link"
              active-class="active"
              :aria-label="navElement.icon ? navElement.text : undefined"
              :title="navElement.icon ? navElement.text : undefined"
            >
              <span v-if="navElement.icon" class="indicator">
                <span
                  v-if="navElement.hasDot"
                  class="indicator-item status status-error"
                ></span>
                <component :is="navElement.icon" class="h-5 w-5" />
              </span>
              <template v-else>{{ navElement.text }}</template>
            </router-link>
          </li>
          <li v-else-if="navElement.action">
            <a @click.prevent="navElement.action">{{ navElement.text }}</a>
          </li>
        </template>
      </ul>
    </div>
  </div>
</template>
