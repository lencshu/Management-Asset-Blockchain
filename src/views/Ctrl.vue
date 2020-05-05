<template>
  <div class="ctrl">
    <el-row type="flex" justify="space-around" :gutter="20">
      <el-col :span="4">
        <a href="/api/start" target="_blank">
          <el-button type="warning" round>Start All</el-button>
        </a>
      </el-col>
      <el-col :span="4">
        <a href="/api/stop" target="_blank">
          <el-button type="danger" round>Stop All</el-button>
        </a>
      </el-col>
    </el-row>
    <el-row >
      <el-col :span="12" :xs="24">
        <CtrlUnit :statusProcessOne="statusProcess.Btc"/>
      </el-col>
      <el-col :span="12" :xs="24">
        <CtrlUnit :statusProcessOne="statusProcess.Usdt"/>
      </el-col>
    </el-row>
    <el-row >
      <el-col :span="12" :xs="24">
        <CtrlUnit :statusProcessOne="statusProcess.Eth"/>
      </el-col>
      <el-col :span="12" :xs="24">
        <CtrlUnit :statusProcessOne="statusProcess.Asset"/>
      </el-col>
    </el-row>
    <el-row >
      <el-col :span="12" :xs="24">
        <CtrlUnit :statusProcessOne="statusProcess.SQL"/>
      </el-col>
    </el-row>
  </div>
</template>
<script>
import $backend from '../backend'
import CtrlUnit from '@/components/CtrlUnit'
export default {
  name: 'ctrl',
  components: {
    CtrlUnit
  },
  beforeDestroy () {
    clearInterval(this.timer)
  },
  created () {
    this.getStatus()
    this.timer = setInterval(() => {
      this.getStatus()
    }, 3000)
  },
  methods: {
    cancelAutoUpdate () { clearInterval(this.timer) },
    getStatus () {
      $backend
        .getStatus()
        .then(responseData => {
          console.log(responseData.status)
          this.statusProcess = responseData.status
        })
    }
  },
  data () {
    return {
      timer: '',
      statusProcess: {
        'SQL': {
          'process': 'SQL',
          'alive': false,
          'lastRun': 1586046782.79623,
          'progress': 0
        },
        'Btc': {
          'process': 'Btc',
          'alive': false,
          'lastRun': 1586046782.7962613,
          'progress': 0
        },
        'Eth': {
          'process': 'Eth',
          'alive': false,
          'lastRun': 1586046782.7962754,
          'progress': 0
        },
        'Usdt': {
          'process': 'Usdt',
          'alive': false,
          'lastRun': 1586046782.7962875,
          'progress': 0
        },
        'Asset': {
          'process': 'Asset',
          'alive': false,
          'lastRun': 1586046782.7962973,
          'progress': 0
        }
      }
    }
  }
}
</script>
<style>
.el-row {
  margin-bottom: 20px;
}
.el-col {
  border-radius: 4px;
}
.bg-purple-dark {
  background: #99a9bf;
}
.bg-purple {
  background: #d3dce6;
}
.bg-purple-light {
  background: #e5e9f2;
}
.grid-content {
  border-radius: 4px;
  min-height: 36px;
}
.row-bg {
  padding: 10px 0;
  background-color: #f9fafc;
}
</style>
