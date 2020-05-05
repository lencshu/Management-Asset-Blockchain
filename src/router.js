import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home'
import Api from './views/Api'
import log from './views/Log'
import Ctrl from './views/Ctrl'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/api',
      name: 'api',
      component: Api
    },
    {
      path: '/log',
      name: 'log',
      component: log
    },
    {
      path: '/ctrl',
      name: 'ctrl',
      component: Ctrl
    }
  ]
})
