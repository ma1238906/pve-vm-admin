import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const service = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 5000
})

service.interceptors.request.use(
  config => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers['Authorization'] = `Bearer ${authStore.token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    return Promise.reject(error)
  }
)

export default service
