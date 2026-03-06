<template>
  <div class="sidebar-hierarchy-menu">
    <!-- Header -->
    <div class="menu-header">
      <div class="header-content">
        <h3>Organization</h3>
        <span v-if="isFiltered" class="filter-badge" title="Showing only your team">👤</span>
      </div>
      <button @click="refreshData" class="refresh-btn" :disabled="loading">
        <RefreshIcon :class="{ 'animate-spin': loading }" />
      </button>
    </div>

    <!-- Shift List -->
    <div class="shift-list">
      <div 
        v-for="shift in hierarchyData" 
        :key="shift.name" 
        class="shift-item"
      >
        <!-- Shift Header -->
        <button 
          class="shift-button"
          :class="{ expanded: expandedShifts.includes(shift.name) }"
          @click="toggleShift(shift.name)"
        >
          <div class="shift-content">
            <div class="shift-title">
              <ClockIcon class="icon" />
              <span class="shift-name">{{ shift.shift_name }}</span>
            </div>
            <div class="shift-meta">
              <span class="timing">{{ formatTime(shift.start_time) }} - {{ formatTime(shift.end_time) }}</span>
              <span class="duration">• {{ getShiftDuration(shift.start_time, shift.end_time) }}</span>
              <span class="count">[{{ shift.departments.length }} depts]</span>
            </div>
          </div>
          <ChevronDownIcon 
            class="chevron" 
            :class="{ rotated: expandedShifts.includes(shift.name) }"
          />
        </button>

        <!-- Departments List -->
        <div 
          v-if="expandedShifts.includes(shift.name)" 
          class="departments-list"
        >
          <div 
            v-for="dept in shift.departments" 
            :key="dept.name" 
            class="department-item"
          >
            <!-- Department Button -->
            <button 
              class="department-button"
              :class="{ expanded: expandedDepartments.includes(dept.name) }"
              @click="toggleDepartment(dept.name)"
            >
              <div class="dept-content">
                <div class="dept-title">
                  <BuildingIcon class="icon" />
                  <span class="dept-name">{{ dept.department_name }}</span>
                </div>
                <div class="dept-meta">
                  <span class="dept-id">{{ dept.name }}</span>
                  <span class="count">[{{ dept.teams.length }} teams]</span>
                </div>
              </div>
              <ChevronDownIcon 
                class="chevron" 
                :class="{ rotated: expandedDepartments.includes(dept.name) }"
              />
            </button>

            <!-- Teams List -->
            <div 
              v-if="expandedDepartments.includes(dept.name)" 
              class="teams-list"
            >
              <div 
                v-for="team in dept.teams" 
                :key="team.name" 
                class="team-item"
              >
                <!-- Team Button -->
                <button 
                  class="team-button"
                  :class="{ expanded: expandedTeams.includes(team.name) }"
                  @click="toggleTeam(team.name)"
                >
                  <div class="team-content">
                    <div class="team-title">
                      <UsersIcon class="icon" />
                      <span class="team-name">{{ team.team_name }}</span>
                    </div>
                    <span class="count">[{{ team.agents.length }}]</span>
                  </div>
                  <ChevronDownIcon 
                    class="chevron" 
                    :class="{ rotated: expandedTeams.includes(team.name) }"
                  />
                </button>

                <!-- Agents List -->
                <div 
                  v-if="expandedTeams.includes(team.name)" 
                  class="agents-list"
                >
                  <div
                    v-for="agent in team.agents" 
                    :key="agent.name"
                    class="agent-item-wrapper"
                    @mouseenter="hoveredAgent = agent.name"
                    @mouseleave="hoveredAgent = null"
                  >
                    <router-link
                      :to="{ name: 'Dashboard', query: { user: agent.name } }"
                      class="agent-item"
                    >
                      <UserIcon class="icon" />
                      <span class="agent-name">{{ agent.full_name }}</span>
                    </router-link>
                    
                    <!-- Quick Actions Dropdown -->
                    <div 
                      v-if="hoveredAgent === agent.name"
                      class="agent-actions"
                    >
                      <router-link
                        :to="{ name: 'Dashboard', query: { user: agent.name } }"
                        class="action-link"
                        title="View Dashboard"
                      >
                        📊 Dashboard
                      </router-link>
                      <router-link
                        :to="{ name: 'Leads', query: { lead_owner: agent.name } }"
                        class="action-link"
                        title="View Leads"
                      >
                        📋 Leads
                      </router-link>
                      <router-link
                        :to="{ name: 'Deals', query: { deal_owner: agent.name } }"
                        class="action-link"
                        title="View Deals"
                      >
                        💼 Deals
                      </router-link>
                    </div>
                  </div>
                  <div v-if="team.agents.length === 0" class="empty-message">
                    No agents
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="hierarchyData.length === 0 && !loading" class="empty-state">
      <ClockIcon class="empty-icon" />
      <p>No shifts configured</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { 
  RefreshCw as RefreshIcon, 
  Clock as ClockIcon, 
  Building2 as BuildingIcon, 
  Users as UsersIcon, 
  User as UserIcon,
  ChevronDown as ChevronDownIcon 
} from 'lucide-vue-next'

const loading = ref(false)
const hierarchyData = ref([])
const expandedShifts = ref([])
const expandedDepartments = ref([])
const expandedTeams = ref([])
const hoveredAgent = ref(null)
const isFiltered = ref(false)

const hierarchyResource = createResource({
  url: 'crm.api.hierarchy.get_hierarchy_tree',
  auto: true,
  onSuccess(data) {
    console.log('[HIERARCHY] Full data received:', data)
    hierarchyData.value = data
    
    // Check if data is filtered (only 1 shift with 1 department with 1 team)
    if (data.length === 1 && 
        data[0].departments.length === 1 && 
        data[0].departments[0].teams.length === 1) {
      isFiltered.value = true
    } else {
      isFiltered.value = false
    }
    
    // Debug: Log each shift's departments and teams
    data.forEach(shift => {
      console.log(`[HIERARCHY] Shift: ${shift.shift_name}`)
      shift.departments.forEach(dept => {
        console.log(`  Department: ${dept.department_name} (${dept.name})`)
        dept.teams.forEach(team => {
          console.log(`    Team: ${team.team_name} (${team.name}) - ${team.agents.length} agents`)
          team.agents.forEach(agent => {
            console.log(`      Agent: ${agent.full_name} (${agent.name})`)
          })
        })
      })
    })
    
    // Auto-expand first shift
    if (data.length > 0 && expandedShifts.value.length === 0) {
      expandedShifts.value = [data[0].name]
    }
  }
})

function refreshData() {
  loading.value = true
  hierarchyResource.reload().finally(() => {
    loading.value = false
  })
}

function toggleShift(shiftName) {
  const index = expandedShifts.value.indexOf(shiftName)
  if (index > -1) {
    expandedShifts.value.splice(index, 1)
  } else {
    expandedShifts.value.push(shiftName)
  }
}

function toggleDepartment(deptName) {
  const index = expandedDepartments.value.indexOf(deptName)
  if (index > -1) {
    expandedDepartments.value.splice(index, 1)
  } else {
    expandedDepartments.value.push(deptName)
  }
}

function toggleTeam(teamName) {
  const index = expandedTeams.value.indexOf(teamName)
  if (index > -1) {
    expandedTeams.value.splice(index, 1)
  } else {
    expandedTeams.value.push(teamName)
  }
}

function formatTime(time) {
  if (!time) return ''
  const [hours, minutes] = time.split(':')
  const hour = parseInt(hours)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const displayHour = hour % 12 || 12
  return `${displayHour}:${minutes} ${ampm}`
}

function getShiftDuration(start, end) {
  if (!start || !end) return ''
  const startHour = parseInt(start.split(':')[0])
  const endHour = parseInt(end.split(':')[0])
  let duration = endHour - startHour
  if (duration < 0) duration += 24
  return `${duration}h`
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.sidebar-hierarchy-menu {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
}

/* Header */
.menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.menu-header h3 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.filter-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  font-size: 0.75rem;
  background: #dbeafe;
  border-radius: 50%;
  cursor: help;
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #f3f4f6;
  color: #111827;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-btn svg {
  width: 1rem;
  height: 1rem;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Shift List */
.shift-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.shift-item {
  margin-bottom: 0.5rem;
}

/* Shift Button */
.shift-button {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0.75rem;
  border: none;
  background: #eff6ff;
  color: #1e40af;
  cursor: pointer;
  border-radius: 0.5rem;
  transition: all 0.2s;
  text-align: left;
}

.shift-button:hover {
  background: #dbeafe;
}

.shift-button.expanded {
  background: #3b82f6;
  color: white;
}

.shift-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.shift-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.shift-title .icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.shift-name {
  font-size: 0.875rem;
  font-weight: 600;
}

.shift-meta {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  opacity: 0.9;
  flex-wrap: wrap;
}

.timing, .duration, .count {
  white-space: nowrap;
}

.chevron {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  transition: transform 0.2s;
  margin-top: 0.125rem;
}

.chevron.rotated {
  transform: rotate(180deg);
}

/* Departments List */
.departments-list {
  margin-top: 0.375rem;
  margin-left: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.department-item {
  display: flex;
  flex-direction: column;
}

/* Department Button */
.department-button {
  width: 100%;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 0.625rem;
  border: none;
  background: #ecfdf5;
  color: #065f46;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
  text-align: left;
}

.department-button:hover {
  background: #d1fae5;
}

.department-button.expanded {
  background: #10b981;
  color: white;
}

.dept-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.dept-title {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.dept-title .icon {
  width: 0.875rem;
  height: 0.875rem;
  flex-shrink: 0;
}

.dept-name {
  font-size: 0.8125rem;
  font-weight: 600;
}

.dept-meta {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.6875rem;
  opacity: 0.9;
}

.dept-id {
  font-family: monospace;
  font-size: 0.625rem;
}

/* Teams List */
.teams-list {
  margin-top: 0.375rem;
  margin-left: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.team-item {
  display: flex;
  flex-direction: column;
}

/* Team Button */
.team-button {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem;
  border: none;
  background: #fffbeb;
  color: #92400e;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
  text-align: left;
}

.team-button:hover {
  background: #fef3c7;
}

.team-button.expanded {
  background: #f59e0b;
  color: white;
}

.team-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.team-title {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  flex: 1;
}

.team-title .icon {
  width: 0.75rem;
  height: 0.75rem;
  flex-shrink: 0;
}

.team-name {
  font-size: 0.75rem;
  font-weight: 600;
}

.team-content .count {
  font-size: 0.6875rem;
  opacity: 0.9;
}

/* Agents List */
.agents-list {
  margin-top: 0.25rem;
  margin-left: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.agent-item-wrapper {
  position: relative;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.5rem;
  background: #f9fafb;
  border-radius: 0.25rem;
  font-size: 0.6875rem;
  color: #374151;
  transition: all 0.2s;
  text-decoration: none;
  cursor: pointer;
}

.agent-item:hover {
  background: #e0e7ff;
  color: #4f46e5;
}

.agent-item:hover .icon {
  color: #4f46e5;
}

.agent-item .icon {
  width: 0.75rem;
  height: 0.75rem;
  color: #6b7280;
  flex-shrink: 0;
  transition: color 0.2s;
}

.agent-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Agent Actions Dropdown */
.agent-actions {
  position: absolute;
  left: 100%;
  top: 0;
  margin-left: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  padding: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  z-index: 1000;
  min-width: 120px;
}

.action-link {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.5rem;
  font-size: 0.6875rem;
  color: #374151;
  text-decoration: none;
  border-radius: 0.25rem;
  transition: all 0.2s;
  white-space: nowrap;
}

.action-link:hover {
  background: #f3f4f6;
  color: #4f46e5;
}

/* Empty States */
.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  text-align: center;
  color: #9ca3af;
}

.empty-icon {
  width: 2rem;
  height: 2rem;
  margin-bottom: 0.5rem;
}

.empty-state p,
.loading-state p {
  font-size: 0.8125rem;
  margin: 0;
}

.empty-message {
  padding: 0.5rem;
  text-align: center;
  font-size: 0.6875rem;
  color: #9ca3af;
  font-style: italic;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 0.5rem;
}

/* Scrollbar */
.shift-list::-webkit-scrollbar {
  width: 0.375rem;
}

.shift-list::-webkit-scrollbar-track {
  background: #f9fafb;
}

.shift-list::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 0.25rem;
}

.shift-list::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
