$(document).ready(function() {
	// window.location.hash = "#work";
	event.preventDefault();
	$('#new_conn').on('submit', function(event) {
		
		$.ajax({
			data : {
				conn: $('#conn').val(),
			},
			type : 'POST',
			url : '/accept_new_conn',
		});

		
		window.location.replace("http://localhost:3300/connections");

	});

});