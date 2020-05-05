<template>
  <div class="about">
    <h1>Call Demo</h1>
    <a href @click.prevent="fetchTable('btc')">Fetch</a>
    <br />
    <a href @click.prevent="fetchSecureResource">Secure Resource</a>
    <h4>Results</h4>
    <p v-for="r in resources" :key="r">
      {{r.result}}
      <!-- Server Timestamp: {{r.timestamp | formatTimestamp }} -->
    </p>
    <p>{{error}}</p>
  </div>
</template>

<script>
import $backend from '../backend'

export default {
  name: 'about',
  data () {
    return {
      resources: [],
      error: ''
    }
  },
  methods: {
    fetchTable (tableName) {
      $backend
        .fetchTable(tableName)
        .then(responseData => {
          console.log(responseData.result)
          this.resources.push(responseData)
        })
        .catch(error => {
          this.error = error.message
        })
    },
    fetchSecureResource () {
      $backend
        .fetchSecureResource()
        .then(responseData => {
          this.resources.push(responseData)
        })
        .catch(error => {
          this.error = error.message
        })
    }
  }
}
</script>

<style lang="scss">
</style>
