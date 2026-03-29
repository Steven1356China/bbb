import axios from 'axios'

const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:5000/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // token过期，跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default {
  // 用户相关
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getUserInfo: () => api.get('/users/me'),
  updateProfile: (data) => api.put('/users/profile', data),
  
  // 题目相关
  getProblems: (params) => api.get('/problems', { params }),
  getProblem: (id) => api.get(`/problems/${id}`),
  createProblem: (data) => api.post('/problems', data),
  updateProblem: (id, data) => api.put(`/problems/${id}`, data),
  getPendingProblems: () => api.get('/problems/admin/pending'),
  approveProblem: (id) => api.post(`/problems/admin/approve/${id}`),
  
  // 提交相关
  submitCode: (data) => api.post('/submissions', data),
  getSubmissions: (params) => api.get('/submissions', { params }),
  getSubmission: (id) => api.get(`/submissions/${id}`),
  getMySubmissions: (problemId) => api.get(`/submissions/my/${problemId}`),
  
  // 比赛相关
  getContests: (params) => api.get('/contests', { params }),
  getContest: (id) => api.get(`/contests/${id}`),
  createContest: (data) => api.post('/contests', data),
  joinContest: (id) => api.post(`/contests/${id}/join`),
  getContestRanking: (id) => api.get(`/contests/${id}/ranking`),
  
  // 标签
  getTags: () => api.get('/tags')
}
