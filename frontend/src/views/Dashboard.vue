<template>
  <div class="dashboard">
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6" v-for="card in cards" :key="card.label">
        <el-card shadow="hover">
          <div class="stat-value" :style="{color:card.color}">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="12"><el-card><div ref="chartRef" style="height:320px"></div></el-card></el-col>
      <el-col :span="12"><el-card><div ref="pieRef" style="height:320px"></div></el-card></el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import request from '@/api/request'
import * as echarts from 'echarts'

const chartRef = ref(null)
const pieRef = ref(null)
const cards = ref([])
let chart = null, pie = null

async function fetchData() {
  try {
    const d = await request.get('/dashboard/summary')
    cards.value = [
      { label: '总收入', value: `¥${(d.total_revenue/10000).toFixed(1)}万`, color: '#67C23A' },
      { label: '应收余额', value: `¥${(d.total_receivable/10000).toFixed(1)}万`, color: '#E6A23C' },
      { label: '应付余额', value: `¥${(d.total_payable/10000).toFixed(1)}万`, color: '#F56C6C' },
      { label: '项目数', value: `${d.project_count}`, color: '#409EFF' },
    ]
    renderChart(d)
  } catch {}
}

function renderChart(d) {
  nextTick(() => {
    if (chartRef.value) {
      chart?.dispose()
      chart = echarts.init(chartRef.value)
      chart.setOption({
        tooltip: {},
        xAxis: { type: 'category', data: ['收入', '应收', '应付'] },
        yAxis: { type: 'value', axisLabel: { formatter: v => (v/10000)+'万' } },
        series: [{ type: 'bar', data: [d.total_revenue, d.total_receivable, d.total_payable], itemStyle: { borderRadius: [4,4,0,0] } }]
      })
    }
    if (pieRef.value) {
      pie?.dispose()
      pie = echarts.init(pieRef.value)
      pie.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: ¥{c}' },
        series: [{
          type: 'pie', radius: ['40%','70%'],
          data: [
            { name: '已回款', value: d.total_revenue - d.total_receivable, itemStyle: { color: '#67C23A' } },
            { name: '未回款', value: d.total_receivable, itemStyle: { color: '#E6A23C' } },
          ]
        }]
      })
    }
  })
}

onMounted(fetchData)
onUnmounted(() => { chart?.dispose(); pie?.dispose() })
</script>

<style scoped>
.stat-value { font-size: 28px; font-weight: bold; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
</style>
