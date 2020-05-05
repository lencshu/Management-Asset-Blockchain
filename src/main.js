import Vue from 'vue'
import App from './App'
import router from './router'
import store from './store'
import { ButtonGroup, Container, Row, Col, Button, DatePicker, Menu, Submenu, MenuItem, Table, TableColumn, Progress, Tag, Card } from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import './filters'

Vue.config.productionTip = false

Vue.use(Card)
Vue.use(Tag)
Vue.use(Progress)
Vue.use(ButtonGroup)
Vue.use(Container)
Vue.use(Row)
Vue.use(Col)
Vue.use(Button)
Vue.use(DatePicker)
Vue.use(Menu)
Vue.use(Submenu)
Vue.use(MenuItem)
Vue.use(Table)
Vue.use(TableColumn)

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
