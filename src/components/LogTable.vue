<template>
  <div class="logtable">
    <el-row :gutter="20" style="padding:20px">
      <el-col :span="4" :xs="24">
        <el-button @click="resetDateFilter">Date</el-button>
        <el-button @click="clearFilter">All</el-button>
      </el-col>
      <el-col :span="12" :xs="24">
        <el-button-group>
          <el-button type="primary" round plain @click.prevent="fetchTable('btc')">BTC</el-button>
          <el-button type="primary" round plain @click.prevent="fetchTable('usdt')">USDT</el-button>
          <el-button type="primary" round plain @click.prevent="fetchTable('eth')">ETH</el-button>
          <el-button type="primary" round plain @click.prevent="fetchTable('sql')">SQL</el-button>
          <el-button type="primary" round plain @click.prevent="fetchTable('asset')">ASSET</el-button>
        </el-button-group>
      </el-col>
      <el-col :span="4" :xs="24">
        <DatePicker @pick="show" />
      </el-col>
    </el-row>
    <el-table
      border
      :data="tableData"
      ref="filterTable"
      :row-class-name="tableRowClassName"
    >
      >
      <el-table-column prop="id" label="ID" sortable width="66" column-key="id"></el-table-column>
      <el-table-column
        prop="type"
        label="Type"
        sortable
        width="98"
        :filters="[
          { text: 'Error', value: 'err' },
          { text: 'Info', value: 'info' },
          { text: 'Success', value: 'success' },
        ]"
        :filter-method="filterHandler"
      ></el-table-column>
      <el-table-column prop="function" label="Function" width="212" sortable></el-table-column>
      <el-table-column prop="data" label="Logging"></el-table-column>
      <el-table-column
        prop="date"
        label="Date"
        sortable
        :formatter="formatter"
        width="250"
      ></el-table-column>
      <!-- <infinite-loading
      slot="append"
      @infinite="infiniteHandler"
      force-use-infinite-wrapper=".el-table__body-wrapper">
    </infinite-loading> -->
    </el-table>
  </div>
</template>
<script>
import DatePicker from '@/components/DatePicker'
import $backend from '../backend'
// import InfiniteLoading from 'vue-infinite-loading'
export default {
  components: {
    DatePicker
    // InfiniteLoading
  },
  data () {
    return {
      tableData: [],
      endTime: (new Date()).getTime() / 1000,
      startTime: ((new Date()).getTime() - 3600 * 1000 * 24) / 1000,
      // page: 1,
      error: ''
      // tableData: [{
      //   id: 1,
      //   type: 'err',
      //   function: 'main',
      //   data: 'asdsad',
      //   date: 1585435388.3053575
      // }, {
      //   id: 2,
      //   type: 'info',
      //   function: 'main',
      //   data: 'asdsad',
      //   date: 1585435388.3053575
      // }, {
      //   id: 2,
      //   type: 'success',
      //   function: 'func',
      //   data: 'asdsad',
      //   date: 1585435344.3053575
      // }]
    }
  },
  methods: {
    // infiniteHandler ($state) {
    //   $backend
    //     .infiniteHandler($state, 'btc')
    // },
    show (info) {
      // console.log(info[1].getTime())
      this.startTime = info[0].getTime() / 1000
      this.endTime = info[1].getTime() / 1000
    },
    fetchTable (tableName) {
      // console.log(this.startTime, this.endTime)
      // console.log((this.startTime * 1000).toLocaleString(), (this.endTime * 1000).toLocaleString())
      $backend
        .fetchTableDate(tableName, this.startTime, this.endTime)
        .then(responseData => {
          var rawData = responseData.result
          var dictData = []
          for (let index = 0; index < rawData.length; index++) {
            const element = rawData[index]
            // console.log(element)
            dictData.push({
              id: element[0],
              type: element[1],
              function: element[2],
              data: element[3],
              date: element[4]
            })
          }
          this.tableData = dictData
        // console.log(this.tableData)
        })
        .catch(error => {
          this.error = error.message
        })
    },
    tableRowClassName ({ row, rowIndex }) {
    // console.log(row)
      if (row.type === 'err') {
        return 'error-row'
      } else if (row.type === 'success') {
        return 'success-row'
      }
      return ''
    },
    resetDateFilter () {
      this.$refs.filterTable.clearFilter('date')
    },
    clearFilter () {
      this.$refs.filterTable.clearFilter()
    },
    formatter (row, column) {
    // console.log(row.date)
      var dateOb = new Date(row.date * 1000)
      return dateOb.toLocaleString()
    },
    filterTag (value, row) {
      return row.tag === value
    },
    filterHandler (value, row, column) {
      const property = column['property']
      return row[property] === value
    }
  }
}
</script>

<style>
.el-table .error-row {
  background: rgb(255, 164, 164);
}
.el-table {
  width: 100%;
  height: 100%;
}
.el-table .success-row {
  background: #d4fbbe;
}
</style>
