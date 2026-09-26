import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiFetch from '@/utils/apiFetch'
import type { Notification } from '@/interfaces/Notification'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)

  async function refreshUnreadCount() {
    const response = await apiFetch('/expenses/notifications/unread-count/')
    if (response.ok) {
      unreadCount.value = (await response.json()).count
    }
  }

  async function markRead(notificationId: number): Promise<Notification | null> {
    const response = await apiFetch(`/expenses/notifications/${notificationId}/read/`, {
      method: 'POST',
    })
    await refreshUnreadCount()
    return response.ok ? await response.json() : null
  }

  return { unreadCount, refreshUnreadCount, markRead }
})
