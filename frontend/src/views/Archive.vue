<template>
  <div>
    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">电子档案</span>
    </div>

    <!-- 面包屑导航 -->
    <div style="margin-bottom:12px;display:flex;align-items:center;gap:4px;flex-wrap:wrap">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item v-for="(crumb, i) in breadcrumbs" :key="i">
          <a v-if="i < breadcrumbs.length - 1" href="#" @click.prevent="navigateTo(crumb.path)">{{ crumb.label }}</a>
          <span v-else>{{ crumb.label }}</span>
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 工具栏 -->
    <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
      <el-input v-model="searchText" placeholder="搜索文件名..." clearable prefix-icon="Search" style="width:240px" @input="fetchList" />
      <el-upload :show-file-list="false" :before-upload="handleUpload" multiple>
        <el-button type="primary">上传文件</el-button>
      </el-upload>
      <el-button @click="showNewFolder = true">新建文件夹</el-button>
    </div>

    <!-- 文件列表 -->
    <el-table :data="archiveList" stripe border size="small" style="width:100%">
      <el-table-column label="名称" min-width="300">
        <template #default="{row}">
          <div v-if="row.is_directory" style="display:flex;align-items:center;gap:6px;cursor:pointer" @click="navigateTo(row)">
            <el-icon color="#E6A23C"><Folder /></el-icon>
            <span style="color:#409EFF">{{ row.name }}</span>
          </div>
          <div v-else style="display:flex;align-items:center;gap:6px;cursor:pointer" @click="previewFile(row)">
            <el-icon color="#409EFF"><Document /></el-icon>
            <span class="file-link">{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="100">
        <template #default="{row}">{{ row.is_directory ? '-' : (row.file_size_display || '-') }}</template>
      </el-table-column>
      <el-table-column label="类型" width="120">
        <template #default="{row}">{{ row.is_directory ? '文件夹' : (row.file_type || '-') }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{row}">
          <el-button v-if="!row.is_directory" text type="primary" size="small" @click="downloadFile(row)">下载</el-button>
          <el-popconfirm :title="`确定删除${row.is_directory?'此目录及所有子文件': '此文件'}？`" @confirm="delEntry(row.id)">
            <template #reference><el-button text type="danger" size="small">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreview" :title="previewTitle" width="90%" top="5vh" :fullscreen="previewType==='pdf'" destroy-on-close>
      <div style="min-height:400px;display:flex;justify-content:center;align-items:center;background:#f5f5f5;border-radius:4px;overflow:hidden">
        <!-- 图片 -->
        <img v-if="previewType==='image'" :src="previewSrc" style="max-width:100%;max-height:80vh;object-fit:contain" />
        <!-- PDF -->
        <iframe v-else-if="previewType==='pdf'" :src="previewSrc" style="width:100%;height:90vh;border:none"></iframe>
        <!-- Office (Word/Excel/PPT) via Office Online Viewer -->
        <iframe v-else-if="previewType==='office'" :src="officeViewerUrl" style="width:100%;height:90vh;border:none"></iframe>
        <!-- 文本 -->
        <pre v-else-if="previewType==='text'" style="width:100%;height:80vh;overflow:auto;margin:0;padding:16px;background:#fff;font-size:13px;white-space:pre-wrap;word-break:break-all">{{ previewText }}</pre>
        <!-- 不支持预览 -->
        <div v-else style="text-align:center;padding:40px;color:#999">
          <el-icon :size="48" color="#ccc"><Document /></el-icon>
          <p style="margin-top:12px">该格式不支持在线预览，请下载后查看</p>
          <el-button type="primary" @click="downloadPreviewFile">下载文件</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 新建文件夹对话框 -->
    <el-dialog v-model="showNewFolder" title="新建文件夹" width="400px">
      <el-form>
        <el-form-item label="文件夹名"><el-input v-model="folderName" placeholder="输入文件夹名称" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNewFolder=false">取消</el-button>
        <el-button type="primary" @click="createFolder">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.file-link { color:#409EFF; text-decoration:none; }
.file-link:hover { text-decoration:underline; }
</style>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Folder, Document, Search } from '@element-plus/icons-vue'
import request from '@/api/request'

const currentDir = ref('/')
const searchText = ref('')
const archiveList = ref([])
const showNewFolder = ref(false)
const folderName = ref('')

// Preview state
const showPreview = ref(false)
const previewTitle = ref('')
const previewSrc = ref('')
const previewType = ref('') // image | pdf | office | text | ''
const previewText = ref('')
const previewFileRow = ref(null)

const officeViewerUrl = computed(() => {
  if (!previewSrc.value) return ''
  return `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(previewSrc.value)}`
})

const breadcrumbs = computed(() => {
  const parts = currentDir.value.split('/').filter(Boolean)
  const crumbs = [{ label: '根目录', path: '/' }]
  let path = ''
  for (const p of parts) {
    path += p + '/'
    crumbs.push({ label: p, path })
  }
  return crumbs
})

function navigateTo(dir) {
  if (typeof dir === 'string') {
    currentDir.value = dir
  } else {
    currentDir.value = dir.directory + dir.name + '/'
  }
  searchText.value = ''
  fetchList()
}

async function fetchList() {
  try {
    const params = { directory: currentDir.value }
    if (searchText.value) params.search = searchText.value
    archiveList.value = await request.get('/archive', { params })
  } catch { archiveList.value = [] }
}

async function handleUpload(file) {
  const form = new FormData()
  form.append('file', file)
  form.append('directory', currentDir.value)
  try {
    await request.post('/archive/upload', form)
    ElMessage.success(`上传成功: ${file.name}`)
    fetchList()
  } catch { ElMessage.error('上传失败') }
  return false
}

async function createFolder() {
  if (!folderName.value) return ElMessage.warning('请输入文件夹名')
  const form = new FormData()
  form.append('name', folderName.value)
  form.append('directory', currentDir.value)
  try {
    await request.post('/archive/directory', form)
    ElMessage.success('文件夹已创建')
    showNewFolder.value = false
    folderName.value = ''
    fetchList()
  } catch { ElMessage.error('创建失败，可能名称已存在') }
}

function detectPreviewType(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  if (['jpg','jpeg','png','gif','webp','svg','bmp','ico','avif'].includes(ext)) return 'image'
  if (ext === 'pdf') return 'pdf'
  if (['doc','docx','xls','xlsx','ppt','pptx'].includes(ext)) return 'office'
  if (['txt','md','json','xml','csv','log','ini','cfg','yaml','yml','toml',
       'js','ts','py','java','c','cpp','h','hpp','rs','go','rb','php',
       'html','htm','css','scss','less','vue','svelte','sql','sh','bat',
       'env','gitignore','dockerfile','makefile'].includes(ext)) return 'text'
  return null
}

async function previewFile(row) {
  previewFileRow.value = row
  previewTitle.value = row.original_filename || row.name
  const type = detectPreviewType(row.original_filename || row.name)
  previewType.value = type || ''

  if (type === 'image') {
    // 图片通过 axios blob 获取（自动 baseURL + Authorization header），创建 objectURL
    try {
      const res = await request.get(`/archive/preview/${row.id}`, { responseType: 'blob' })
      previewSrc.value = URL.createObjectURL(res)
      showPreview.value = true
    } catch (e) {
      console.error('Preview error:', e)
      ElMessage.error('预览失败: ' + (e?.message || e?.detail || '未知错误'))
    }
  } else if (type === 'pdf') {
    try {
      const res = await request.get(`/archive/preview/${row.id}`, { responseType: 'blob' })
      previewSrc.value = URL.createObjectURL(res)
      showPreview.value = true
    } catch (e) {
      console.error('Preview error:', e)
      ElMessage.error('预览失败')
    }
  } else if (type === 'office') {
    // Office 文件通过 Office Online Viewer 预览（部署到 VPS 后可用）
    const token = localStorage.getItem('token')
    previewSrc.value = `${window.location.origin}/api/v1/archive/preview/${row.id}?token=${encodeURIComponent(token)}`
    showPreview.value = true
  } else if (type === 'text') {
    try {
      const res = await request.get(`/archive/preview/${row.id}`, { responseType: 'blob' })
      previewText.value = await res.text()
      showPreview.value = true
    } catch { ElMessage.error('预览失败') }
  } else {
    previewText.value = ''
    showPreview.value = true
  }
}

async function downloadPreviewFile() {
  if (previewFileRow.value) await downloadFile(previewFileRow.value)
}

async function downloadFile(row) {
  try {
    const res = await request.get(`/archive/download/${row.id}`, { responseType: 'blob' })
    const blob = new Blob([res], { type: row.file_type || 'application/octet-stream' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = row.original_filename || row.name
    a.click()
    URL.revokeObjectURL(a.href)
  } catch { ElMessage.error('下载失败') }
}

async function delEntry(id) {
  try {
    await request.delete(`/archive/${id}`)
    ElMessage.success('已删除')
    fetchList()
  } catch { ElMessage.error('删除失败') }
}

onMounted(fetchList)
</script>
