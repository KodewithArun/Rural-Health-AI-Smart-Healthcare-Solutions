// awareness_admin.js
document.addEventListener('DOMContentLoaded', function() {
    const isEventCheckbox = document.querySelector('#id_is_event');
    const eventDateField = document.querySelector('#id_event_date').closest('.field-event_date');

    function toggleEventDate() {
        if (isEventCheckbox.checked) {
            eventDateField.style.display = 'block';
            // Reinitialize date shortcuts for the newly visible field
            if (typeof DateTimeShortcuts !== 'undefined') {
                DateTimeShortcuts.init();
            }
        } else {
            eventDateField.style.display = 'none';
            // Clear the date if hiding
            document.querySelector('#id_event_date').value = '';
        }
    }

    if (isEventCheckbox && eventDateField) {
        // Initial check
        toggleEventDate();
        // On change
        isEventCheckbox.addEventListener('change', toggleEventDate);
    }
});