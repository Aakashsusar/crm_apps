<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-ink-gray-9">Call Center Dashboard</h1>
      <p class="text-ink-gray-5">Monitor real-time call activity and agent performance</p>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-surface-white rounded-lg shadow p-4 border border-outline-gray-2">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-ink-gray-5">Active Calls</p>
            <p class="text-2xl font-bold text-blue-600">{{ summaryStats.active_calls }}</p>
          </div>
          <PhoneIcon class="size-8 text-blue-500" />
        </div>
      </div>
      
      <div class="bg-surface-white rounded-lg shadow p-4 border border-outline-gray-2">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-ink-gray-5">In Queue</p>
            <p class="text-2xl font-bold text-orange-600">{{ summaryStats.queued_calls }}</p>
          </div>
          <ClockIcon class="size-8 text-orange-500" />
        </div>
      </div>
      
      <div class="bg-surface-white rounded-lg shadow p-4 border border-outline-gray-2">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-ink-gray-5">Completed Today</p>
            <p class="text-2xl font-bold text-green-600">{{ summaryStats.completed_calls }}</p>
          </div>
          <CheckIcon class="size-8 text-green-500" />
        </div>
      </div>
      
      <div class="bg-surface-white rounded-lg shadow p-4 border border-outline-gray-2">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-ink-gray-5">Available Agents</p>
            <p class="text-2xl font-bold text-purple-600">{{ summaryStats.available_agents }}</p>
          </div>
          <UsersIcon class="size-8 text-purple-500" />
        </div>
      </div>
    </div>

    <!-- Main Dashboard Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Column - Active Calls and Queue -->
      <div class="lg:col-span-2 space-y-6">
        <ActiveCallsWidget />
        <CallQueueWidget />
      </div>
      
      <!-- Right Column - Recent Calls and Agent Status -->
      <div class="space-y-6">
        <RecentCallsWidget />
        <div class="bg-surface-white rounded-lg shadow p-4">
          <h3 class="text-lg font-semibold text-ink-gray-9 mb-4">Agent Performance</h3>
          <div class="space-y-4">
            <div
              v-for="agent in agentPerformance"
              :key="agent.name"
              class="flex items-center justify-between p-3 rounded-lg hover:bg-surface-gray-1"
            >
              <div class="flex items-center gap-3">
                <UserAvatar :user="agent.name" size="sm" />
                <div>
                  <div class="font-medium text-ink-gray-9">{{ agent.full_name }}</div>
                  <div class="text-sm text-ink-gray-5">{{ agent.department }}</div>
                </div>
              </div>
              <div class="text-right">
                <div class="text-sm font-medium text-ink-gray-9">{{ agent.calls_today }}</div>
                <div class="text-xs text-ink-gray-5">calls today</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Incoming Call Alert (Global) -->
    <IncomingCallAlert />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import ActiveCallsWidget from './ActiveCallsWidget.vue'
import RecentCallsWidget from './RecentCallsWidget.vue'
import CallQueueWidget from './CallQueueWidget.vue'
import IncomingCallAlert from './IncomingCallAlert.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import ClockIcon from '@/components/Icons/ClockIcon.vue'
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import UsersIcon from '@/components/Icons/UsersIcon.vue'

const summaryStats = ref({
  active_calls: 0,
  queued_calls: 0,
  completed_calls: 0,
  available_agents: 0
})

const agentPerformance = ref([])

// Fetch dashboard summary
const summaryResource = createResource({
  url: 'crm.api.call_center.get_dashboard_summary',
  auto: true,
  onSuccess(data) {
    summaryStats.value = data.stats || {
      active_calls: 0,
      queued_calls: 0,
      completed_calls: 0,
      available_agents: 0
    }
    agentPerformance.value = data.agent_performance || []
  }
})

function refreshDashboard() {
  summaryResource.reload()
}

// Auto-refresh dashboard
onMounted(() => {
  setInterval(() => {
    if (document.visibilityState === 'visible') {
      refreshDashboard()
    }
  }, 15000) // Refresh every 15 seconds
})
</script>