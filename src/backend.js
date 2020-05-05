import axios from 'axios'

let $axios = axios.create({
  baseURL: '/api/',
  timeout: 5000,
  headers: { 'Content-Type': 'application/json' }
})

// Request Interceptor
$axios.interceptors.request.use(function (config) {
  config.headers['Authorization'] = 'Fake Token'
  return config
})

// Response Interceptor to handle and log errors
$axios.interceptors.response.use(function (response) {
  return response
}, function (error) {
  // Handle Error
  console.log(error)
  return Promise.reject(error)
})

export default {
  getStatus () {
    return $axios.get('status/')
      .then(response => response.data)
  },
  infiniteHandler ($state, tableName) {
    $axios.get('read/' + tableName, {
      params: {
        page: this.page
      }
    }).then(({ data }) => {
      if (data.length) {
        this.page += 1
        this.list = this.list.concat(data.result.hits)
        $state.loaded()
      } else {
        $state.complete()
      }
    })
  },

  fetchTable (tableName) {
    console.log('read/' + tableName)
    return $axios.get('read/' + tableName)
      .then(response => response.data)
  },

  fetchTableDate (tableName, start, end) {
    console.log('read/' + tableName)
    return $axios.post('read/' + tableName, {
      start: start,
      end: end
    })
      .then(response => response.data)
  },

  fetchSecureResource () {
    return $axios.get(`fus/secure-resource/zzz`)
      .then(response => response.data)
  }
}
