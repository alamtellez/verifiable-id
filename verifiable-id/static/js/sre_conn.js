$(document).ready(function() {
	// window.location.hash = "#work";

	$('#new_conn').on('submit', function(event) {
		
		$.ajax({
			data : {
				curp : $('#curp').val(),
			},
			type : 'POST',
			url : '/new_conn'
		})
		.done(function(data) {

			if (data.error) {

			}
			else {
				$('.success').text(data.details).show();
			}

		});
		event.preventDefault();

	});

});