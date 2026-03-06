frappe.pages['lead-history'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Lead History',
		single_column: true
	});

	page.main.html(`
		<div id="lead-history-app" style="padding: 15px;">
			<div class="text-muted" id="loading-msg">Loading lead history...</div>
			<div id="history-content" style="display:none;">

				<!-- Stat cards -->
				<div class="row" id="stat-cards" style="margin-bottom: 20px;"></div>

				<!-- Lead table section -->
				<h5 id="table-title" style="margin-top: 20px;"></h5>
				<div id="leads-table" class="lead-table-container"></div>
			</div>
		</div>

		<style>
			.lead-table { width: 100%; border-collapse: collapse; }
			.lead-table th, .lead-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border-color); }
			.lead-table th { background: var(--bg-light-gray); font-weight: 600; font-size: 12px; text-transform: uppercase; color: var(--text-muted); }
			.lead-table tr:hover { background: var(--bg-light-gray); }
			.lead-link { color: var(--primary); text-decoration: none; font-weight: 500; }
			.lead-link:hover { text-decoration: underline; }
			.dept-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: var(--blue-50); color: var(--blue-600); }
			.status-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
			.status-done { background: var(--green-50); color: var(--green-700); }
			.status-rejected { background: var(--red-50); color: var(--red-600); }
			.status-working { background: var(--yellow-50); color: var(--yellow-700); }
			.action-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
			.action-forward { background: var(--green-50); color: var(--green-700); }
			.action-backward { background: var(--orange-50); color: var(--orange-700); }
			.action-reject { background: var(--red-50); color: var(--red-600); }
			.action-override { background: var(--blue-50); color: var(--blue-600); }
			.action-initial { background: var(--gray-100); color: var(--gray-700); }
			.empty-state { text-align: center; padding: 30px; color: var(--text-muted); }
			.stat-card { background: var(--bg-light-gray); border-radius: 8px; padding: 16px; text-align: center; }
		</style>
	`);

	function load_history(target_user = null) {
		$('#loading-msg').show();
		$('#history-content').hide();

		let api_args = {};
		if (target_user) {
			api_args.user = target_user;
		}

		frappe.call({
			method: 'lead_routing.api.lead_history.get_my_lead_history',
			args: api_args,
			callback: function (r) {
				$('#loading-msg').hide();
				$('#history-content').show();

				if (!r.message) return;

				const data = r.message;
				const leads = data.leads || [];
				const view_type = data.view_type;

				if (view_type === 'global') {
					render_global_view(data, leads);
				} else {
					render_personal_view(data, leads);
				}
			}
		});
	}

	function render_global_view(data, leads) {
		page.set_title('Lead History — All Completed / Rejected');

		// Stat cards
		const done_count = data.done_count || 0;
		const rejected_count = data.rejected_count || 0;
		$('#stat-cards').html(`
			<div class="col-md-3">
				<div class="stat-card">
					<div class="text-muted small">Completed</div>
					<div style="font-size: 24px; font-weight: bold; color: var(--green-600);">${done_count}</div>
				</div>
			</div>
			<div class="col-md-3">
				<div class="stat-card">
					<div class="text-muted small">Rejected</div>
					<div style="font-size: 24px; font-weight: bold; color: var(--red-600);">${rejected_count}</div>
				</div>
			</div>
			<div class="col-md-3">
				<div class="stat-card">
					<div class="text-muted small">Total</div>
					<div style="font-size: 24px; font-weight: bold;">${leads.length}</div>
				</div>
			</div>
		`);

		$('#table-title').text('All Completed / Rejected Leads');

		if (!leads.length) {
			$('#leads-table').html('<div class="empty-state">No completed or rejected leads yet</div>');
			return;
		}

		const rows = leads.map(lead => {
			const statusClass = get_status_class(lead.department_status);
			const actionBadge = lead.last_action ? get_action_badge(lead.last_action) : '—';
			return `<tr>
				<td><a class="lead-link" href="/crm/leads/${lead.name}">${lead.name}</a></td>
				<td>${lead.lead_name || '-'}</td>
				<td><span class="dept-badge">${lead.current_department || '-'}</span></td>
				<td>${actionBadge}</td>
				<td><span class="status-badge ${statusClass}">${lead.department_status || '-'}</span></td>
				<td>${lead.last_handled_by_name || '—'}</td>
				<td>${frappe.datetime.prettyDate(lead.modified)}</td>
			</tr>`;
		}).join('');

		$('#leads-table').html(`<table class="lead-table">
			<thead>
				<tr>
					<th>Lead ID</th>
					<th>Name</th>
					<th>Department</th>
					<th>Last Action</th>
					<th>Status</th>
					<th>Last Handled By</th>
					<th>Last Updated</th>
				</tr>
			</thead>
			<tbody>${rows}</tbody>
		</table>`);
	}

	function render_personal_view(data, leads) {
		const full_name = data.full_name || data.user;
		const is_self = data.user === frappe.session.user;

		page.set_title(is_self ? 'My Lead History' : `Lead History: ${full_name}`);

		// Stat cards
		$('#stat-cards').html(`
			<div class="col-md-3">
				<div class="stat-card">
					<div class="text-muted small">Total Leads Handled</div>
					<div style="font-size: 24px; font-weight: bold; color: var(--primary);">${leads.length}</div>
				</div>
			</div>
		`);

		$('#table-title').text(is_self ? 'Leads I Previously Worked On' : `Leads Handled by ${full_name}`);

		if (!leads.length) {
			$('#leads-table').html('<div class="empty-state">No lead history found</div>');
			return;
		}

		const rows = leads.map(lead => {
			const statusClass = get_status_class(lead.department_status);
			const actionBadge = lead.user_action ? get_action_badge(lead.user_action) : '—';
			return `<tr>
				<td><a class="lead-link" href="/crm/leads/${lead.name}">${lead.name}</a></td>
				<td>${lead.lead_name || '-'}</td>
				<td><span class="dept-badge">${lead.action_department || lead.current_department || '-'}</span></td>
				<td>${actionBadge}</td>
				<td><span class="status-badge ${statusClass}">${lead.department_status || '-'}</span></td>
				<td>${lead.action_at ? frappe.datetime.prettyDate(lead.action_at) : frappe.datetime.prettyDate(lead.modified)}</td>
			</tr>`;
		}).join('');

		$('#leads-table').html(`<table class="lead-table">
			<thead>
				<tr>
					<th>Lead ID</th>
					<th>Name</th>
					<th>Department</th>
					<th>Action Taken</th>
					<th>Current Status</th>
					<th>Acted On</th>
				</tr>
			</thead>
			<tbody>${rows}</tbody>
		</table>`);
	}

	function get_status_class(status) {
		if (!status) return '';
		const s = status.toLowerCase();
		if (s === 'done') return 'status-done';
		if (s === 'rejected') return 'status-rejected';
		if (s === 'working') return 'status-working';
		return '';
	}

	function get_action_badge(action) {
		if (!action) return '—';
		const labels = {
			'Forward': 'Mark Done',
			'Backward': 'Send Back',
			'Reject': 'Reject to Onboarding',
			'Manager Override': 'Transfer to Department',
			'Initial': 'Initial Assignment',
		};
		const classes = {
			'Forward': 'action-forward',
			'Backward': 'action-backward',
			'Reject': 'action-reject',
			'Manager Override': 'action-override',
			'Initial': 'action-initial',
		};
		const label = labels[action] || action;
		const cls = classes[action] || 'action-initial';
		return `<span class="action-badge ${cls}">${label}</span>`;
	}

	// Add user filter for admin/managers
	if (frappe.user.has_role('System Manager') || frappe.user.has_role('Administrator')) {
		let user_field = page.add_field({
			fieldname: 'user',
			label: 'Select user',
			fieldtype: 'Link',
			options: 'User',
			change: function () {
				load_history(user_field.get_value());
			}
		});
	}

	// Initial load
	load_history();
};
