<template>
  <div>
    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">系统数据备份</span>
      <el-button type="primary" :loading="creating" @click="createBackup">创建备份</el-button>
    </div>

    <el-alert title="备份会创建当前数据库的快照文件，仅管理员可操作。" type="info" show-icon :closable="false" style="margin-bottom:12px" />

    <el-table :data="backupList" stripe border size="small" style="width:100%">
      <el-table-column prop="filename" label="文件名" min-width="250" />
      <el-table-column prop="size_display" label="大小" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="150">
        <template #default="{row}">
          <div style="display:flex;gap:4px;align-items:center">
            <el-button text type="primary" size="small" @click="downloadBackup(row)">下载</el-button>
            <el-popconfirm title="确定删除此备份？" @confirm="deleteBackup(row.filename)">
              <template #reference><el-button text type="danger" size="small">删除</el-button></template>
            </el-popconfirm>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="!backupList.length && !loading" style="text-align:center;padding:40px;color:#999">
      暂无备份，点击上方"创建备份"按钮生成。
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const backupList = ref([])
const loading = ref(false)
const creating = ref(false)

async function fetchList() {
  loading.value = true
  try { backupList.value = await request.get('/backup') } catch { backupList.value = [] }
  loading.value = false
}

async function createBackup() {
  creating.value = true
  try {
    const res = await request.post('/backup')
    ElMessage.success(`备份成功: ${res.filename} (${res.size_display})`)
    fetchList()
  } catch { ElMessage.error('备份失败') }
  creating.value = false
}

async function downloadBackup(row) {
  try {
    const res = await request.get(`/backup/download/${row.filename}`, { responseType: 'blob' })
    const blob = new Blob([res], { type: 'application/octet-stream' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = row.filename
    a.click()
    URL.revokeObjectURL(a.href)
  } catch { ElMessage.error('下载失败') }
}

async function deleteBackup(filename) {
  try {
    await request.delete(`/backup/${filename}`)
    ElMessage.success('已删除')
    fetchList()
  } catch { ElMessage.error('删除失败') }
}

onMounted(fetchList)
</script>
