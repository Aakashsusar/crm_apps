<template>
  <div class="compact-hierarchy-selector">
    <!-- Single Dropdown showing full hierarchy -->
    <Dropdown :options="hierarchyOptions" v-model="selectedValue">
      <template #default="{ open }">
        <Button class="selector-button" :class="{ open }">
          <template #prefix>
            <component :is="getIcon()" class="h-4 w-4" />
          </template>
          <span class="button-text">
            {{ selectedLabel || 'Select Shift → Department → Team' }}
          </span>
          <template #suffix>
            <ChevronDownIcon class="h-4 w-4" :class="{ 'rotate-180': open }" />
          </template>
        </Button>
      </template>
    </Dropdown>

    <!-- Selected Path Display -->
    <div v-if="selectedPath" class="selected-path">
      <div class="path-breadcrumb">
        <span class="path-item shift">
          <ClockIcon class="icon" />
          {{ selectedPath.shift }}
        </span>
        <ChevronRightIcon class="separator" />
        <span class="path-item department">
          <BuildingIcon class="icon" />
          {{ selectedPath.department }}
        </span>
        <ChevronRightIcon class="separator" />
        <span class="path-item team">
          <UsersIcon class="icon" />
          {{ selectedPath.team }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Dropdown, Button, createResource } from 'frappe-ui'
import { 
  Clock as ClockIcon, 
  Building2 as BuildingIcon, 
  Users as UsersIcon, 
  ChevronDown as ChevronDownIcon,
  ChevronRight as ChevronRightIcon 
} from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const selectedValue = ref(null)
const selectedPath = ref(null)
const hierarchyData = ref([])

// Fetch hierarchy tree
const hierarchyResource = createResource({
  url: 'crm.api.hierarchy.get_hierarchy_tree',
  auto: true,
  onSuccess(data) {
    hierarchyData.value = data
  }
})

// Build hierarchical dropdown options
const hierarchyOptions = computed(() => {
  const options = []
  
  hierarchyData.value.forEach(shift => {
    // Shift group header
    options.push({
      label: `${shift.shift_name} (${formatTime(shift.start_time)} - ${formatTime(shift.end_time)})`,
      value: null,
      isGroup: true,
      icon: ClockIcon
    })
    
    shift.departments.forEach(dept => {
      // Department sub-header
      options.push({
        label: `  ${dept.department_name}`,
        value: null,
        isGroup: true,
        icon: BuildingIcon,
        indent: 1
      })
      
      dept.teams.forEach(team => {
        // Team option (selectable)
        options.push({
          label: `    ${team.team_name}`,
          value: {
            shift: shift.name,
            shift_name: shift.shift_name,
            department: dept.name,
            department_name: dept.department_name,
            team: team.name,
            team_name: team.team_name
          },
          icon: UsersIcon,
          indent: 2
        })
      })
    })
  })
  
  return options
})

const selectedLabel = computed(() => {
  if (!selectedValue.value) return null
  const val = selectedValue.value
  return `${val.shift_name} → ${val.department_name} → ${val.team_name}`
})

function getIcon() {
  if (!selectedValue.value) return ClockIcon
  return UsersIcon
}

function formatTime(time) {
  if (!time) return ''
  const [hours, minutes] = time.split(':')
  const hour = parseInt(hours)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const displayHour = hour % 12 || 12
  return `${displayHour}:${minutes} ${ampm}`
}

watch(selectedValue, (newVal) => {
  if (newVal) {
    selectedPath.value = {
      shift: newVal.shift_name,
      department: newVal.department_name,
      team: newVal.team_name
    }
    emit('update:modelValue', newVal)
  } else {
    selectedPath.value = null
    emit('update:modelValue', null)
  }
})

// Initialize from prop
watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.team) {
    selectedValue.value = newVal
  }
}, { immediate: true })
</script>

<style scoped>
.compact-hierarchy-selector {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.selector-button {
  width: 100%;
  justify-content: space-between;
}

.selector-button.open {
  border-color: #3b82f6;
}

.button-text {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-path {
  padding: 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
}

.path-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.path-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.625rem;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
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
  width: 0.875rem;
  height: 0.875rem;
}

.separator {
  width: 0.875rem;
  height: 0.875rem;
  color: #9ca3af;
}
</style>
