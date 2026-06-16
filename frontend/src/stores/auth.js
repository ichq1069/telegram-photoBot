import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authAPI } from '@/api/endpoints'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')

  async function login(username, password) {
    const res = await authAPI.login(username, password)
    token.value = res.data.access_token
    localStorage.setItem('token', token.value)
    await fetchUser()
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await authAPI.getMe()
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { user, token, login, fetchUser, logout }
})
