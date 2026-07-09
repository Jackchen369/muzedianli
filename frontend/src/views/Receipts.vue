<template>
  <div>
    <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-size:18px;font-weight:bold">电子收据</span>
      <div style="display:flex;gap:8px">
        <el-input v-model="searchKey" placeholder="搜索付款方..." clearable prefix-icon="Search" style="width:200px" />
        <el-select v-model="filterStatus" clearable placeholder="状态" style="width:100px">
          <el-option label="已开具" value="已开具" /><el-option label="已作废" value="已作废" />
        </el-select>
        <el-button @click="openSealDialog">财务章管理</el-button>
        <el-button type="primary" @click="openNew">开具收据</el-button>
      </div>
    </div>

    <el-table :data="filteredList" stripe border size="small">
      <el-table-column prop="receipt_no" label="收据编号" width="150" />
      <el-table-column prop="payer_name" label="付款方" min-width="150" />
      <el-table-column prop="amount" label="金额" width="130"><template #default="{row}">¥{{ (row.amount||0).toLocaleString() }}</template></el-table-column>
      <el-table-column prop="amount_words" label="大写金额" min-width="200" />
      <el-table-column prop="reason" label="事由" min-width="150" />
      <el-table-column prop="receipt_date" label="日期" width="100" />
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='已开具'?'success':'info'" size="small">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="175" fixed="right">
        <template #default="{row}">
          <div style="display:flex;gap:2px;white-space:nowrap">
            <el-button text type="primary" size="small" @click="preview(row)">预览</el-button>
            <el-button text type="warning" size="small" @click="voidReceipt(row.id)">作废</el-button>
            <el-popconfirm title="确定删除该收据？" @confirm="delReceipt(row.id)">
              <template #reference><el-button text type="danger" size="small">删除</el-button></template>
            </el-popconfirm>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 开具收据对话框 -->
    <el-dialog v-model="showNew" title="开具电子收据" width="550px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="付款方名称"><el-input v-model="form.payer_name" /></el-form-item>
        <el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :step="1000" style="width:100%" /></el-form-item>
        <el-form-item label="大写金额"><el-input :model-value="amountWords" disabled /></el-form-item>
        <el-form-item label="收款事由"><el-input v-model="form.reason" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="收款方式">
          <el-radio-group v-model="form.payment_method">
            <el-radio value="现金">现金</el-radio><el-radio value="转账">转账</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="经办人"><el-input v-model="form.handler" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="核准人"><el-input v-model="form.approver" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.remark" /></el-form-item>
        <el-form-item label="开票日期"><el-date-picker v-model="form.receipt_date" type="date" style="width:100%" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="加盖财务章">
          <el-select v-model="form.seal_id" clearable placeholder="选择财务章" style="width:100%">
            <el-option v-for="s in seals" :key="s.id" :label="s.seal_name" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNew=false">取消</el-button>
        <el-button type="primary" @click="saveReceipt">开具</el-button>
      </template>
    </el-dialog>

    <!-- 财务章管理对话框 -->
    <el-dialog v-model="showSeal" title="财务章管理" width="450px">
      <div style="margin-bottom:12px">
        <el-upload :action="sealUploadUrl" :headers="uploadHeaders" :on-success="onSealUpload" :show-file-list="false">
          <el-button size="small" type="primary">上传财务章图片</el-button>
          <template #tip><span style="font-size:12px;color:#909399;margin-left:8px">支持 PNG/JPG</span></template>
        </el-upload>
      </div>
      <el-table :data="seals" stripe size="small">
        <el-table-column prop="seal_name" label="印章名称" min-width="120" />
        <el-table-column label="状态" width="70"><template #default="{row}"><el-tag :type="row.is_active?'success':'info'" size="small">{{ row.is_active?'启用':'停用' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="70">
          <template #default="{row}">
            <el-popconfirm title="确定删除？" @confirm="delSeal(row.id)">
              <template #reference><el-button text type="danger" size="small">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 收据预览对话框 -->
    <el-dialog v-model="showPreview" :title="'电子收款收据 - '+(previewData?.receipt_no||'')" width="700px" top="3vh">
      <div v-if="previewData" id="receipt-preview" style="background:#fff;padding:30px 40px;border:1px solid #ccc;font-family:'SimSun','STSong',serif;position:relative;min-height:500px">
        <!-- 标题 -->
        <div style="text-align:center;font-size:24px;font-weight:bold;letter-spacing:8px">电子收款收据</div>
        <div style="border-top:2px solid #000;margin:4px 0 2px"></div>
        <div style="border-top:1px solid #000;margin-bottom:16px"></div>

        <!-- 右上角：编号+日期 -->
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <div style="font-size:14px;color:#666">收据日期：{{ previewData.receipt_date }}</div>
          <div style="color:red;font-size:15px;font-weight:bold">NO. {{ previewData.receipt_no }}</div>
        </div>

        <!-- 表单内容 -->
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-top:20px">
          <tr>
            <td style="width:80px;padding:8px 4px;white-space:nowrap;vertical-align:top;font-size:15px">今收到：</td>
            <td style="border-bottom:1px dashed #999;padding:8px 4px;font-size:15px">{{ previewData.payer_name }}</td>
          </tr>
          <tr>
            <td style="width:80px;padding:8px 4px;white-space:nowrap;vertical-align:top;font-size:15px">交 来：</td>
            <td style="border-bottom:1px dashed #999;padding:8px 4px;font-size:15px">{{ previewData.reason }}</td>
          </tr>
          <tr>
            <td style="padding:8px 4px;white-space:nowrap;font-size:15px">人民币（大写）：</td>
            <td style="border-bottom:1px dashed #999;padding:8px 4px;display:flex;align-items:center;gap:8px">
              <span style="font-weight:bold;font-size:15px">{{ previewData.amount_words }}</span>
              <span style="margin-left:auto;font-size:15px">¥ {{ (previewData.amount||0).toLocaleString() }}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 4px;white-space:nowrap;font-size:15px">收款方式：</td>
            <td style="border-bottom:1px dashed #999;padding:8px 4px;font-size:15px">
              <span v-if="previewData.payment_method">✓ {{ previewData.payment_method }}</span>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 4px;white-space:nowrap;font-size:15px">备 注：</td>
            <td style="border-bottom:1px dashed #999;padding:8px 4px;font-size:14px;color:#999">{{ previewData.remark || '' }}</td>
          </tr>
        </table>

        <!-- 底部：核准/经办人/盖章 -->
        <div style="display:flex;justify-content:space-between;margin-top:40px">
          <div style="font-size:14px">核准：<span style="border-bottom:1px solid #333;min-width:100px;display:inline-block">&nbsp;{{ previewData.approver || '' }}&nbsp;&nbsp;&nbsp;</span></div>
          <div style="font-size:14px">经办人：<span style="border-bottom:1px solid #333;min-width:100px;display:inline-block">&nbsp;{{ previewData.handler || '' }}&nbsp;&nbsp;&nbsp;</span></div>
          <div style="font-size:14px;text-align:center;position:relative">
            收款单位（盖章）
            <div v-if="sealImg" style="position:absolute;top:-50px;left:50%;transform:translateX(-50%);width:90px;height:90px;opacity:0.75">
              <img :src="sealImg" style="width:100%;height:100%;object-fit:contain" />
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="printReceipt">打印</el-button>
        <el-button @click="showPreview=false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import request from '@/api/request'

const list = ref([])
const searchKey = ref('')
const filterStatus = ref('')
const seals = ref([])
const showNew = ref(false)
const showSeal = ref(false)
const showPreview = ref(false)
const previewData = ref(null)
const sealImg = ref('')
const form = reactive({
  payer_name:'', amount:0, reason:'', payment_method:'现金', handler:'', approver:'', remark:'', receipt_date:'', seal_id:null
})
const token = computed(() => localStorage.getItem('token') || '')
const sealUploadUrl = '/api/v1/files/upload/0?filetype=seal'
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${token.value}` }))

// 数字转中文大写
const digits = ['零','壹','贰','叁','肆','伍','陆','柒','捌','玖']
const units = ['','拾','佰','仟']
const bigUnits = ['','万','亿','万亿']

function numberToWords(n) {
  if (n === 0) return '零元整'
  let num = Math.round(n * 100) // 转成分
  const jiao = num % 10; num = Math.floor(num / 10)
  const yuan = Math.floor(num / 10); const fenPart = num % 10

  function convertInt(x) {
    if (x === 0) return ''
    let s = '', zero = false
    for (let i = 0; i < 4 && x > 0; i++) {
      const d = x % 10
      if (d === 0) { zero = true } else {
        if (zero) { s = '零' + s; zero = false }
        s = digits[d] + units[i] + s
      }
      x = Math.floor(x / 10)
    }
    return s
  }

  let result = '', yi = Math.floor(yuan / 100000000)
  let wan = Math.floor((yuan % 100000000) / 10000)
  let ge = yuan % 10000

  if (yi > 0) { result += convertInt(yi) + '亿'; if (wan < 1000 && wan > 0 && ge > 0) result += '零' }
  if (wan > 0) { result += convertInt(wan) + '万'; if (ge < 1000 && ge > 0) result += '零' }
  if (ge > 0) result += convertInt(ge)

  result += '元'
  if (fenPart === 0 && jiao === 0) result += '整'
  else {
    if (jiao > 0) result += digits[jiao] + '角'
    if (fenPart > 0) result += digits[fenPart] + '分'
  }
  return result
}

const amountWords = computed(() => form.amount ? numberToWords(form.amount) : '')

const filteredList = computed(() => {
  let items = list.value
  if (searchKey.value) {
    const s = searchKey.value.toLowerCase()
    items = items.filter(i => i.payer_name?.toLowerCase().includes(s))
  }
  if (filterStatus.value) {
    items = items.filter(i => i.status === filterStatus.value)
  }
  return items
})

async function fetch() {
  list.value = await request.get('/ereceipts/receipts').catch(() => [])
  seals.value = await request.get('/ereceipts/seals').catch(() => [])
}

function openNew() { Object.assign(form, { payer_name:'', amount:0, reason:'', payment_method:'现金', handler:'', approver:'', remark:'', receipt_date:'', seal_id:null }); showNew.value = true }
function openSealDialog() { showSeal.value = true }
function onSealUpload(r) {
  request.post('/ereceipts/seals', { seal_name: r.filename || '财务章', file_path: r.filepath })
  ElMessage.success('上传成功'); fetch()
}

async function saveReceipt() {
  const payload = { ...form, amount_words: amountWords.value }
  await request.post('/ereceipts/receipts', payload)
  ElMessage.success('开具成功'); showNew.value = false; fetch()
}

async function preview(row) {
  previewData.value = row
  if (row.seal_id) {
    const s = seals.value.find(x => x.id === row.seal_id)
    if (s?.file_path) sealImg.value = `/api/v1/files/by-filename/${s.file_path}`
    else sealImg.value = ''
  } else sealImg.value = ''
  showPreview.value = true
}

function printReceipt() {
  const printContent = document.getElementById('receipt-preview')
  if (!printContent) return
  const win = window.open('', '_blank')
  win.document.write(`
    <html><head><title>电子收款收据</title>
    <style>
      @page { margin: 0; size: 210mm 99mm; }
      body { font-family: 'SimSun','STSong','Noto Serif SC',serif; margin: 0; padding: 8mm 10mm; width: 210mm; height: 99mm; box-sizing: border-box; }
      * { box-sizing: border-box; }
      .receipt { width: 100%; height: 100%; }
      .title { text-align:center; font-size:20px; font-weight:bold; letter-spacing:6px; margin-bottom:2px; }
      .line-thick { border-top:2px solid #000; margin:3px 0 1px; }
      .line-thin { border-top:1px solid #000; margin-bottom:10px; }
      .top-row { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; }
      .date { font-size:12px; color:#666; }
      .no { color:red; font-size:13px; font-weight:bold; }
      table { width:100%; border-collapse:collapse; font-size:12px; }
      td { padding:5px 3px; }
      .label { width:85px; white-space:nowrap; vertical-align:top; font-size:13px; }
      .dash-line { border-bottom:1px dashed #999; }
      .amount-row { display:flex; align-items:center; justify-content:space-between; }
      .amount-words { font-weight:bold; font-size:13px; }
      .amount-num { font-size:13px; }
      .checkbox { border:1px solid #666; display:inline-block; width:11px; height:11px; margin-right:3px; vertical-align:middle; }
      .method-item { margin-right:20px; font-size:12px; }
      .footer { display:flex; justify-content:space-between; margin-top:20px; align-items:flex-end; }
      .footer-item { font-size:12px; }
      .sign-line { border-bottom:1px solid #333; display:inline-block; min-width:70px; }
      .stamp-area { text-align:center; position:relative; }
      .stamp-img { position:absolute; bottom:0; left:50%; transform:translateX(-50%); width:484px; height:484px; max-width:4.1cm; max-height:4.1cm; opacity:0.75; }
      .stamp-img img { width:100%; height:100%; object-fit:contain; }
    </style></head><body>
    <div class="receipt">
      <div class="title">电子收款收据</div>
      <div class="line-thick"></div>
      <div class="line-thin"></div>
      <div class="top-row">
        <div class="date">收据日期：${previewData.value?.receipt_date || ''}</div>
        <div class="no">NO. ${previewData.value?.receipt_no || ''}</div>
      </div>
      <table>
        <tr><td class="label">今收到：</td><td class="dash-line">${previewData.value?.payer_name || ''}</td></tr>
        <tr><td class="label">交 来：</td><td class="dash-line">${previewData.value?.reason || ''}</td></tr>
        <tr>
          <td class="label">人民币（大写）：</td>
          <td class="dash-line"><div class="amount-row"><span class="amount-words">${previewData.value?.amount_words || ''}</span><span class="amount-num">&yen; ${(previewData.value?.amount||0).toLocaleString()}</span></div></td>
        </tr>
        <tr>
          <td class="label">收款方式：</td>
          <td class="dash-line">${previewData.value?.payment_method || ''}</td>
        </tr>
        <tr><td class="label">备 注：</td><td class="dash-line">${previewData.value?.remark || ''}</td></tr>
      </table>
      <div class="footer">
        <div class="footer-item">核准：<span class="sign-line">&nbsp;${previewData.value?.approver || ''}&nbsp;</span></div>
        <div class="footer-item">经办人：<span class="sign-line">&nbsp;${previewData.value?.handler || ''}&nbsp;</span></div>
        <div class="footer-item stamp-area">
          收款单位（盖章）
          ${sealImg.value ? `<div class="stamp-img"><img src="${sealImg.value}" /></div>` : ''}
        </div>
      </div>
    </div>
    </body></html>
  `)
  win.document.close()
  win.focus()
  setTimeout(() => { win.print(); win.close() }, 300)
}

async function voidReceipt(id) {
  await request.put(`/ereceipts/receipts/${id}`, { status: '已作废' })
  ElMessage.success('已作废'); fetch()
}
async function delReceipt(id) {
  await request.delete(`/ereceipts/receipts/${id}`)
  ElMessage.success('已删除'); fetch()
}
async function delSeal(id) { await request.delete(`/ereceipts/seals/${id}`); ElMessage.success('已删除'); fetch() }

onMounted(fetch)
</script>
