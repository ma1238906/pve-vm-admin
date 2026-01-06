import { defineStore } from 'pinia'
import request from '../api/request'
import { jwtDecode } from "jwt-decode";

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.is_superuser
  },
  actions: {
    async login(username, password) {
        // FastAPI expects form data for OAuth2
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const res = await request.post('/auth/login/access-token', formData)
        this.token = res.access_token
        localStorage.setItem('token', this.token)
        await this.fetchUser()
    },
    async fetchUser() {
        if (!this.token) return
        try {
            const res = await request.get('/users/me')
            this.user = res
        } catch (e) {
            this.logout()
        }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    }
  }
})
