<template>
  <div>
    <div style="margin-bottom:16px;display:flex;justify-content:space-between">
      <span style="font-size:18px;font-weight:bold">项目管理</span>
      <el-button type="primary" @click="openNew">新建项目</el-button>
    </div>
    <el-table :data="list" stripe border style="width:100%">
      <el-table-column prop="name" label="项目名称" min-width="150">
        <template #default="{row}">
          <el-link type="primary" @click="router.push(`/projects/${row.id}`)">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column label="业主" width="100">
        <template #default="{row}">{{ ownerMap[row.owner_id] || '' }}</template>
      </el-table-column>
      <el-table-column label="中标单位" width="110">
        <template #default="{row}">{{ partnerMap[row.winning_bid_unit_id] || '-' }}</template>
      </el-table-column>
      <el-table-column prop="contract_amount" label="合同金额" width="110">
        <template #default="{row}">¥{{ (row.contract_amount/10000).toFixed(1) }}万</template>
      </el-table-column>
      <el-table-column prop="settlement_amount" label="审定金额" width="110">
        <template #default="{row}">{{ row.settlement_amount ? '¥'+(row.settlement_amount/10000).toFixed(1)+'万' : '-' }}</template>
      </el-table-column>
      <el-table-column label="签订日期" width="105">
        <template #default="{row}">{{ row.contract_sign_date || '-' }}</template>
      </el-table-column>
      <el-table-column label="计划" width="105">
        <template #default="{row}">{{ row.start_date || '-' }}~{{ row.end_date||'-' }}</template>
      </el-table-column>
      <el-table-column label="实际" width="105">
        <template #default="{row}">{{ row.actual_start_date||'-' }}~{{ row.actual_end_date||'-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-tag :type="row.status==='在建'?'primary':row.status==='已完工'?'success':'info'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{row}">
          <el-button text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm title="确定删除该项目？" @confirm="handleDelete(row.id)">
            <template #reference><el-button text type="danger" size="small">删除</el-button></template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showDialog" :title="isEdit?'编辑项目':'新建项目'" width="600px">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="项目名称"><el-input v-model="form.name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="业主单位">
            <el-select v-model="form.owner_id" filterable style="width:100%">
              <el-option v-for="p in partners" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="中标单位">
            <el-select v-model="form.winning_bid_unit_id" filterable clearable style="width:100%">
              <el-option v-for="p in partners" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="分包单位">
            <el-select v-model="form.subcontractor_ids" multiple filterable collapse-tags style="width:100%">
              <el-option v-for="p in partners" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="合同金额"><el-input-number v-model="form.contract_amount" :min="0" :step="10000" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="劳务分包"><el-input-number v-model="form.labor_subcontract_amount" :min="0" :step="10000" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="机械租赁"><el-input-number v-model="form.machinery_rental_amount" :min="0" :step="10000" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="带电作业"><el-input-number v-model="form.live_working_amount" :min="0" :step="10000" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="审定金额"><el-input-number v-model="form.settlement_amount" :min="0" :step="10000" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-divider content-position="left">日期</el-divider>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="合同签订日期"><el-date-picker v-model="form.contract_sign_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="项目状态">
            <el-select v-model="form.status" style="width:100%">
              <el-option label="在建" value="在建" /><el-option label="已完工" value="已完工" />
              <el-option label="待验收" value="待验收" /><el-option label="质保中" value="质保中" />
            </el-select>
          </el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="计划开工日期"><el-date-picker v-model="form.start_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计划竣工日期"><el-date-picker v-model="form.end_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="实际开工日期"><el-date-picker v-model="form.actual_start_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="实际竣工日期"><el-date-picker v-model="form.actual_end_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" @click="saveProject">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const router = useRouter()
const list = ref([])
const partners = ref([])
const ownerMap = ref({})
const partnerMap = ref({})
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = reactive({
  name: '', owner_id: null, winning_bid_unit_id: null, subcontractor_ids: [],
  contract_amount: 0, budget_amount: 0, labor_subcontract_amount: 0, machinery_rental_amount: 0, live_working_amount: 0,
  settlement_amount: 0,
  status: '在建', remark: '',
  contract_sign_date: null, start_date: null, end_date: null,
  actual_start_date: null, actual_end_date: null,
})

async function fetchList() { list.value = await request.get('/projects') }
async function fetchPartners() {
  partners.value = await request.get('/partners')
  partners.value.forEach(p => { ownerMap.value[p.id] = p.name; partnerMap.value[p.id] = p.name })
}

function openNew() {
  isEdit.value = false; editId.value = null
  Object.assign(form, {
    name: '', owner_id: null, winning_bid_unit_id: null, subcontractor_ids: [],
    contract_amount: 0, budget_amount: 0, labor_subcontract_amount: 0, machinery_rental_amount: 0, live_working_amount: 0,
    settlement_amount: 0,
    status: '在建', remark: '',
    contract_sign_date: null, start_date: null, end_date: null,
    actual_start_date: null, actual_end_date: null,
  })
  showDialog.value = true
}

function openEdit(row) {
  isEdit.value = true; editId.value = row.id
  Object.assign(form, {
    name: row.name, owner_id: row.owner_id,
    winning_bid_unit_id: row.winning_bid_unit_id || null, subcontractor_ids: [],
    contract_amount: row.contract_amount || 0,
    budget_amount: row.budget_amount || 0,
    labor_subcontract_amount: row.labor_subcontract_amount || 0,
    machinery_rental_amount: row.machinery_rental_amount || 0,
    live_working_amount: row.live_working_amount || 0,
    settlement_amount: row.settlement_amount || 0,
    status: row.status, remark: row.remark || '',
    contract_sign_date: row.contract_sign_date || null,
    start_date: row.start_date || null,
    end_date: row.end_date || null,
    actual_start_date: row.actual_start_date || null,
    actual_end_date: row.actual_end_date || null,
  })
  showDialog.value = true
}

async function saveProject() {
  const scIds = [...form.subcontractor_ids]
  delete form.subcontractor_ids  // remove before sending to API
  try {
    if (isEdit.value) {
      await request.put(`/projects/${editId.value}`, form)
      ElMessage.success('编辑成功')
    } else {
      const r = await request.post('/projects', form)
      editId.value = r.id
      ElMessage.success('创建成功')
    }
    // Save subcontractors
    if (editId.value && scIds.length > 0) {
      for (const pid of scIds) {
        try { await request.post('/subcontractors', { project_id: editId.value, partner_id: pid }) } catch {}
      }
    }
  } catch (e) { ElMessage.error(e?.detail || '保存失败') }
  form.subcontractor_ids = scIds  // restore
  showDialog.value = false
  fetchList()
}

async function handleDelete(id) {
  await request.delete(`/projects/${id}`)
  ElMessage.success('删除成功'); fetchList()
}

onMounted(() => { fetchPartners(); fetchList() })
</script>
