import axios from 'axios'

// In dev, Vite proxies /api -> the Django backend (see vite.config.js).
// In prod, set VITE_API_BASE_URL to the deployed backend origin.
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({ baseURL })

function getTokens() {
  return {
    access: localStorage.getItem('cf_access'),
    refresh: localStorage.getItem('cf_refresh'),
  }
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem('cf_access', access)
  if (refresh) localStorage.setItem('cf_refresh', refresh)
}

export function clearTokens() {
  localStorage.removeItem('cf_access')
  localStorage.removeItem('cf_refresh')
}

api.interceptors.request.use((config) => {
  const { access } = getTokens()
  if (access) config.headers.Authorization = `Bearer ${access}`
  return config
})

let refreshingPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const isAuthEndpoint = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh')
    if (error.response?.status === 401 && !original._retry && !isAuthEndpoint) {
      original._retry = true
      const { refresh } = getTokens()
      if (!refresh) {
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(error)
      }
      try {
        if (!refreshingPromise) {
          refreshingPromise = axios
            .post(`${baseURL}/auth/refresh`, { refresh })
            .then((res) => {
              setTokens({ access: res.data.access })
              refreshingPromise = null
              return res.data.access
            })
            .catch((err) => {
              refreshingPromise = null
              throw err
            })
        }
        const newAccess = await refreshingPromise
        original.headers.Authorization = `Bearer ${newAccess}`
        return api(original)
      } catch {
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export default api
