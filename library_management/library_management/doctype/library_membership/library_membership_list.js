frappe.listview_settings["Library Membership"] = {
	add_fields: ["from_date", "to_date", "paid", "docstatus"],
	get_indicator(doc) {
		if (doc.docstatus === 0) {
			return [__("Draft"), "grey", "docstatus,=,0"];
		}

		if (!doc.paid) {
			return [__("Unpaid"), "orange", "paid,=,0"];
		}

		if (doc.to_date && frappe.datetime.get_diff(doc.to_date, frappe.datetime.get_today()) < 0) {
			return [__("Expired"), "red", "to_date,<,Today"];
		}

		return [__("Active"), "green", "paid,=,1"];
	},
};
