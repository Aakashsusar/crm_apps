<template>
  <SettingsPage
    doctype="CRM Tata Tele Settings"
    :title="__('Tata Teleservices settings')"
    :successMessage="__('Tata Teleservices settings updated')"
    class="p-8"
    :back="() => $emit('updateStep', 'telephony-settings')"
  />
</template>
<script setup>
import SettingsPage from '@/components/Settings/SettingsPage.vue'

defineEmits(['updateStep'])
</script>
