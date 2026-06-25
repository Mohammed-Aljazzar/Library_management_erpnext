frappe.listview_settings["Library Transaction"] = {
	add_fields: ["type", "status", "due_date", "overdue_days"],
	get_indicator(doc) {
		if (doc.type === "Return" || doc.status === "Returned") {
			return [__("Returned"), "green", "status,=,Returned"];
		}

		if (doc.status === "Overdue" || cint(doc.overdue_days) > 0) {
			return [__("Overdue"), "red", "status,=,Overdue"];
		}

		return [__("Open"), "orange", "status,=,Open"];
	},
};
