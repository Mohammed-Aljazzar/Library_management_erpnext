// Copyright (c) 2026, Faris Ansari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Article", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		if (frm.doc.status === "Available") {
			frm.add_custom_button(__("Issue Article"), () => {
				frappe.new_doc("Library Transaction", {
					article: frm.doc.name,
					type: "Issue",
					date: frappe.datetime.get_today(),
				});
			}, __("Library"));
		}

		if (frm.doc.status === "Issued") {
			frm.add_custom_button(__("Return Article"), () => {
				frappe.call({
					method: "library_management.library_management.doctype.library_transaction.library_transaction.get_article_current_issue",
					args: {
						article: frm.doc.name,
					},
					callback(r) {
						frappe.new_doc("Library Transaction", {
							article: frm.doc.name,
							library_member: r.message?.library_member,
							type: "Return",
							date: frappe.datetime.get_today(),
						});
					},
				});
			}, __("Library"));
		}
	},
});
