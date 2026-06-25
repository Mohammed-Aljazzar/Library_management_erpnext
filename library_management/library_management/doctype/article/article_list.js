frappe.listview_settings["Article"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		if (doc.status === "Issued") {
			return [__("Issued"), "orange", "status,=,Issued"];
		}

		return [__("Available"), "green", "status,=,Available"];
	},
};
