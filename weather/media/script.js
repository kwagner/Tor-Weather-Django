// Shows or hides sections based on initial selection of checkboxes and future
// clicks of checkboxes.
function showOrHideSect(check, sect) {
	if ($(check).attr('checked')) {
		$(sect).show();
	} else {
		$(sect).hide();
	}

	$(check).click(function() {
		$(sect).toggle();
	});
}

// Turns the input field in row row gray and makes text disappear on click
// if it initially had "Default value is --def_val--".
function showDefault(row, defVal) {
	var val = $(row + " input[type='text']").val();
	if (val == "Default value is " + defVal) {
		$(row + " input[type='text']").css("color", "rgb(150, 150, 150)");

		$(row + " input[type='text']").click(function() {
			$(row + " input[type='text']").val("");
			$(row + " input[type='text']").css("color", "black");
		});
	}
}

$(document).ready(function() {

	// Shows or hides sections based on the initial selection of checkboxes.
	// By, default (ie, with javascript turned off), all sections will be 
	// shown since they are only ever hidden here. Also, sets the sections
	// to expand/collapse upon click.
	showOrHideSect("input#id_get_node_down", "div#node-down-section");
	showOrHideSect("input#id_get_version", "div#version-section");
	showOrHideSect("input#id_get_band_low", "div#band-low-section");
	showOrHideSect("input#id_get_t_shirt", "div#t-shirt-section");

	// Turns the input field text gray and makes the text disappear on click
	// if it has the "Default Value is ---" when the page loads.
	showDefault("div#node-down-section", 1);
	showDefault("div#band-low-section", 20);

	$("#more-info a").hover(function() {
		$("#more-info span").toggle();
	});
});

