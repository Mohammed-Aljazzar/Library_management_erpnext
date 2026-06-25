// Copyright (c) 2026, Faris Ansari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Library Member", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		frappe.call({
			method: "library_management.library_management.doctype.library_transaction.library_transaction.get_member_summary",
			args: {
				library_member: frm.doc.name,
			},
			callback(r) {
				const summary = r.message || {};
				frm.dashboard.clear_headline();

				if (summary.overdue_count) {
					frm.dashboard.set_headline_alert(
						__("Overdue Articles: {0} | Estimated Fine: {1}", [
							summary.overdue_count,
							format_currency(summary.fine_amount || 0),
						]),
						"orange"
					);
				} else {
					frm.dashboard.set_headline(
						__("Open Articles: {0}", [summary.open_count || 0])
					);
				}
			},
		});

		frm.add_custom_button("New Membership", () => {
			frappe.new_doc("Library Membership", {
				library_member: frm.doc.name,
			});
		}, "Create");

		frm.add_custom_button("Issue Article", () => {
			frappe.new_doc("Library Transaction", {
				library_member: frm.doc.name,
				type: "Issue",
				date: frappe.datetime.get_today(),
			});
		}, "Create");

		frm.add_custom_button("Return Article", () => {
			frappe.new_doc("Library Transaction", {
				library_member: frm.doc.name,
				type: "Return",
				date: frappe.datetime.get_today(),
			});
		}, "Create");

		frm.add_custom_button(__("Open Transactions"), () => {
			frappe.set_route("List", "Library Transaction", {
				library_member: frm.doc.name,
				status: ["in", ["Open", "Overdue"]],
			});
		}, __("View"));
	},
});
