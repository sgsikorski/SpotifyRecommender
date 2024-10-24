$(document).ready(function () {
    $('#search').on('input', function () {
        var searchTerm = $(this).val();
        $.ajax({
            url: '/filter',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ term: searchTerm }),
            success: function (data) {
                var dropdown = $('#items');
                dropdown.empty();
                dropdown.append('<option value="">--Select an item--</option>');
                data.forEach(function (item) {
                    dropdown.append('<option value="' + item['id'] + '">' + item['name'] + ' (' + item['artists'][0]['name'] + ')</option>');
                });
            }
        });
    });
});