<template>
  <div class="hierarchy-dashboard">
    <div class="header">
      <h2>CRM Hierarchy</h2>
      <Button @click="refreshHierarchy" :loading="loading">
        <template #prefix>
          <RefreshIcon class="h-4 w-4" />
        </template>
        Refresh
      </Button>
    </div>

    <!-- User's Current Hierarchy -->
    <div v-if="userHierarchy" class="user-hierarchy-card">
      <h3>Your Assignment</h3>
      <div class="hierarchy-info">
        <div class="info-item">
          <label>Shift:</label>
          <span class="value">
            {{ userHierarchy.shift?.shift_name || 'Not Assigned' }}
            <Badge 
              v-if="userHierarchy.shift" 
              :variant="userHierarchy.is_shift_active ? 'success' : 'subtle'"
            >
              {{ userHierarchy.is_shift_active ? 'Active' : 'Inactive' }}
            </Badge>
          </span>
        </div>
        <div class="info-item" v-if="userHierarchy.shift">
          <label>Timing:</label>
          <span class="value">
            {{ userHierarchy.shift.start_time }} - {{ userHierarchy.shift.end_time }}
          </span>
        </div>
        <div class="info-item" v-if="userHierarchy.is_shift_active">
          <label>Time Remaining:</label>
          <span class="value time-remaining">
            {{ userHierarchy.remaining_minutes }} minutes
          </span>
        </div>
        <div class="info-item">
          <label>Department:</label>
          <span class="value">
            {{ userHierarchy.department?.department_name || 'Not Assigned' }}
          </span>
        </div>
        <div class="info-item">
          <label>Team:</label>
          <span class="value">
            {{ userHierarchy.team?.team_name || 'Not Assigned' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Hierarchy Tree -->
    <div class="hierarchy-tree">
      <h3>Organization Hierarchy</h3>
      <div v-if="hierarchyTree.length === 0" class="empty-state">
        <p>No hierarchy data available</p>
      </div>
      <div v-else class="tree-container">
        <div 
          v-for="shift in hierarchyTree" 
          :key="shift.name" 
          class="shift-node"
        >
          <div class="node-header shift-header">
            <ClockIcon class="icon" />
            <div class="node-info">
              <h4>{{ shift.shift_name }}</h4>
              <span class="timing">{{ shift.start_time }} - {{ shift.end_time }}</span>
            </div>
            <Badge variant="outline">{{ shift.departments.length }} departments</Badge>
          </div>

          <div class="departments">
            <div 
              v-for="dept in shift.departments" 
              :key="dept.name" 
              class="department-node"
            >
              <div class="node-header dept-header">
                <BuildingIcon class="icon" />
                <div class="node-info">
                  <h5>{{ dept.department_name }}</h5>
                  <span class="dept-id">ID: {{ dept.name }}</span>
                  <span v-if="dept.department_head" class="head">
                    Head: {{ dept.department_head }}
                  </span>
                </div>
                <Badge variant="outline">{{ dept.teams.length }} teams</Badge>
              </div>

              <div class="teams">
                <div 
                  v-for="team in dept.teams" 
                  :key="team.name" 
                  class="team-node"
                >
                  <div class="node-header team-header">
                    <UsersIcon class="icon" />
                    <div class="node-info">
                      <h6>{{ team.team_name }}</h6>
                      <span class="team-id">ID: {{ team.name }}</span>
                      <span v-if="team.team_leader" class="leader">
                        Leader: {{ team.team_leader }}
                      </span>
                    </div>
                    <Badge>{{ team.agents.length }} agents</Badge>
                  </div>

                  <div v-if="expandedTeams.includes(team.name)" class="agents">
                    <div 
                      v-for="agent in team.agents" 
                      :key="agent.name" 
                      class="agent-item"
                    >
                      <UserIcon class="icon" />
                      <span>{{ agent.full_name }}</span>
                      <span class="email">{{ agent.email }}</span>
                    </div>
                  </div>

                  <Button 
                    variant="ghost" 
                    size="sm"
                    @click="toggleTeam(team.name)"
                    class="toggle-btn"
                  >
                    {{ expandedTeams.includes(team.name) ? 'Hide' : 'Show' }} Agents
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
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
  User as UserIcon 
} from 'lucide-vue-next'

const loading = ref(false)
const userHierarchy = ref(null)
const hierarchyTree = ref([])
const expandedTeams = ref([])

const userHierarchyResource = createResource({
  url: 'crm.api.hierarchy.get_user_hierarchy',
  auto: true,
  onSuccess(data) {
    userHierarchy.value = data
  }
})

const hierarchyTreeResource = createResource({
  url: 'crm.api.hierarchy.get_hierarchy_tree',
  auto: true,
  onSuccess(data) {
    hierarchyTree.value = data
  }
})

function refreshHierarchy() {
  loading.value = true
  Promise.all([
    userHierarchyResource.reload(),
    hierarchyTreeResource.reload()
  ]).finally(() => {
    loading.value = false
  })
}

function toggleTeam(teamName) {
  const index = expandedTeams.value.indexOf(teamName)
  if (index > -1) {
    expandedTeams.value.splice(index, 1)
  } else {
    expandedTeams.value.push(teamName)
  }
}

onMounted(() => {
  refreshHierarchy()
})
</script>

<style scoped>
.hierarchy-dashboard {
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
}

.user-hierarchy-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.user-hierarchy-card h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.hierarchy-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.info-item .value {
  font-size: 1rem;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.time-remaining {
  color: #059669;
  font-weight: 600;
}

.hierarchy-tree {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.hierarchy-tree h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.tree-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.shift-node {
  border: 2px solid #3b82f6;
  border-radius: 0.5rem;
  padding: 1rem;
}

.node-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.node-header .icon {
  width: 1.25rem;
  height: 1.25rem;
}

.node-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.shift-header {
  color: #3b82f6;
}

.shift-header h4 {
  font-size: 1.125rem;
  font-weight: 600;
}

.timing {
  font-size: 0.875rem;
  color: #6b7280;
}

.departments {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-left: 1.5rem;
}

.department-node {
  border: 2px solid #10b981;
  border-radius: 0.5rem;
  padding: 1rem;
}

.dept-header {
  color: #10b981;
}

.dept-header h5 {
  font-size: 1rem;
  font-weight: 600;
}

.dept-id, .team-id {
  font-size: 0.75rem;
  color: #9ca3af;
  font-family: monospace;
}

.head, .leader {
  font-size: 0.875rem;
  color: #6b7280;
}

.teams {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-left: 1.5rem;
}

.team-node {
  border: 2px solid #f59e0b;
  border-radius: 0.5rem;
  padding: 0.75rem;
}

.team-header {
  color: #f59e0b;
}

.team-header h6 {
  font-size: 0.9375rem;
  font-weight: 600;
}

.agents {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0.75rem 0 0.75rem 1.5rem;
}

.agent-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.agent-item .icon {
  width: 1rem;
  height: 1rem;
  color: #6b7280;
}

.agent-item .email {
  color: #6b7280;
  margin-left: auto;
}

.toggle-btn {
  margin-top: 0.5rem;
  font-size: 0.875rem;
}
</style>
