<template>
  <div class="h-full w-full">
    <div
      v-if="item.type == 'number_chart'"
      class="flex h-full w-full rounded shadow overflow-hidden"
      :class="isClickable(item) ? 'cursor-pointer hover:shadow-md transition-shadow' : 'cursor-pointer'"
      @click="navigateToPage(item)"
    >
      <Tooltip :text="__(item.data.tooltip)">
        <NumberChart
          class="!items-start"
          v-if="item.data"
          :key="index"
          :config="item.data"
        />
      </Tooltip>
    </div>
    <div
      v-else-if="item.type == 'spacer'"
      class="rounded bg-surface-white h-full overflow-hidden text-ink-gray-5 flex items-center justify-center"
      :class="editing ? 'border border-dashed border-outline-gray-2' : ''"
    >
      {{ editing ? __('Spacer') : '' }}
    </div>
    <div
      v-else-if="item.type == 'axis_chart'"
      class="h-full w-full rounded-md bg-surface-white shadow"
    >
      <AxisChart v-if="item.data" :config="item.data" />
    </div>
    <div
      v-else-if="item.type == 'donut_chart'"
      class="h-full w-full rounded-md bg-surface-white shadow overflow-hidden"
    >
      <DonutChart v-if="item.data" :config="item.data" />
    </div>
  </div>
</template>
<script setup>
import { AxisChart, DonutChart, NumberChart, Tooltip } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { inject } from 'vue'

const router = useRouter()
const filters = inject('filters', {})

const props = defineProps({
  index: {
    type: Number,
    required: true,
  },
  item: {
    type: Object,
    required: true,
  },
  editing: {
    type: Boolean,
    default: false,
  },
})

function isClickable(item) {
  if (item.type !== 'number_chart') return false
  const name = (item.name || item.data?.title || '').toLowerCase()
  return ['lead', 'deal', 'contact', 'won', 'lost', 'open'].some(k => name.includes(k))
}

function navigateToPage(item) {
  const name = (item.name || item.data?.title || '').toLowerCase()
  const query = {}
  
  // Pass user filter from dashboard context
  if (filters?.user) {
    query.user = filters.user
  }
  
  // Pass date range filters from dashboard context
  if (filters?.fromDate) {
    query.from_date = filters.fromDate
  }
  if (filters?.toDate) {
    query.to_date = filters.toDate
  }
  
  if (name.includes('lead')) {
    router.push({ name: 'Leads', query })
  } else if (name.includes('won') || name.includes('lost') || name.includes('open')) {
    // Deal status variants
    if (name.includes('won')) query.status_type = 'Won'
    else if (name.includes('lost')) query.status_type = 'Lost'
    else if (name.includes('open')) query.status_type = 'Open'
    router.push({ name: 'Deals', query })
  } else if (name.includes('deal')) {
    router.push({ name: 'Deals', query })
  } else if (name.includes('contact')) {
    router.push({ name: 'Contacts', query })
  }
}
</script>

