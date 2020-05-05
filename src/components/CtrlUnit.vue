<template>
  <el-card shadow="hover" style="padding: 20px; margin: 20px;">
    <div slot="header" class="clearfix">
      <span>{{ statusProcessOne.name }} Process :</span>
      <span v-if="statusProcessOne.alive">Running</span>
      <span v-else>Waiting</span>
    </div>
    <el-row>
      <el-col :span="20">
        <div style="padding: 10px;">
          Last Run Time:
          {{ new Date(statusProcessOne.lastRun * 1000).toLocaleString() }}
        </div>
      </el-col>
      <el-col :span="4">
        <el-button @click="stopLink()" type="danger">Stop</el-button>
      </el-col>
    </el-row>
    <el-progress v-if="statusProcessOne.active" :text-inside="true" :stroke-width="38" :percentage="statusProcessOne.progress"></el-progress>
    <el-progress v-else status="exception" :text-inside="true" :stroke-width="38" :percentage="100"></el-progress>
  </el-card>
</template>
<script>
export default {
  props: ['statusProcessOne'],
  methods: {
    stopLink () {
      window.location = 'api/stop/' + this.statusProcessOne.name
    }
  }
}
</script>
