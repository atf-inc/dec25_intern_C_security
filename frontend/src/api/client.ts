import axios from 'axios'

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    timeout: 30000,
    // Don't set default Content-Type - let axios handle it based on request data
})

// Request interceptor to set appropriate Content-Type
apiClient.interceptors.request.use(
    (config) => {
        // If data is FormData, don't set Content-Type (let browser set it with boundary)
        if (config.data instanceof FormData) {
            // Remove any Content-Type header for FormData
            delete config.headers['Content-Type']
        } else {
            // For non-FormData requests, set JSON content type
            config.headers['Content-Type'] = 'application/json'
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', error)
        return Promise.reject(error)
    }
)

export default apiClient
