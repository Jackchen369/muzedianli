<template>
  <div>
    <!-- 统计卡片 -->
    <el-row :gutter="12" style="margin-bottom:16px">
      <el-col :span="6" v-for="s in stats" :key="s.label">
        <el-card shadow="hover" style="text-align:center;padding:4px">
          <div style="font-size:20px;font-weight:bold;color:#409EFF">{{ s.value }}</div>
          <div style="font-size:12px;color:#909399">{{ s.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">发票管理</span>
      <div style="display:flex;gap:8px">
        <el-input v-model="searchText" placeholder="搜索项目名称" clearable style="width:180px" @change="fetch" @clear="fetch" />
        <el-button type="primary" @click="openNew(tab)">新增{{ tab==='out'?'销项':'进项' }}发票</el-button>
      </div>
    </div>

    <el-tabs v-model="tab" @tab-change="fetch">
      <!-- 销项发票 -->
      <el-tab-pane label="销项发票" name="out">
        <el-table :data="outList" stripe border size="small">
          <el-table-column label="类型" width="80"><template #default="{row}"><el-tag size="small" :type="row.invoice_type==='乙→甲'?'':row.invoice_type==='丙→乙'?'warning':'success'">{{ row.invoice_type }}</el-tag></template></el-table-column>
          <el-table-column label="项目" min-width="110"><template #default="{row}">{{ projMap[row.project_id] }}</template></el-table-column>
          <el-table-column label="收票方" min-width="100"><template #default="{row}">{{ partnerMap[row.receiver_id] }}</template></el-table-column>
          <el-table-column label="不含税金额" width="115"><template #default="{row}">¥{{ (row.amount_excluding_tax||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="税率" width="55"><template #default="{row}">{{ row.tax_rate }}%</template></el-table-column>
          <el-table-column label="税额" width="110"><template #default="{row}">¥{{ (row.tax_amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="含税金额" width="115"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="发票号码" width="120" prop="invoice_no" />
          <el-table-column label="开票日期" width="90" prop="invoice_date" />
          <el-table-column label="附件" width="55">
            <template #default="{row}"><el-button v-if="row.file_path" text size="small" @click="viewFile(row)">📎</el-button><span v-else>-</span></template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{row}">
              <el-button text type="primary" size="small" @click="editOut(row)">编</el-button>
              <el-popconfirm title="确定删除？" @confirm="delOut(row.id)"><template #reference><el-button text type="danger" size="small">删</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-if="outTotal>pageSize" v-model:current-page="outPage" :page-size="pageSize" :total="outTotal" layout="total, sizes, prev, pager, next, jumper" :page-sizes="[10,20,50,100]" style="margin-top:8px;justify-content:center" @current-change="fetch" @size-change="pageSize=$event;fetch()" />
      </el-tab-pane>

      <!-- 进项发票 -->
      <el-tab-pane label="进项发票" name="in">
        <el-table :data="inList" stripe border size="small">
          <el-table-column label="项目" min-width="110"><template #default="{row}">{{ projMap[row.project_id] }}</template></el-table-column>
          <el-table-column label="开票方" min-width="100"><template #default="{row}">{{ partnerMap[row.issuer_id] }}</template></el-table-column>
          <el-table-column label="不含税金额" width="115"><template #default="{row}">¥{{ (row.amount_excluding_tax||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="税率" width="55"><template #default="{row}">{{ row.tax_rate }}%</template></el-table-column>
          <el-table-column label="税额" width="110"><template #default="{row}">¥{{ (row.tax_amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="含税金额" width="115"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="实收税金" width="110"><template #default="{row}">¥{{ (row.actual_tax_received||0).toLocaleString() }}</template></el-table-column>
          <el-table-column label="税差(净收益)" width="115">
            <template #default="{row}">
              <span :style="{color:(row.tax_amount||0)-(row.actual_tax_received||0)>=0?'#67C23A':'#F56C6C',fontWeight:'bold'}">
                ¥{{ ((row.tax_amount||0)-(row.actual_tax_received||0)).toLocaleString() }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="发票号码" width="120" prop="invoice_no" />
          <el-table-column label="日期" width="90" prop="invoice_date" />
          <el-table-column label="附件" width="55">
            <template #default="{row}"><el-button v-if="row.file_path" text size="small" @click="viewFile(row)">📎</el-button><span v-else>-</span></template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{row}">
              <el-button text type="primary" size="small" @click="editIn(row)">编</el-button>
              <el-popconfirm title="确定删除？" @confirm="delIn(row.id)"><template #reference><el-button text type="danger" size="small">删</el-button></template></el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-if="inTotal>pageSize" v-model:current-page="inPage" :page-size="pageSize" :total="inTotal" layout="total, sizes, prev, pager, next, jumper" :page-sizes="[10,20,50,100]" style="margin-top:8px;justify-content:center" @current-change="fetch" @size-change="pageSize=$event;fetch()" />
      </el-tab-pane>
    </el-tabs>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showNew" :title="dialogTitle" width="620px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="项目"><el-select v-model="form.project_id" filterable style="width:100%"><el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" /></el-select></el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item :label="tab==='out'?'收票方':'开票方'">
              <el-select v-model="form.partner_id" filterable style="width:100%"><el-option v-for="p in partners" :key="p.id" :label="p.name" :value="p.id" /></el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item v-if="tab==='out'" label="发票类型">
              <el-select v-model="form.invoice_type" style="width:100%"><el-option label="乙→甲" value="乙→甲" /><el-option label="丙→乙" value="丙→乙" /><el-option label="丙→甲" value="丙→甲" /></el-select>
            </el-form-item>
            <el-form-item v-else label="可抵扣"><el-switch v-model="form.is_deductible" active-text="是" inactive-text="否" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="含税金额"><el-input-number v-model="form.amount" :min="0" :step="10000" style="width:100%" @change="calcTax" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="税率(%)"><el-input-number v-model="form.tax_rate" :min="0" :max="100" step="1" style="width:100%" @change="calcTax" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8"><el-form-item label="不含税金额"><el-input :model-value="calcExcluding" disabled style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="税额"><el-input :model-value="calcTaxAmount" disabled style="width:100%" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="含税金额"><el-input :model-value="form.amount" disabled style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item v-if="tab==='in'" label="实收税金">
          <el-input-number v-model="form.actual_tax_received" :min="0" :step="1000" style="width:100%" />
          <div style="font-size:12px;color:#909399;margin-top:4px">
            税差(净收益): <span :style="{color:taxDiff>=0?'#67C23A':'#F56C6C',fontWeight:'bold'}">¥{{ taxDiff.toLocaleString() }}</span>
            = 税额 {{ calcTaxAmount }} - 实收 {{ form.actual_tax_received||0 }}
          </div>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="发票号码"><el-input v-model="form.invoice_no" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="开票日期"><el-date-picker v-model="form.invoice_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="发票附件">
          <el-upload :action="uploadUrl" :headers="uploadHeaders" :on-success="upSuccess" :on-error="upError" :show-file-list="false">
            <el-button size="small" type="primary">上传发票扫描件</el-button>
            <template #tip><span style="font-size:12px;color:#909399;margin-left:8px">{{ form.file_path ? '已上传' : '未上传' }}</span></template>
          </el-upload>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="showNew=false">取消</el-button><el-button type="primary" @click="saveInvoice">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const tab = ref('out')
const outList = ref([])
const inList = ref([])
const partners = ref([])
const projects = ref([])
const partnerMap = ref({})
const projMap = ref({})
const filterProject = ref('')
const showNew = ref(false)
const editId = ref(null)
const uploadFilePath = ref('')
const outPage = ref(1)
const outTotal = ref(0)
const inPage = ref(1)
const inTotal = ref(0)
const pageSize = ref(10)
const searchText = ref('')
// All data for stats computation (unpaginated)
const allOutList = ref([])
const allInList = ref([])

const form = reactive({
  project_id:null, partner_id:null, invoice_type:'乙→甲',
  amount:0, tax_rate:9, invoice_no:'', invoice_date:null,
  is_deductible:true, actual_tax_received:0, remark:'', file_path:''
})

const token = computed(() => localStorage.getItem('token') || '')
const uploadUrl = computed(() => `/api/v1/files/upload/0?filetype=invoice`)
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${token.value}` }))

const calcExcluding = computed(() => {
  if (!form.amount || !form.tax_rate) return '0.00'
  const rate = form.tax_rate
  const excluding = form.amount / (1 + rate / 100)
  return excluding.toFixed(2)
})
const calcTaxAmount = computed(() => {
  if (!form.amount || !form.tax_rate) return '0.00'
  const rate = form.tax_rate / 100
  return (form.amount * rate / (1 + rate)).toFixed(2)
})
const taxDiff = computed(() => {
  const tax = parseFloat(calcTaxAmount.value) || 0
  const received = form.actual_tax_received || 0
  return tax - received
})

function calcTax() {} // triggers computed recalculation

const dialogTitle = computed(() => {
  const t = tab.value==='out'?'销项':'进项'
  return editId.value ? `编辑${t}发票` : `新增${t}发票`
})

const stats = computed(() => {
  const t = { '丙→乙':0, '丙→甲':0 }
  let taxC = 0  // 丙公司的销项税额
  allOutList.value.forEach(f => {
    if (f.invoice_type === '丙→乙' || f.invoice_type === '丙→甲') {
      t[f.invoice_type] += Number(f.amount) || 0
      taxC += Number(f.tax_amount) || 0
    }
  })
  let taxIn = 0  // 供货商的实收税金（仅可抵扣）
  allInList.value.forEach(f => {
    if (f.is_deductible) taxIn += Number(f.actual_tax_received) || 0
  })
  return [
    { label: '总开票额(含税)', value: `¥${(Object.values(t).reduce((a,b)=>a+b,0)/10000).toFixed(1)}万`, color: '#409EFF' },
    { label: '总销项税额', value: `¥${(taxC/10000).toFixed(1)}万`, color: '#67C23A' },
    { label: '总实收税金', value: `¥${(taxIn/10000).toFixed(1)}万`, color: '#E6A23C' },
    { label: '总票据数', value: `${outList.value.length+inList.value.length}`, color: '#303133' },
  ]
})

async function fetch() {
  const st = searchText.value ? `&search=${encodeURIComponent(searchText.value)}` : ''
  const [outRes, inRes, allOut, allIn, partnersRes, projectsRes] = await Promise.all([
    request.get(`/invoices/out?page=${outPage.value}&page_size=${pageSize.value}${st}`),
    request.get(`/invoices/in?page=${inPage.value}&page_size=${pageSize.value}${st}`),
    request.get(`/invoices/out?page=1&page_size=99999${st.replace('&','?')}`),
    request.get(`/invoices/in?page=1&page_size=99999${st.replace('&','?')}`),
    request.get('/partners'),
    request.get('/projects?page=1&page_size=999').then(r => r.items || r || []),
  ])
  outList.value = outRes.items || []
  outTotal.value = outRes.total || 0
  inList.value = inRes.items || []
  inTotal.value = inRes.total || 0
  allOutList.value = allOut.items || []
  allInList.value = allIn.items || []
  partners.value = partnersRes
  projects.value = projectsRes
  partners.value.forEach(p => partnerMap.value[p.id] = p.name)
  projects.value.forEach(p => projMap.value[p.id] = p.name)
}

function openNew(t) {
  editId.value = null; uploadFilePath.value = ''
  Object.assign(form, { project_id:null, partner_id:null, invoice_type:'乙→甲', amount:0, tax_rate:9, invoice_no:'', invoice_date:null, is_deductible:true, actual_tax_received:0, remark:'', file_path:'' })
  showNew.value = true
}

function editOut(row) {
  editId.value = row.id; tab.value = 'out'
  Object.assign(form, { project_id:row.project_id, partner_id:row.receiver_id, invoice_type:row.invoice_type, amount:row.amount, tax_rate:row.tax_rate, invoice_no:row.invoice_no||'', invoice_date:row.invoice_date||null, is_deductible:true, actual_tax_received:0, remark:row.remark||'', file_path:row.file_path||'' })
  showNew.value = true
}

function editIn(row) {
  editId.value = row.id; tab.value = 'in'
  Object.assign(form, { project_id:row.project_id, partner_id:row.issuer_id, invoice_type:'乙→甲', amount:row.amount, tax_rate:row.tax_rate, invoice_no:row.invoice_no||'', invoice_date:row.invoice_date||null, is_deductible:row.is_deductible, actual_tax_received:row.actual_tax_received||0, remark:row.remark||'', file_path:row.file_path||'' })
  showNew.value = true
}

function upSuccess(r) { uploadFilePath.value = r.filepath; form.file_path = r.filepath; ElMessage.success('上传成功') }
function upError() { ElMessage.error('上传失败') }

async function saveInvoice() {
  const isOut = tab.value === 'out'
  const payload = {
    project_id: form.project_id, amount: form.amount, tax_rate: form.tax_rate,
    invoice_no: form.invoice_no, invoice_date: form.invoice_date,
    file_path: form.file_path, remark: form.remark,
  }
  if (isOut) {
    payload.receiver_id = form.partner_id; payload.invoice_type = form.invoice_type
  } else {
    payload.issuer_id = form.partner_id; payload.is_deductible = form.is_deductible
    payload.actual_tax_received = form.actual_tax_received
  }
  if (editId.value) {
    await request.put(`/invoices/${isOut?'out':'in'}/${editId.value}`, payload)
    ElMessage.success('编辑成功')
  } else {
    await request.post(`/invoices/${isOut?'out':'in'}`, payload)
    ElMessage.success('新增成功')
  }
  showNew.value = false; editId.value = null; fetch()
}

function viewFile(row) {
  if (row.file_path) window.open(`/api/v1/files/by-filename/${row.file_path}`, '_blank')
}

async function delOut(id) { await request.delete(`/invoices/out/${id}`); ElMessage.success('已删除'); fetch() }
async function delIn(id) { await request.delete(`/invoices/in/${id}`); ElMessage.success('已删除'); fetch() }
onMounted(fetch)
</script>
