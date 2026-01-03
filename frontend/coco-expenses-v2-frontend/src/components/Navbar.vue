<script setup lang="ts">
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { computed } from 'vue'

const userStore = useUserStore()
const router = useRouter()

interface NavElement {
  text: string
  link?: string
  action?: () => void
}

const navElements = computed<NavElement[]>(() => {
  return [
    { text: 'Expenses', link: '/expenses' },
    { text: 'Recurring Expenses', link: '/recurring-expenses' },
    { text: 'Categories', link: '/categories' },
    { text: 'Trips', link: '/trips' },
    { text: 'Statistics', link: '/statistics' },
    ...(userStore.isLoggedIn
      ? [
          { text: 'Profile', link: '/profile' },
          { text: 'Logout', action: handleLogout },
        ]
      : [
          { text: 'Login', link: '/login' },
          { text: 'Register', link: '/register' },
        ]),
  ]
})

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
              <router-link :to="navElement.link" active-class="active">{{
                navElement.text
              }}</router-link>
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
            <router-link :to="navElement.link" active-class="active">{{
              navElement.text
            }}</router-link>
          </li>
          <li v-else-if="navElement.action">
            <a @click.prevent="navElement.action">{{ navElement.text }}</a>
          </li>
        </template>
      </ul>
    </div>
  </div>
</template>
