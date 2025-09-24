frappe.ui.form.on('Timesheet', {
	custom_is_billable(frm) {
		// your code here
        frm.doc.time_logs.forEach(row => {
            frappe.model.set_value(row.doctype, row.name, 'is_billable', frm.doc.custom_is_billable ? 1 : 0);
        });
	}
})