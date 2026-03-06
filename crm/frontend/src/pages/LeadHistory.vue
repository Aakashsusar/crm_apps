<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Lead History'), route: { name: 'LeadHistory' } }]" />
      </template>
      <template #right-header>
        <Button
          :label="__('Refresh')"
          :iconLeft="LucideRefreshCcw"
          @click="loadHistory"
        />
      </template>
    </LayoutHeader>

    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar for Admins / Managers -->
      <div v-if="isAdmin() || isManager()" class="w-64 border-r border-outline-gray-2 bg-surface-gray-1 overflow-y-auto flex flex-col shrink-0 transition-all">
        <div class="px-4 py-3 text-sm font-semibold text-ink-gray-9 border-b border-outline-gray-2 sticky top-0 bg-surface-gray-1 z-10">
          {{ __('Team Members') }}
        </div>
        
        <button
          v-for="u in usersList"
          :key="u.name"
          @click="onUserChange(u.name)"
          :class="['flex items-center gap-3 px-4 py-3 text-left hover:bg-surface-gray-2 transition-all group', selectedUser === u.name ? 'bg-surface-gray-2 relative' : '']"
        >
          <div v-if="selectedUser === u.name" class="absolute left-0 top-3 bottom-3 w-1 bg-ink-gray-9 rounded-r-full"></div>
          <UserAvatar :user="u.name" size="lg" class="shrink-0 transition-transform group-hover:scale-105" />
          <div class="flex flex-col justify-center overflow-hidden">
            <span :class="['text-sm font-bold truncate transition-colors', selectedUser === u.name ? 'text-ink-gray-9' : 'text-ink-gray-7 group-hover:text-ink-gray-9']">{{ u.full_name }}</span>
            <span class="text-xs text-ink-gray-4 truncate">{{ u.name }}</span>
          </div>
        </button>
      </div>

      <!-- Main Content Area -->
      <div class="flex-1 overflow-y-auto p-6 bg-base">
        <!-- Loading state -->
      <div v-if="loading" class="flex h-full items-center justify-center">
        <div class="text-base text-ink-gray-4">{{ __('Loading lead history...') }}</div>
      </div>

      <div v-else>
        <!-- Stats cards - Global view -->
        <div v-if="viewType === 'global'" class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div class="rounded-xl border border-outline-gray-2 bg-surface-gray-2 p-5 shadow-sm transition-all hover:shadow-md">
            <div class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5 mb-2">{{ __('Completed') }}</div>
            <div class="text-3xl font-bold text-ink-green-3">{{ doneCount }}</div>
          </div>
          <div class="rounded-xl border border-outline-gray-2 bg-surface-gray-2 p-5 shadow-sm transition-all hover:shadow-md">
            <div class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5 mb-2">{{ __('Rejected') }}</div>
            <div class="text-3xl font-bold text-ink-red-3">{{ rejectedCount }}</div>
          </div>
          <div class="rounded-xl border border-outline-gray-2 bg-surface-gray-2 p-5 shadow-sm transition-all hover:shadow-md">
            <div class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5 mb-2">{{ __('Total') }}</div>
            <div class="text-3xl font-bold text-ink-gray-9">{{ leads.length }}</div>
          </div>
        </div>

        <!-- Stats cards - Personal view -->
        <div v-else class="grid grid-cols-1 gap-6 mb-8" style="max-width: 300px;">
          <div class="rounded-xl border border-outline-gray-2 bg-surface-gray-2 p-5 shadow-sm transition-all hover:shadow-md">
            <div class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5 mb-2">{{ __('Total Leads Handled') }}</div>
            <div class="text-3xl font-bold text-ink-blue-3">{{ leads.length }}</div>
          </div>
        </div>

        <!-- Viewing indicator -->
        <div
          v-if="historyData?.full_name && selectedUser"
          class="mb-6 flex items-center gap-3 rounded-xl border border-outline-gray-2 bg-surface-gray-2 px-5 py-3 shadow-sm"
        >
          <UserAvatar :user="selectedUser" size="lg" />
          <div class="flex flex-col">
            <span class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5">{{ __('Viewing History') }}</span>
            <span class="text-lg font-bold text-ink-gray-9 leading-tight">{{ historyData.full_name }}</span>
          </div>
        </div>

        <!-- Filters row -->
        <div class="mb-8 flex items-center gap-6 flex-wrap bg-surface-gray-1 p-4 rounded-xl border border-outline-gray-2 shadow-sm">
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em] ml-1">{{ __('Status') }}</label>
            <select
              v-model="filterStatus"
              class="form-control text-sm w-[160px] !bg-surface-gray-2 !border-outline-gray-2 focus:!border-ink-gray-9 transition-all rounded-md"
            >
              <option value="">{{ __('All Statuses') }}</option>
              <option value="Working">{{ __('Working') }}</option>
              <option value="Done">{{ __('Done') }}</option>
              <option value="Completed">{{ __('Completed') }}</option>
              <option value="Rejected">{{ __('Rejected') }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em] ml-1">{{ __('Action') }}</label>
            <select
              v-model="filterAction"
              class="form-control text-sm w-[180px] !bg-surface-gray-2 !border-outline-gray-2 focus:!border-ink-gray-9 transition-all rounded-md"
            >
              <option value="">{{ __('All Actions') }}</option>
              <option value="Forward">{{ __('Mark Done') }}</option>
              <option value="Backward">{{ __('Send Back') }}</option>
              <option value="Reject">{{ __('Reject') }}</option>
              <option value="Manager Override">{{ __('Transfer') }}</option>
              <option value="Initial">{{ __('Initial') }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1.5 grow max-w-[300px]">
            <label class="text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em] ml-1">{{ __('Search') }}</label>
            <input
              v-model="searchQuery"
              type="text"
              class="form-control text-sm !bg-surface-gray-2 !border-outline-gray-2 focus:!border-ink-gray-9 transition-all rounded-md placeholder:text-ink-gray-3"
              :placeholder="__('Lead name or ID...')"
            />
          </div>
          <div class="mt-auto pb-0.5">
            <Button
              v-if="filterStatus || filterAction || searchQuery"
              :label="__('Clear Filters')"
              variant="subtle"
              theme="gray"
              size="sm"
              class="!h-9"
              @click="clearFilters"
            />
          </div>
        </div>

        <!-- Previously Handled Leads table -->
        <div>
          <h3 class="text-base font-semibold text-ink-gray-9 mb-3 flex items-center gap-2">
            <span>✅</span>
            {{ viewType === 'global' ? __('All Completed / Rejected Leads') : __('Previously Handled Leads') }}
            <span class="text-sm font-normal text-ink-gray-5">({{ filteredLeads.length }})</span>
          </h3>
          <div v-if="filteredLeads.length" class="rounded-xl border border-outline-gray-2 shadow-sm overflow-hidden bg-surface-gray-1">
            <table class="w-full">
              <thead>
                <tr class="bg-surface-gray-2 border-b border-outline-gray-2">
                  <th class="px-5 py-3 text-left text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em]">{{ __('Lead ID') }}</th>
                  <th class="px-5 py-3 text-left text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em]">{{ __('Lead Name') }}</th>
                  <th class="px-5 py-3 text-left text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em]">{{ __('Department') }}</th>
                  <th class="px-5 py-3 text-left text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em]">{{ viewType === 'global' ? __('Last Action') : __('Action Taken') }}</th>
                  <th class="px-5 py-3 text-left text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em]">{{ __('Status') }}</th>
                  <th v-if="viewType === 'global'" class="px-5 py-3 text-left text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em]">{{ __('Last Handled By') }}</th>
                  <th class="px-5 py-3 text-left text-[10px] font-bold text-ink-gray-4 uppercase tracking-[0.05em] w-[140px]">{{ __('Last Updated') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="lead in filteredLeads"
                  :key="lead.name"
                  class="border-b border-outline-gray-2 last:border-0 hover:bg-surface-gray-2 cursor-pointer transition-colors group"
                  @click="openLead(lead.name)"
                >
                  <td class="px-5 py-3">
                    <span class="text-sm font-semibold text-ink-blue-3 group-hover:underline">{{ lead.name }}</span>
                  </td>
                  <td class="px-5 py-3 text-sm font-medium text-ink-gray-9">{{ lead.lead_name || '—' }}</td>
                  <td class="px-5 py-3">
                    <Badge variant="subtle" :label="lead.current_department || '—'" theme="blue" />
                  </td>
                  <td class="px-5 py-3">
                    <Badge
                      v-if="getLeadAction(lead)"
                      variant="subtle"
                      :label="getActionLabel(getLeadAction(lead))"
                      :theme="getActionTheme(getLeadAction(lead))"
                    />
                    <span v-else class="text-sm text-ink-gray-4">—</span>
                  </td>
                  <td class="px-5 py-3">
                    <Badge
                      variant="subtle"
                      :label="lead.department_status || lead.status || '—'"
                      :theme="getStatusTheme(lead.department_status || lead.status)"
                    />
                  </td>
                  <td v-if="viewType === 'global'" class="px-5 py-3 text-sm font-medium text-ink-gray-7">
                    {{ lead.last_handled_by_name || '—' }}
                  </td>
                  <td class="px-5 py-3 text-xs text-ink-gray-5">
                    <Tooltip :text="formatDate(lead.modified)">
                      <div class="flex items-center gap-1.5 justify-end">
                        <span class="w-1.5 h-1.5 rounded-full bg-surface-gray-4"></span>
                        {{ __(timeAgo(lead.modified)) }}
                      </div>
                    </Tooltip>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="flex items-center justify-center rounded-lg border border-dashed py-8">
            <span class="text-sm text-ink-gray-4">
              {{ (filterStatus || filterAction || searchQuery) ? __('No leads match the selected filters') : (viewType === 'global' ? __('No completed or rejected leads yet') : __('No lead history found')) }}
            </span>
          </div>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import LayoutHeader from '@/components/LayoutHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { timeAgo, formatDate } from '@/utils'
import { Breadcrumbs, Badge, Tooltip, Button, usePageMeta, call } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { getUser, isManager, isAdmin, users } = usersStore()

const usersList = computed(() => {
  return users.data?.crmUsers || []
})

const loading = ref(false)
const selectedUser = ref(null)
const historyData = ref(null)
const leads = ref([])
const viewType = ref('global')
const doneCount = ref(0)
const rejectedCount = ref(0)

// Filters
const filterStatus = ref('')
const filterAction = ref('')
const searchQuery = ref('')

const filteredLeads = computed(() => {
  let result = leads.value
  if (filterStatus.value) {
    if (filterStatus.value === 'Completed') {
      result = result.filter(l => l.status === 'Completed' || l.department_status === 'Done')
    } else {
      result = result.filter(l => l.department_status === filterStatus.value || l.status === filterStatus.value)
    }
  }
  if (filterAction.value) {
    result = result.filter(l => {
      const action = l.last_action || l.user_action
      return action === filterAction.value
    })
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(l =>
      (l.name && l.name.toLowerCase().includes(q)) ||
      (l.lead_name && l.lead_name.toLowerCase().includes(q))
    )
  }
  return result
})

function clearFilters() {
  filterStatus.value = ''
  filterAction.value = ''
  searchQuery.value = ''
}

async function loadHistory() {
  loading.value = true
  try {
    const args = {}
    if (selectedUser.value) {
      args.user = selectedUser.value
    }
    const data = await call(
      'lead_routing.api.lead_history.get_my_lead_history',
      args,
    )
    historyData.value = data
    leads.value = data.leads || []
    viewType.value = data.view_type || 'global'
    doneCount.value = data.done_count || 0
    rejectedCount.value = data.rejected_count || 0
  } catch (e) {
    console.error('Failed to load lead history:', e)
    leads.value = []
  } finally {
    loading.value = false
  }
}

function onUserChange(value) {
  selectedUser.value = value
  clearFilters()
  loadHistory()
}

function openLead(leadId) {
  router.push({ name: 'Lead', params: { leadId } })
}

function getLeadAction(lead) {
  return lead.last_action || lead.user_action || null
}

const actionLabels = {
  'Forward': 'Mark Done',
  'Backward': 'Send Back',
  'Reject': 'Reject to Onboarding',
  'Manager Override': 'Manager Override',
  'Initial': 'Initial Assignment',
}

function getActionLabel(action) {
  return actionLabels[action] || action
}

function getActionTheme(action) {
  const themes = {
    'Forward': 'green',
    'Backward': 'orange',
    'Reject': 'red',
    'Manager Override': 'blue',
    'Initial': 'gray',
  }
  return themes[action] || 'gray'
}

function getStatusTheme(status) {
  if (!status) return 'gray'
  const s = status.toLowerCase()
  if (s === 'done' || s === 'completed') return 'green'
  if (s === 'rejected') return 'red'
  if (s === 'working') return 'orange'
  return 'blue'
}

onMounted(() => {
  const currentUser = getUser()
  if (currentUser) {
    selectedUser.value = currentUser.name
  }
  loadHistory()
})

usePageMeta(() => {
  if (viewType.value === 'global' && !selectedUser.value) {
    return { title: __('Lead History — All Completed / Rejected') }
  }
  if (historyData.value?.full_name) {
    return { title: __('Lead History: {0}', [historyData.value.full_name]) }
  }
  return { title: __('Lead History') }
})
</script>
