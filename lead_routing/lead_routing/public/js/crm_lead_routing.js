// Copyright (c) 2026, IP CRM and contributors
// Department-Based Lead Routing — UI Buttons for CRM Lead

frappe.ui.form.on("CRM Lead", {
    refresh(frm) {
        // Inject custom styles for toast notifications
        // Frappe CRM (Vue) uses different classes than classic Frappe desk-alert
        if (!window._crm_lead_routing_style_injected) {
            let style = document.createElement("style");
            style.innerHTML = `
                /* ── Frappe CRM (Vue) toast: targets Toastify or the CRM notification component ── */
                
                /* Frappe v15+ / CRM uses .alert-container > .alert or Toastify */
                .alert-container .alert,
                .toastify,
                .notifications-list .notification-item,
                /* Classic frappe desk fallback */
                .desk-alert {
                    border-radius: 8px !important;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.25) !important;
                    z-index: 99999 !important;
                    padding: 12px 16px !important;
                    display: flex !important;
                    align-items: center !important;
                    border-left-width: 5px !important;
                    border-left-style: solid !important;
                    font-weight: 600 !important;
                    font-size: 14px !important;
                    min-width: 260px !important;
                    opacity: 1 !important;
                }

                /* ── GREEN (success / mark done / move forward) ── */
                .alert-container .alert.alert-success,
                .toastify.on.success,
                .desk-alert.green,
                /* Frappe CRM indicator-based */
                [data-indicator="green"],
                .indicator-pill.green {
                    background-color: #dcfce7 !important;
                    color: #166534 !important;
                    border-left-color: #16a34a !important;
                }
                .desk-alert.green *, .alert-container .alert.alert-success * { color: #166534 !important; fill: #166534 !important; }

                /* ── RED (reject / error) ── */
                .alert-container .alert.alert-danger,
                .toastify.on.danger,
                .desk-alert.red,
                [data-indicator="red"],
                .indicator-pill.red {
                    background-color: #fee2e2 !important;
                    color: #991b1b !important;
                    border-left-color: #dc2626 !important;
                }
                .desk-alert.red *, .alert-container .alert.alert-danger * { color: #991b1b !important; fill: #991b1b !important; }

                /* ── BLUE (transfer) ── */
                .alert-container .alert.alert-info,
                .toastify.on.info,
                .desk-alert.blue,
                [data-indicator="blue"],
                .indicator-pill.blue {
                    background-color: #dbeafe !important;
                    color: #1e40af !important;
                    border-left-color: #2563eb !important;
                }
                .desk-alert.blue *, .alert-container .alert.alert-info * { color: #1e40af !important; fill: #1e40af !important; }

                /* ── ORANGE (send back / warning) ── */
                .alert-container .alert.alert-warning,
                .toastify.on.warning,
                .desk-alert.orange,
                .desk-alert.yellow,
                [data-indicator="orange"],
                [data-indicator="yellow"],
                .indicator-pill.orange,
                .indicator-pill.yellow {
                    background-color: #ffedd5 !important;
                    color: #c2410c !important;
                    border-left-color: #ea580c !important;
                }
                .desk-alert.orange *, .desk-alert.yellow *, .alert-container .alert.alert-warning * { color: #c2410c !important; fill: #c2410c !important; }

                /* ── Text inside toasts ── */
                .alert-container .alert .alert-message,
                .toastify .alert-message,
                .desk-alert .alert-message {
                    font-weight: 600 !important;
                    font-size: 14px !important;
                }

                /* ── Dark Mode ── */
                html[data-theme="dark"] .alert-container .alert.alert-success,
                html[data-theme="dark"] .desk-alert.green {
                    background-color: #052e16 !important; color: #4ade80 !important; border-left-color: #22c55e !important;
                }
                html[data-theme="dark"] .alert-container .alert.alert-success *, html[data-theme="dark"] .desk-alert.green * {
                    color: #4ade80 !important; fill: #4ade80 !important;
                }

                html[data-theme="dark"] .alert-container .alert.alert-danger,
                html[data-theme="dark"] .desk-alert.red {
                    background-color: #450a0a !important; color: #f87171 !important; border-left-color: #ef4444 !important;
                }
                html[data-theme="dark"] .alert-container .alert.alert-danger *, html[data-theme="dark"] .desk-alert.red * {
                    color: #f87171 !important; fill: #f87171 !important;
                }

                html[data-theme="dark"] .alert-container .alert.alert-info,
                html[data-theme="dark"] .desk-alert.blue {
                    background-color: #172554 !important; color: #60a5fa !important; border-left-color: #3b82f6 !important;
                }
                html[data-theme="dark"] .alert-container .alert.alert-info *, html[data-theme="dark"] .desk-alert.blue * {
                    color: #60a5fa !important; fill: #60a5fa !important;
                }

                html[data-theme="dark"] .alert-container .alert.alert-warning,
                html[data-theme="dark"] .desk-alert.orange,
                html[data-theme="dark"] .desk-alert.yellow {
                    background-color: #431407 !important; color: #fb923c !important; border-left-color: #f97316 !important;
                }
                html[data-theme="dark"] .alert-container .alert.alert-warning *, html[data-theme="dark"] .desk-alert.orange *, html[data-theme="dark"] .desk-alert.yellow * {
                    color: #fb923c !important; fill: #fb923c !important;
                }
            `;
            document.head.appendChild(style);
            window._crm_lead_routing_style_injected = true;
        }

        // Only show routing buttons if the lead has a department assigned
        if (!frm.doc.current_department) return;

        // Remove any previously added routing buttons to avoid duplicates
        frm.remove_custom_button(__("Mark Done"), __("Routing"));
        frm.remove_custom_button(__("Reject to Onboarding"), __("Routing"));
        frm.remove_custom_button(__("Send Back"), __("Routing"));
        frm.remove_custom_button(__("Manager Override"), __("Routing"));
        frm.remove_custom_button(__("Transfer to Department"), __("Routing"));

        // ──── Current Department Info Banner ────
        let dept_html = `<div style="
      padding: 8px 14px;
      margin-bottom: 10px;
      border-radius: 8px;
      background: var(--subtle-accent);
      border-left: 4px solid var(--primary-color);
      font-size: 13px;
    ">
      <strong>🏢 Department:</strong> ${frm.doc.current_department}
      &nbsp;&nbsp;|&nbsp;&nbsp;
      <strong>🕐 Shift:</strong> ${frm.doc.current_shift || "Not Set"}
      &nbsp;&nbsp;|&nbsp;&nbsp;
      <strong>📋 Status:</strong> ${frm.doc.department_status || "—"}
    </div>`;

        frm.set_intro(dept_html, "blue");

        // Don't show action buttons if lifecycle is already complete
        if (frm.doc.department_status === "Done") {
            frappe.db.get_value("Department Pipeline Stage", frm.doc.current_department, "is_terminal")
                .then((r) => {
                    if (r.message && r.message.is_terminal) {
                        frm.set_intro(dept_html.replace("📋 Status:", "✅ Status:"), "green");
                    }
                });
            return;
        }

        // ──── 1. MARK DONE Button ────
        frm.add_custom_button(
            __("Mark Done"),
            function () {
                frappe.confirm(
                    __("Mark this department's work as <b>Done</b> and move lead to the next department?"),
                    function () {
                        frappe.call({
                            method: "lead_routing.api.lead_transfer.mark_department_done",
                            args: { lead_name: frm.doc.name },
                            freeze: true,
                            freeze_message: __("Transferring lead..."),
                            callback: function (r) {
                                if (r.message) {
                                    if (r.message.status === "completed") {
                                        frappe.show_alert({
                                            message: __("🎉 Lead lifecycle completed!"),
                                            indicator: "green",
                                        }, 5);
                                    } else {
                                        frappe.show_alert({
                                            message: __("✅ Lead moved to {0}", [r.message.to]),
                                            indicator: "green",
                                        }, 5);
                                    }
                                    frm.reload_doc();
                                }
                            },
                        });
                    }
                );
            },
            __("Routing")
        );



        // ──── 3. REJECT TO ONBOARDING Button ────
        frm.add_custom_button(
            __("Reject to Onboarding"),
            function () {
                frappe.confirm(
                    __("Reject this lead back to <b>Seller Onboarding</b>?<br>This is typically used when the lead needs to restart the process."),
                    function () {
                        frappe.call({
                            method: "lead_routing.api.lead_transfer.reject_to_onboarding",
                            args: { lead_name: frm.doc.name },
                            freeze: true,
                            freeze_message: __("Rejecting lead..."),
                            callback: function (r) {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __("🔄 Lead rejected back to {0}", [r.message.to]),
                                        indicator: "red",
                                    }, 5);
                                    frm.reload_doc();
                                }
                            },
                        });
                    }
                );
            },
            __("Routing")
        );

        // ──── 4. TRANSFER TO DEPARTMENT Button ────
        frm.add_custom_button(
            __("Transfer to Department"),
            function () {
                frappe.call({
                    method: "lead_routing.api.lead_transfer.get_transfer_targets",
                    args: { current_department: frm.doc.current_department },
                    callback: function (r) {
                        if (!r.message || r.message.length === 0) {
                            frappe.msgprint(__("No other departments available."));
                            return;
                        }

                        let options = r.message.map((d) => d.name);

                        let d = new frappe.ui.Dialog({
                            title: __("Transfer Lead to Department"),
                            fields: [
                                {
                                    fieldname: "target_stage",
                                    fieldtype: "Select",
                                    label: __("Transfer To"),
                                    options: options.join("\n"),
                                    reqd: 1,
                                },
                                {
                                    fieldname: "notes",
                                    fieldtype: "Small Text",
                                    label: __("Reason / Notes"),
                                },
                            ],
                            primary_action_label: __("Transfer"),
                            primary_action: function (values) {
                                frappe.call({
                                    method: "lead_routing.api.lead_transfer.manager_override_transfer",
                                    args: {
                                        lead_name: frm.doc.name,
                                        target_stage: values.target_stage,
                                        notes: values.notes || "",
                                    },
                                    freeze: true,
                                    freeze_message: __("Transferring lead..."),
                                    callback: function (r) {
                                        if (r.message) {
                                            frappe.show_alert({
                                                message: __("⚡ Lead transferred to {0}", [r.message.to]),
                                                indicator: "blue",
                                            }, 5);
                                            d.hide();
                                            frm.reload_doc();
                                        }
                                    },
                                });
                            },
                        });
                        d.show();
                    },
                });
            },
            __("Routing")
        );
    },
});