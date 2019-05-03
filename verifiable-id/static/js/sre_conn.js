$(document).ready(function() {
	// window.location.hash = "#work";

	$('#new_conn').on('submit', function(event) {
		
		$.ajax({
			data : {
				curp : $('#curp').val(),
			},
			type : 'POST',
			url : '/new_conn',
			success: function (response) {
				console.log(response);
			},
			error: function (error) {
				console.log(error);
			}
		});
		event.preventDefault();

	});

});