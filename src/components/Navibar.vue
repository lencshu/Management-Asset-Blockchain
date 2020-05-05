<template>
  <div class="navbar">
    <el-menu
      :default-active="activeIndex"
      class="el-menu-demo"
      mode="horizontal"
      @select="handleSelect"
      background-color="#545c64"
      text-color="#fff"
      active-text-color="#ffd04b"
      router
    >
      <el-menu-item index='/'>Home</el-menu-item>
      <el-menu-item index="/ctrl">Control</el-menu-item>
      <el-menu-item index="/log">Log</el-menu-item>
      <el-submenu index="1">
          <template slot="title">API</template>
        <el-menu-item  index="/api">Frontend API</el-menu-item>
        <el-menu-item><a href="/api/docs" target="_blank">Backend API</a></el-menu-item>
      </el-submenu>
      <el-submenu index="2">
        <template slot="title" >Crypto Coins</template>
          <el-menu-item index="4-1">BTC</el-menu-item>
          <el-menu-item index="4-2">USDT</el-menu-item>
          <el-menu-item index="4-3">ETH(ERC20)</el-menu-item>
      </el-submenu>
    </el-menu>
  </div>
</template>
<script>
export default {
  name: 'Navibar',
  data () {
    return {
      activeIndex: '1'
    }
  },
  methods: {
    handleSelect (key, keyPath) {
      console.log(key, keyPath)
    }
  }
}
</script>
<style>
a {
font-weight: bold;
  color: #dad6d6;
  text-decoration: none;
  /* & > a */
  display: block;
}
</style>
