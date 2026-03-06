<template>
  <div class="hierarchy-dropdown-view">
    <div class="header">
      <h2>Organization Structure</h2>
      <Button @click="refreshData" :loading="loading">
        <template #prefix>
          <RefreshIcon class="h-4 w-4" />
        </template>
        Refresh
      </Button>
    </div>

    <!-- Shift Dropdown Menu -->
    <div class="shift-menu">
      <div 
        v-for="shift in hierarchyData" 
        :key="shift.name" 
        class="shift-card"
      >
        <!-- Shift Header (Clickable) -->
        <div 
          class="shift-header"
          @click="toggleShift(shift.name)"
          :class="{ expanded: expandedShifts.includes(shift.name) }"
        >
          <div class="shift-info">
            <div class="shift-title">
              <ClockIcon class="icon" />
              <h3>{{ shift.shift_name }}</h3>
              <Badge variant="outline">{{ shift.departments.length }} depts</Badge>
            </div>
            <div class="shift-timing">
              {{ formatTime(shift.start_time) }} - {{ formatTime(shift.end_time) }}
              <span class="duration">• {{ getShiftDuration(shift.start_time, shift.end_time) }}</span>
            </div>
          </div>
          <ChevronDownIcon 
            class="chevron" 
            :class="{ rotated: expandedShifts.includes(shift.name) }"
          />
        </div>

        <!-- Departments Dropdown (Shown when shift expanded) -->
        <div 
          v-if="expandedShifts.includes(shift.name)" 
          class="departments-dropdown"
        >
          <div 
            v-for="dept in shift.departments" 
            :key="dept.name" 
            class="department-card"
          >
            <!-- Department Header (Clickable) -->
            <div 
              class="department-header"
              @click="toggleDepartment(dept.name)"
              :class="{ expanded: expandedDepartments.includes(dept.name) }"
            >
              <div class="department-info">
                <div class="department-title">
                  <BuildingIcon class="icon" />
                  <h4>{{ dept.department_name }}</h4>
                  <Badge variant="outline" size="sm">{{ dept.teams.length }} teams</Badge>
                </div>
                <div class="department-meta">
                  <span class="dept-id">{{ dept.name }}</span>
                  <span v-if="dept.department_head" class="dept-head">
                    Head: {{ dept.department_head }}
                  </span>
                </div>
              </div>
              <ChevronDownIcon 
                class="chevron" 
                :class="{ rotated: expandedDepartments.includes(dept.name) }"
              />
            </div>

            <!-- Teams Dropdown (Shown when department expanded) -->
            <div 
              v-if="expandedDepartments.includes(dept.name)" 
              class="teams-dropdown"
            >
              <div 
                v-for="team in dept.teams" 
                :key="team.name" 
                class="team-card"
              >
                <!-- Team Header (Clickable) -->
                <div 
                  class="team-header"
                  @click="toggleTeam(team.name)"
                  :class="{ expanded: expandedTeams.includes(team.name) }"
                >
                  <div class="team-info">
                    <div class="team-title">
                      <UsersIcon class="icon" />
                      <h5>{{ team.team_name }}</h5>
                      <Badge size="sm">{{ team.agents.length }} agents</Badge>
                    </div>
                    <div class="team-meta">
                      <span class="team-id">{{ team.name }}</span>
                      <span v-if="team.team_leader" class="team-leader">
                        Leader: {{ team.team_leader }}
                      </span>
                    </div>
                  </div>
                  <ChevronDownIcon 
                    class="chevron" 
                    :class="{ rotated: expandedTeams.includes(team.name) }"
                  />
                </div>

                <!-- Agents List (Shown when team expanded) -->
                <div 
                  v-if="expandedTeams.includes(team.name)" 
                  class="agents-list"
                >
                  <div 
                    v-for="agent in team.agents" 
                    :key="agent.name" 
                    class="agent-item"
                  >
                    <UserIcon class="icon" />
                    <div class="agent-details">
                      <span class="agent-name">{{ agent.full_name }}</span>
                      <span class="agent-email">{{ agent.email }}</span>
                    </div>
                  </div>
                  <div v-if="team.agents.length === 0" class="empty-agents">
                    No agents assigned to this team
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
      <h3>No Shifts Configured</h3>
      <p>Create shifts, departments, and teams to see the hierarchy</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createResource, Badge, Button } from 'frappe-ui'
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

const hierarchyResource = createResource({
  url: 'crm.api.hierarchy.get_hierarchy_tree',
  auto: true,
  onSuccess(data) {
    hierarchyData.value = data
    // Auto-expand first shift
    if (data.length > 0) {
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
.hierarchy-dropdown-view {
  padding: 1.5rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
}

.shift-menu {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Shift Card */
.shift-card {
  background: white;
  border: 2px solid #3b82f6;
  border-radius: 0.75rem;
  overflow: hidden;
}

.shift-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem;
  cursor: pointer;
  transition: background 0.2s;
  background: #eff6ff;
}

.shift-header:hover {
  background: #dbeafe;
}

.shift-header.expanded {
  background: #3b82f6;
  color: white;
}

.shift-info {
  flex: 1;
}

.shift-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.shift-title .icon {
  width: 1.5rem;
  height: 1.5rem;
}

.shift-title h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.shift-timing {
  font-size: 0.875rem;
  opacity: 0.9;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.duration {
  font-weight: 500;
}

.chevron {
  width: 1.25rem;
  height: 1.25rem;
  transition: transform 0.2s;
}

.chevron.rotated {
  transform: rotate(180deg);
}

/* Departments Dropdown */
.departments-dropdown {
  padding: 1rem;
  background: #f9fafb;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.department-card {
  background: white;
  border: 2px solid #10b981;
  border-radius: 0.5rem;
  overflow: hidden;
}

.department-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  cursor: pointer;
  transition: background 0.2s;
  background: #ecfdf5;
}

.department-header:hover {
  background: #d1fae5;
}

.department-header.expanded {
  background: #10b981;
  color: white;
}

.department-info {
  flex: 1;
}

.department-title {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  margin-bottom: 0.375rem;
}

.department-title .icon {
  width: 1.25rem;
  height: 1.25rem;
}

.department-title h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.department-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.8125rem;
  opacity: 0.9;
}

.dept-id, .team-id {
  font-family: monospace;
  font-size: 0.75rem;
  opacity: 0.7;
}

/* Teams Dropdown */
.teams-dropdown {
  padding: 0.75rem;
  background: #f3f4f6;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.team-card {
  background: white;
  border: 2px solid #f59e0b;
  border-radius: 0.5rem;
  overflow: hidden;
}

.team-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem;
  cursor: pointer;
  transition: background 0.2s;
  background: #fffbeb;
}

.team-header:hover {
  background: #fef3c7;
}

.team-header.expanded {
  background: #f59e0b;
  color: white;
}

.team-info {
  flex: 1;
}

.team-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.team-title .icon {
  width: 1.125rem;
  height: 1.125rem;
}

.team-title h5 {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0;
}

.team-meta {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 0.75rem;
  opacity: 0.9;
}

/* Agents List */
.agents-list {
  padding: 0.75rem;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.agent-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.agent-item .icon {
  width: 1rem;
  height: 1rem;
  color: #6b7280;
}

.agent-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.agent-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
}

.agent-email {
  font-size: 0.75rem;
  color: #6b7280;
}

.empty-agents {
  text-align: center;
  padding: 1rem;
  color: #9ca3af;
  font-size: 0.875rem;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.empty-icon {
  width: 3rem;
  height: 3rem;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.empty-state h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.empty-state p {
  font-size: 0.875rem;
  color: #6b7280;
}
</style>
