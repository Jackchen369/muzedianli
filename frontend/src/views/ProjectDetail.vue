<template>
  <div v-if="project">
    <el-button text @click="$router.push('/projects')">< 返回项目列表</el-button>

    <!-- 基本信息 -->
    <el-card style="margin-top:12px">
      <template #header><span style="font-size:18px;font-weight:bold">{{ project.name }}</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="项目状态"><el-tag size="small">{{ project.status }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="合同金额">¥{{ (project.contract_amount/10000).toFixed(1) }}万</el-descriptions-item>
        <el-descriptions-item label="业主">{{ ownerName }}</el-descriptions-item>
        <el-descriptions-item label="中标单位">{{ bidUnitName }}</el-descriptions-item>
        <el-descriptions-item label="合同签订日期">{{ project.contract_sign_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="计划开工日期">{{ project.start_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="计划竣工日期">{{ project.end_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="实际开工日期">{{ project.actual_start_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="实际竣工日期">{{ project.actual_end_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="预算金额">{{ project.budget_amount ? '¥'+(project.budget_amount/10000).toFixed(1)+'万' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="送审定案金额"><span style="color:#E6A23C;font-weight:bold">{{ project.settlement_amount ? '¥'+(project.settlement_amount/10000).toFixed(1)+'万' : '-' }}</span></el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ project.created_at }}</el-descriptions-item>
        <el-descriptions-item label="项目编号">{{ project.project_code || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 总包合同文件 -->
    <el-card style="margin-top:12px">
      <template #header>
        <span style="font-weight:bold">总包合同文件</span>
        <el-button size="small" type="primary" style="float:right" @click="openUpload(null)">上传合同</el-button>
      </template>
      <el-table v-if="mainFiles.length>0" :data="mainFiles" stripe size="small">
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column label="类型" width="80"><template #default="{row}"><el-tag size="small">{{ row.filetype }}</el-tag></template></el-table-column>
        <el-table-column label="大小" width="80"><template #default="{row}">{{ (row.filesize/1024).toFixed(1) }}KB</template></el-table-column>
        <el-table-column label="上传时间" width="160"><template #default="{row}">{{ row.created_at }}</template></el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{row}">
            <el-button text type="primary" size="small" @click="downloadFile(row)">下载</el-button>
            <el-popconfirm title="确定删除？" @confirm="deleteFile(row)"><template #reference><el-button text type="danger" size="small">删除</el-button></template></el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无总包合同" style="padding:16px" />
    </el-card>

    <!-- 分包单位 -->
    <el-card style="margin-top:12px">
      <template #header><span style="font-weight:bold">分包单位 ({{ subs.length }}家)</span></template>
      <div v-if="subs.length===0" style="padding:16px;text-align:center;color:#999">暂无分包单位</div>
      <div v-for="sub in subs" :key="sub.id" style="border:1px solid #ebeef5;border-radius:6px;padding:12px;margin-bottom:8px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <el-tag type="warning">{{ sub.partner_name }}</el-tag>
          <div>
            <el-button size="small" type="primary" @click="openUpload(sub.partner_id, sub.partner_name)">上传分包合同</el-button>
            <el-popconfirm title="移除该分包单位？" @confirm="removeSub(sub.id)"><template #reference><el-button size="small" type="danger" text>移除</el-button></template></el-popconfirm>
          </div>
        </div>
        <el-table v-if="subFilesMap[sub.partner_id]?.length" :data="subFilesMap[sub.partner_id]" stripe size="small">
          <el-table-column prop="filename" label="合同文件" min-width="200" />
          <el-table-column label="类型" width="80"><template #default="{row}"><el-tag size="small">{{ row.filetype }}</el-tag></template></el-table-column>
          <el-table-column label="大小" width="80"><template #default="{row}">{{ (row.filesize/1024).toFixed(1) }}KB</template></el-table-column>
          <el-table-column label="上传时间" width="160"><template #default="{row}">{{ row.created_at }}</template></el-table-column>
          <el-table-column label="操作" width="140">
            <template #default="{row}">
              <el-button text type="primary" size="small" @click="downloadFile(row)">下载</el-button>
              <el-popconfirm title="确定删除？" @confirm="deleteFile(row)"><template #reference><el-button text type="danger" size="small">删除</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无分包合同" style="padding:8px" :image-size="60" />
      </div>
    </el-card>

    <!-- 利润核算 -->
    <el-row :gutter="16" style="margin-top:12px">
      <el-col :span="8" v-for="item in profitCards" :key="item.label">
        <el-card shadow="hover"><div class="pv" :style="{color:item.color}">{{ item.value }}</div><div class="pl">{{ item.label }}</div></el-card>
      </el-col>
    </el-row>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUpload" :title="uploadTitle" width="450px">
      <el-upload drag :action="uploadUrl" :headers="uploadHeaders" :data="uploadData" :on-success="onUploadSuccess" :on-error="onUploadError" multiple>
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处，或<em>点击选择</em></div>
        <template #tip><div class="el-upload__tip">支持 PDF / Word / Excel / 图片 格式</div></template>
      </el-upload>
      <template #footer><el-button @click="showUpload=false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import request from '@/api/request'

const route = useRoute()
const project = ref(null)
const profit = ref(null)
const ownerMap = ref({})
const partnerMap = ref({})
const subs = ref([])
const allFiles = ref([])
const mainFiles = computed(() => allFiles.value.filter(f => !f.partner_id))
const subFilesMap = ref({})
const showUpload = ref(false)
const uploadPid = ref(null)
const uploadPname = ref('')
const uploadTitle = computed(() => uploadPid.value ? `上传分包合同 - ${uploadPname.value}` : '上传总包合同')

const ownerName = computed(() => ownerMap.value[project.value?.owner_id] || '')
const bidUnitName = computed(() => partnerMap.value[project.value?.winning_bid_unit_id] || '-')
const token = computed(() => localStorage.getItem('token') || '')
const uploadUrl = computed(() => `/api/v1/files/upload/${route.params.id}`)
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${token.value}` }))
const uploadData = computed(() => uploadPid.value ? { partner_id: uploadPid.value } : {})

const profitCards = computed(() => [
  { label: '总收入', value: `¥${((profit.value?.total_income||0)/10000).toFixed(1)}万`, color: '#67C23A' },
  { label: '总成本', value: `¥${(((profit.value?.total_invoice_cost||0)+(profit.value?.total_other_cost||0))/10000).toFixed(1)}万`, color: '#F56C6C' },
  { label: '净利润', value: `¥${((profit.value?.profit||0)/10000).toFixed(1)}万`, color: profit.value?.profit >= 0 ? '#67C23A' : '#F56C6C' },
])

function openUpload(partnerId, partnerName) {
  uploadPid.value = partnerId; uploadPname.value = partnerName || ''
  showUpload.value = true
}
function onUploadSuccess() { ElMessage.success('上传成功'); showUpload.value = false; fetchData() }

async function fetchData() {
  try {
    const [pj, partners, subList, files] = await Promise.all([
      request.get(`/projects/${route.params.id}`),
      request.get('/partners'),
      request.get(`/subcontractors/${route.params.id}`),
      request.get(`/files/list/${route.params.id}`),
    ])
    project.value = pj
    partners.forEach(p => { ownerMap.value[p.id] = p.name; partnerMap.value[p.id] = p.name })
    subs.value = subList
    allFiles.value = files
    // Group files by partner_id
    const map = {}
    files.forEach(f => {
      if (f.partner_id) {
        if (!map[f.partner_id]) map[f.partner_id] = []
        map[f.partner_id].push(f)
      }
    })
    subFilesMap.value = map
    profit.value = await request.get(`/projects/${route.params.id}/profit`)
  } catch {}
}

async function downloadFile(f) {
  try {
    const resp = await fetch(`/api/v1/files/download/${f.id}`, { headers: { Authorization: `Bearer ${token.value}` } })
    if (!resp.ok) throw Error()
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = f.filename
    document.body.appendChild(a); a.click()
    document.body.removeChild(a); URL.revokeObjectURL(url)
  } catch { ElMessage.error('下载失败') }
}
async function deleteFile(f) { await request.delete(`/files/${f.id}`); ElMessage.success('删除成功'); fetchData() }
async function removeSub(id) { await request.delete(`/subcontractors/${id}`); ElMessage.success('已移除'); fetchData() }

onMounted(fetchData)
</script>

<style scoped>
.pv { font-size:24px; font-weight:bold; }
.pl { font-size:13px; color:#909399; margin-top:4px; }
</style>
