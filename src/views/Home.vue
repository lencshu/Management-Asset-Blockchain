<template>
  <div class="home">
    <HelloWorld msg="Sepoch Python V2.0" />
  </div>
</template>

<script>
// @ is an alias to /src
import HelloWorld from '@/components/HelloWorld'

export default {
  name: 'home',
  components: {
    HelloWorld
  }
}
</script>

<style lang="scss">
</style>
