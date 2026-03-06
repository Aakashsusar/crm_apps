// Basic JS file for Tata Tele Settings
frappe.ui.form.on('CRM Tata Tele Settings', {
	refresh: function(frm) {
		if (frm.doc.enabled) {
			frm.set_df_property('api_endpoint', 'reqd', 1);
			frm.set_df_property('api_token', 'reqd', 1);
			frm.set_df_property('account_id', 'reqd', 1);
		}
	}
});
