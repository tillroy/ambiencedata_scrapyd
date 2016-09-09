


        $(document).ready(function () {
        //for modal submition




        //$(':checkbox').checkboxpicker();
        // for disabling del button
        $(':checkbox').checkboxpicker().change(function() {
            if ($(':checkbox').is(":checked") == true){
                $('button[name="del_egg"]').prop('disabled', false);
            }
            else if ($(':checkbox').is(":checked") == false) {
                $('button[name="del_egg"]').prop('disabled', true);
            }
            //var ch =  $(':checkbox').val();
            //alert(ch);
        });
            //$('button[name="del_egg"]').prop('disabled', false);



        // Run this code only when the DOM (all elements) are ready

            $('form[name="file_loader"]').on("submit", function (e) {
            // Find all <form>s with the name "register", and bind a "submit" event handler

            // Find the <input /> element with the name "username"
                var filename = $(this).find('input[name="filename"]');
            if ($.trim(filename.val()) === "") {
                //alert('empty')
                // If its value is empty
                e.preventDefault();    // Stop the form from submitting
                //$("#alert_is_success").slideDown(400);    // Show the Alert
                $("#alert_is_warning").slideDown(400)
            } else {
                filename.val() = '';
                e.preventDefault();    // Not needed, just for demonstration
                $("#alert_is_success").slideUp(400, function () {    // Hide the Alert (if visible)
                    alert("Would be submitting form");    // Not needed, just for demonstration
                    username.val("");    // Not needed, just for demonstration
            });
        }
    });

    $(".alert").find(".close").on("click", function (e) {
        // Find all elements with the "alert" class, get all descendant elements with the class "close", and bind a "click" event handler
        e.stopPropagation();    // Don't allow the click to bubble up the DOM
        e.preventDefault();    // Don't let any default functionality occur (in case it's a link)
        $(this).closest(".alert").slideUp(400);    // Hide this specific Alert
    });
});