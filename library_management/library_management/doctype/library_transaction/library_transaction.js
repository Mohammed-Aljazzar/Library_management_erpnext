// Copyright (c) 2026, Faris Ansari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Library Transaction", {
	setup(frm) {
		frm.set_query("article", () => {
			if (frm.doc.type === "Return") {
				return { filters: { status: "Issued" } };
			}

			return { filters: { status: "Available" } };
		});
	},

	refresh(frm) {
		if (frm.is_new() && !frm.doc.date) {
			frm.set_value("date", frappe.datetime.get_today());
		}

		frm.dashboard.clear_headline();
		if (frm.doc.status === "Overdue") {
			frm.dashboard.set_headline_alert(
				__("Overdue by {0} day(s)", [frm.doc.overdue_days || 0]),
				"red"
			);
		} else if (frm.doc.status === "Returned") {
			frm.dashboard.set_headline(__("Returned"));
		} else if (frm.doc.type === "Issue") {
			frm.dashboard.set_headline(__("Open until {0}", [frm.doc.due_date || ""]));
		}
	},

	type(frm) {
		frm.set_value("article", null);
	},

	article(frm) {
		if (frm.doc.type === "Return" && frm.doc.article && !frm.doc.library_member) {
			frappe.call({
				method: "library_management.library_management.doctype.library_transaction.library_transaction.get_article_current_issue",
				args: {
					article: frm.doc.article,
				},
				callback(r) {
					if (r.message?.library_member) {
						frm.set_value("library_member", r.message.library_member);
					}
				},
			});
		}
	},
});
