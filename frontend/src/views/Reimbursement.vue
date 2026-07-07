<template>
  <div>
    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">报销管理</span>
    </div>

    <!-- 工具栏 -->
    <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap">
      <el-select v-model="filterStatus" clearable placeholder="审核状态" style="width:130px" @change="fetchList">
        <el-option label="待审核" value="待审核" />
        <el-option label="已通过" value="已通过" />
        <el-option label="已付款" value="已付款" />
        <el-option label="已驳回" value="已驳回" />
      </el-select>
      <el-input v-model="filterApplicant" placeholder="搜索报销人..." clearable prefix-icon="Search" style="width:200px" @input="fetchList" />
      <el-button type="primary" @click="openCreate">新增报销</el-button>
    </div>

    <!-- 报销列表 -->
    <el-table :data="list" stripe border size="small" style="width:100%">
      <el-table-column prop="applicant" label="报销人" width="80" />
      <el-table-column prop="expense_type" label="类型" width="80" />
      <el-table-column label="金额" width="100"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
      <el-table-column prop="description" label="费用说明" min-width="130" show-overflow-tooltip />
      <el-table-column label="凭证" width="70">
        <template #default="{row}">
          <el-button v-if="row.receipt_urls" text type="primary" size="small" @click="viewReceipts(row)">{{ formatReceipts(row.receipt_urls).length }}个</el-button>
          <span v-else style="color:#999">-</span>
        </template>
      </el-table-column>
      <el-table-column label="开户行" width="100"><template #default="{row}">{{ row.bank_name || '-' }}</template></el-table-column>
      <el-table-column label="银行账号" width="120"><template #default="{row}">{{ row.bank_account || '-' }}</template></el-table-column>
      <el-table-column label="审核" width="80">
        <template #default="{row}">
          <el-tag :type="row.status==='已通过'?'success':(row.status==='已付款'?'':(row.status==='已驳回'?'danger':'warning'))" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="付款时间" width="170"><template #default="{row}">{{ row.paid_at ? row.paid_at.slice(0,16).replace('T',' ') : '-' }}</template></el-table-column>
      <el-table-column prop="created_at" label="申请时间" width="170" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{row}">
          <div style="display:flex;gap:4px;align-items:center">
            <el-button v-if="row.status==='待审核'" text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="row.status==='待审核'" text type="success" size="small" @click="openReview(row)">审核</el-button>
            <el-button v-if="row.status==='已通过'" text type="warning" size="small" @click="payItem(row)">付款</el-button>
            <el-popconfirm title="确定删除？" @confirm="delItem(row.id)">
              <template #reference><el-button text type="danger" size="small">删除</el-button></template>
            </el-popconfirm>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 报销对话框 -->
    <el-dialog v-model="showForm" :title="editId?'编辑报销':'新增报销'" width="550px">
      <el-form :model="form" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="报销人"><el-input :model-value="currentUserName" disabled /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="类型"><el-select v-model="form.expense_type" style="width:100%">
            <el-option label="交通费" value="交通费" /><el-option label="餐饮费" value="餐饮费" />
            <el-option label="办公用品" value="办公用品" /><el-option label="差旅费" value="差旅费" />
            <el-option label="其他" value="其他" />
          </el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :precision="2" style="width:100%" /></el-form-item>
        <el-form-item label="费用说明"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-divider content-position="left">银行信息</el-divider>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="开户行"><el-input v-model="form.bank_name" placeholder="如: 中国银行" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="银行账号"><el-input v-model="form.bank_account" placeholder="银行卡号" /></el-form-item></el-col>
        </el-row>
        <el-divider content-position="left">报销凭证（可多选）</el-divider>
        <el-form-item label="凭证文件">
          <el-upload :show-file-list="false" :before-upload="handleUploadReceipt" multiple accept="image/*,.pdf,.doc,.docx,.xls,.xlsx">
            <el-button type="primary" plain>选择文件</el-button>
          </el-upload>
          <div v-if="receiptFiles.length" style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px">
            <el-tag v-for="(f, i) in receiptFiles" :key="i" closable :disable-transitions="false" @close="removeReceipt(i)" style="margin-bottom:4px">
              {{ f.name }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm=false">取消</el-button>
        <el-button type="primary" @click="saveForm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog v-model="showReview" title="审核报销" width="400px">
      <el-form label-width="90px">
        <el-form-item label="审核结果">
          <el-radio-group v-model="reviewAction">
            <el-radio value="approve">通过</el-radio>
            <el-radio value="reject">驳回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审核备注"><el-input v-model="reviewRemark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReview=false">取消</el-button>
        <el-button type="primary" @click="submitReview">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import request from '@/api/request'

const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('user')) } catch { return { display_name: '未知用户' } }
})
const currentUserName = computed(() => currentUser.value?.display_name || currentUser.value?.username || '未知')

const list = ref([])
const filterStatus = ref('')
const filterApplicant = ref('')

const showForm = ref(false)
const editId = ref(null)
const form = ref({ expense_type:'其他', amount:0, description:'', bank_name:'', bank_account:'' })
const receiptFiles = ref([])  // {name, url}[]

const showReview = ref(false)
const reviewTarget = ref(null)
const reviewAction = ref('approve')
const reviewRemark = ref('')

function formatReceipts(urls) {
  if (!urls) return []
  try { return JSON.parse(urls) } catch { return [] }
}

async function fetchList() {
  const params = {}
  if (filterStatus.value) params.status = filterStatus.value
  if (filterApplicant.value) params.applicant = filterApplicant.value
  list.value = await request.get('/reimbursement', { params })
}

function openCreate() {
  editId.value = null
  form.value = { expense_type:'其他', amount:0, description:'', bank_name:'', bank_account:'' }
  receiptFiles.value = []
  showForm.value = true
}

function openEdit(row) {
  editId.value = row.id
  form.value = {
    expense_type:row.expense_type,
    amount:parseFloat(row.amount), description:row.description || '',
    bank_name:row.bank_name || '', bank_account:row.bank_account || ''
  }
  receiptFiles.value = formatReceipts(row.receipt_urls).map(u => ({ name: decodeURIComponent(u.split('/').pop()), url: u }))
  showForm.value = true
}

async function handleUploadReceipt(file) {
  const fd = new FormData()
  fd.append('file', file)
  try {
    const res = await request.post('/reimbursement/upload', fd)
    receiptFiles.value.push({ name: file.name, url: res.url })
  } catch { ElMessage.error('上传失败: ' + file.name) }
  return false
}

function removeReceipt(index) {
  receiptFiles.value.splice(index, 1)
}

async function saveForm() {
  if (form.value.amount <= 0) return ElMessage.warning('请填写金额')
  const payload = {
    ...form.value,
    receipt_urls: receiptFiles.value.length ? JSON.stringify(receiptFiles.value.map(f => f.url)) : ''
  }
  if (editId.value) await request.put(`/reimbursement/${editId.value}`, payload)
  else await request.post('/reimbursement', payload)
  ElMessage.success('保存成功')
  showForm.value = false
  fetchList()
}

function viewReceipts(row) {
  const urls = formatReceipts(row.receipt_urls)
  urls.forEach(u => window.open(u, '_blank'))
}

function openReview(row) {
  reviewTarget.value = row
  reviewAction.value = 'approve'
  reviewRemark.value = ''
  showReview.value = true
}

async function submitReview() {
  if (!reviewTarget.value) return
  await request.put(`/reimbursement/${reviewTarget.value.id}/review`, { action: reviewAction.value, remark: reviewRemark.value })
  ElMessage.success(reviewAction.value === 'approve' ? '已审核通过' : '已驳回')
  showReview.value = false
  fetchList()
}

async function delItem(id) {
  await request.delete(`/reimbursement/${id}`)
  ElMessage.success('已删除')
  fetchList()
}

async function payItem(row) {
  await request.put(`/reimbursement/${row.id}/pay`)
  ElMessage.success('已标记付款')
  fetchList()
}

onMounted(fetchList)
</script>
