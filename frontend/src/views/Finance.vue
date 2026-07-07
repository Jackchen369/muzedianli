<template>
  <div>
    <!-- 统计卡片 -->
    <el-row :gutter="12" style="margin-bottom:16px">
      <el-col :span="6" v-for="c in cards" :key="c.label">
        <el-card shadow="hover" style="text-align:center;padding:4px">
          <div class="fv" :style="{color:c.color}">{{ c.value }}</div>
          <div class="fl">{{ c.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">财务管理</span>
      <div style="display:flex;gap:8px">
        <el-button type="success" @click="openNew('receipt')">新增回款</el-button>
        <el-button type="danger" @click="openNew('payment')">新增付款</el-button>
      </div>
    </div>

    <el-tabs v-model="tab" @tab-change="fetch">
      <!-- 回款记录 -->
      <el-tab-pane label="回款记录" name="receipt">
        <el-table :data="receipts" stripe border size="small">
          <el-table-column label="项目" min-width="120"><template #default="{row}">{{ projMap[row.project_id] }}</template></el-table-column>
          <el-table-column label="付款方" width="130"><template #default="{row}">{{ partnerMap[row.payer_id] }}</template></el-table-column>
          <el-table-column prop="amount" label="回款金额" width="130"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column prop="receipt_date" label="回款日期" width="100" />
          <el-table-column prop="receipt_type" label="方式" width="90" />
          <el-table-column label="附件" width="55"><template #default="{row}"><el-button v-if="row.file_path" text size="small" @click="viewFile(row)">📎</el-button><span v-else>-</span></template></el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{row}">
              <el-button text type="primary" size="small" @click="editRec(row)">编</el-button>
              <el-popconfirm title="确定删除？" @confirm="delRec(row.id)"><template #reference><el-button text type="danger" size="small">删</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 付款记录 -->
      <el-tab-pane label="付款记录" name="payment">
        <el-table :data="payments" stripe border size="small">
          <el-table-column label="项目" min-width="120"><template #default="{row}">{{ projMap[row.project_id] }}</template></el-table-column>
          <el-table-column label="收款方" width="130"><template #default="{row}">{{ partnerMap[row.payee_id] }}</template></el-table-column>
          <el-table-column prop="amount" label="付款金额" width="130"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column prop="payment_date" label="付款日期" width="100" />
          <el-table-column prop="payment_type" label="方式" width="90" />
          <el-table-column label="附件" width="55"><template #default="{row}"><el-button v-if="row.file_path" text size="small" @click="viewFile(row)">📎</el-button><span v-else>-</span></template></el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{row}">
              <el-button text type="primary" size="small" @click="editPay(row)">编</el-button>
              <el-popconfirm title="确定删除？" @confirm="delPay(row.id)"><template #reference><el-button text type="danger" size="small">删</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showNew" :title="dialogTitle" width="550px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="项目"><el-select v-model="form.project_id" filterable style="width:100%"><el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" /></el-select></el-form-item>
        <el-form-item :label="tab==='receipt'?'付款方':'收款方'">
          <el-select v-model="form.partner_id" filterable style="width:100%"><el-option v-for="p in partners" :key="p.id" :label="p.name" :value="p.id" /></el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :step="10000" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="tab==='receipt'?'回款日期':'付款日期'"><el-date-picker v-model="form.finance_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-form-item :label="tab==='receipt'?'回款方式':'付款方式'">
          <el-select v-model="form.finance_type" style="width:100%">
            <el-option label="银行转账" value="银行转账" /><el-option label="现金" value="现金" /><el-option label="承兑汇票" value="承兑汇票" /><el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="凭证附件">
          <el-upload :action="uploadUrl" :headers="uploadHeaders" :on-success="upSuccess" :on-error="upError" :show-file-list="false">
            <el-button size="small" type="primary">上传回单/凭证</el-button>
            <template #tip><span style="font-size:12px;color:#909399;margin-left:8px">{{ form.file_path ? '已上传' : '未上传' }}</span></template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="showNew=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const tab = ref('receipt')
const receipts = ref([])
const payments = ref([])
const partners = ref([])
const projects = ref([])
const partnerMap = ref({})
const projMap = ref({})
const showNew = ref(false)
const editId = ref(null)
const summary = ref({})

const form = reactive({
  project_id:null, partner_id:null, amount:0, finance_date:'', finance_type:'银行转账', file_path:''
})

const token = computed(() => localStorage.getItem('token') || '')
const uploadUrl = computed(() => `/api/v1/files/upload/0?filetype=receipt`)
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${token.value}` }))

const dialogTitle = computed(() => {
  const t = tab.value === 'receipt' ? '回款' : '付款'
  return editId.value ? `编辑${t}记录` : `新增${t}记录`
})

const cards = computed(() => {
  const s = summary.value || {}
  return [
    { label: '销项总额', value: `¥${((s.total_invoice_out||0)/10000).toFixed(1)}万`, color: '#409EFF' },
    { label: '已回款', value: `¥${((s.total_receipt||0)/10000).toFixed(1)}万`, color: '#67C23A' },
    { label: '应收余额', value: `¥${((s.receivable_balance||0)/10000).toFixed(1)}万`, color: '#E6A23C' },
    { label: '应付余额', value: `¥${((s.payable_balance||0)/10000).toFixed(1)}万`, color: '#F56C6C' },
  ]
})

async function fetch() {
  const [s, r, p2, partners2, projects2] = await Promise.all([
    request.get('/finance/summary'),
    request.get('/finance/receipts'),
    request.get('/finance/payments'),
    request.get('/partners'),
    request.get('/projects'),
  ])
  summary.value = s; receipts.value = r; payments.value = p2
  partners.value = partners2; projects.value = projects2
  partners2.forEach(x => partnerMap.value[x.id] = x.name)
  projects2.forEach(x => projMap.value[x.id] = x.name)
}

function openNew(t) {
  tab.value = t; editId.value = null
  Object.assign(form, { project_id:null, partner_id:null, amount:0, finance_date:'', finance_type:'银行转账', file_path:'' })
  showNew.value = true
}

function editRec(row) {
  tab.value = 'receipt'; editId.value = row.id
  Object.assign(form, { project_id:row.project_id, partner_id:row.payer_id, amount:row.amount, finance_date:row.receipt_date, finance_type:row.receipt_type, file_path:row.file_path||'' })
  showNew.value = true
}

function editPay(row) {
  tab.value = 'payment'; editId.value = row.id
  Object.assign(form, { project_id:row.project_id, partner_id:row.payee_id, amount:row.amount, finance_date:row.payment_date, finance_type:row.payment_type, file_path:row.file_path||'' })
  showNew.value = true
}

function upSuccess(r) { form.file_path = r.filepath; ElMessage.success('上传成功') }
function upError() { ElMessage.error('上传失败') }

async function save() {
  const isRec = tab.value === 'receipt'
  const payload = { project_id: form.project_id, amount: form.amount, file_path: form.file_path }
  if (isRec) { payload.payer_id = form.partner_id; payload.receipt_date = form.finance_date; payload.receipt_type = form.finance_type }
  else { payload.payee_id = form.partner_id; payload.payment_date = form.finance_date; payload.payment_type = form.finance_type }

  try {
    if (editId.value) {
      await request.put(`/finance/${isRec?'receipts':'payments'}/${editId.value}`, payload)
      ElMessage.success('编辑成功')
    } else {
      await request.post(`/finance/${isRec?'receipts':'payments'}`, payload)
      ElMessage.success('新增成功')
    }
    showNew.value = false; editId.value = null; fetch()
  } catch (e) { ElMessage.error(e?.detail || '保存失败') }
}

function viewFile(row) { if (row.file_path) window.open(`/api/v1/files/download/by-path?path=${row.file_path}`, '_blank') }
async function delRec(id) { await request.delete(`/finance/receipts/${id}`); ElMessage.success('已删除'); fetch() }
async function delPay(id) { await request.delete(`/finance/payments/${id}`); ElMessage.success('已删除'); fetch() }

onMounted(fetch)
</script>

<style scoped>
.fv { font-size:20px;font-weight:bold; }
.fl { font-size:12px;color:#909399;margin-top:4px; }
</style>
