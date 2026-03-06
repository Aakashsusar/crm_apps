<template>
  <div class="hierarchy-selector">
    <!-- Shift Selection -->
    <div class="form-group">
      <label class="form-label">Select Shift</label>
      <Autocomplete
        v-model="selectedShift"
        :options="shiftOptions"
        placeholder="Choose a shift..."
        @change="onShiftChange"
      />
    </div>

    <!-- Department Selection -->
    <div v-if="selectedShift" class="form-group">
      <label class="form-label">Select Department</label>
      <Autocomplete
        v-model="selectedDepartment"
        :options="departmentOptions"
        placeholder="Choose a department..."
        @change="onDepartmentChange"
      />
    </div>

    <!-- Team Selection -->
    <div v-if="selectedDepartment" class="form-group">
      <label class="form-label">Select Team</label>
      <Autocomplete
        v-model="selectedTeam"
        :options="teamOptions"
        placeholder="Choose a team..."
        @change="onTeamChange"
      />
    </div>

    <!-- Selected Hierarchy Display -->
    <div v-if="selectedTeam" class="selected-hierarchy">
      <div class="hierarchy-path">
        <div class="path-item shift">
          <ClockIcon class="icon" />
          <span>{{ getShiftDisplay(selectedShift) }}</span>
        </div>
        <ChevronRightIcon class="separator" />
        <div class="path-item department">
          <BuildingIcon class="icon" />
          <span>{{ getDepartmentDisplay(selectedDepartment) }}</span>
        </div>
        <ChevronRightIcon class="separator" />
        <div class="path-item team">
          <UsersIcon class="icon" />
          <span>{{ getTeamDisplay(selectedTeam) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Autocomplete, createResource } from 'frappe-ui'
import { Clock as ClockIcon, Building2 as BuildingIcon, Users as UsersIcon, ChevronRight as ChevronRightIcon } from 'lucide-vue-next'

const emit = defineEmits(['update:shift', 'update:department', 'update:team'])

const selectedShift = ref(null)
const selectedDepartment = ref(null)
const selectedTeam = ref(null)

const shifts = ref([])
const departments = ref([])
const teams = ref([])

// Fetch all shifts
const shiftsResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'CRM Shift',
    filters: { enabled: 1 },
    fields: ['name', 'shift_name', 'shift_code', 'start_time', 'end_time'],
    order_by: 'start_time'
  },
  auto: true,
  onSuccess(data) {
    shifts.value = data
  }
})

// Shift options with timing
const shiftOptions = computed(() => {
  return shifts.value.map(shift => ({
    label: `${shift.shift_name} (${formatTime(shift.start_time)} - ${formatTime(shift.end_time)})`,
    value: shift.name,
    description: `${shift.shift_code || ''} • ${getShiftDuration(shift.start_time, shift.end_time)}`
  }))
})

// Department options
const departmentOptions = computed(() => {
  return departments.value.map(dept => ({
    label: dept.department_name,
    value: dept.name,
    description: `ID: ${dept.name}`
  }))
})

// Team options
const teamOptions = computed(() => {
  return teams.value.map(team => ({
    label: team.team_name,
    value: team.name,
    description: `ID: ${team.name} • Leader: ${team.team_leader || 'Not assigned'}`
  }))
})

// Fetch departments when shift changes
const departmentsResource = createResource({
  url: 'crm.fcrm.doctype.crm_department.crm_department.get_departments_by_shift',
  onSuccess(data) {
    departments.value = data
  }
})

// Fetch teams when department changes
const teamsResource = createResource({
  url: 'crm.fcrm.doctype.crm_team.crm_team.get_teams_by_department',
  onSuccess(data) {
    teams.value = data
  }
})

function onShiftChange(value) {
  selectedDepartment.value = null
  selectedTeam.value = null
  departments.value = []
  teams.value = []
  
  if (value) {
    departmentsResource.fetch({ shift: value })
  }
  
  emit('update:shift', value)
}

function onDepartmentChange(value) {
  selectedTeam.value = null
  teams.value = []
  
  if (value) {
    teamsResource.fetch({ department: value })
  }
  
  emit('update:department', value)
}

function onTeamChange(value) {
  emit('update:team', value)
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
  if (duration < 0) duration += 24 // Handle overnight shifts
  return `${duration} hours`
}

function getShiftDisplay(shiftName) {
  const shift = shifts.value.find(s => s.name === shiftName)
  return shift ? `${shift.shift_name} (${formatTime(shift.start_time)} - ${formatTime(shift.end_time)})` : shiftName
}

function getDepartmentDisplay(deptName) {
  const dept = departments.value.find(d => d.name === deptName)
  return dept ? dept.department_name : deptName
}

function getTeamDisplay(teamName) {
  const team = teams.value.find(t => t.name === teamName)
  return team ? team.team_name : teamName
}

// Watch for external changes
watch(() => selectedShift.value, (newVal) => {
  emit('update:shift', newVal)
})

watch(() => selectedDepartment.value, (newVal) => {
  emit('update:department', newVal)
})

watch(() => selectedTeam.value, (newVal) => {
  emit('update:team', newVal)
})
</script>

<style scoped>
.hierarchy-selector {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.selected-hierarchy {
  margin-top: 0.5rem;
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
}

.hierarchy-path {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.path-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.path-item.shift {
  background: #dbeafe;
  color: #1e40af;
}

.path-item.department {
  background: #d1fae5;
  color: #065f46;
}

.path-item.team {
  background: #fef3c7;
  color: #92400e;
}

.path-item .icon {
  width: 1rem;
  height: 1rem;
}

.separator {
  width: 1rem;
  height: 1rem;
  color: #9ca3af;
}
</style>
