document.addEventListener('DOMContentLoaded', function() {
    const gastosRecurrentesModal = document.getElementById('gastosRecurrentesModal');
    const checklistItems = gastosRecurrentesModal.querySelectorAll('.list-group-item');

    // Función para marcar/desmarcar un gasto recurrente
    function toggleGastoRecurrente(item, checked) {
        const gastoId = item.dataset.gastoId;
        const checkbox = item.querySelector('.gasto-checkbox');

        // Enviar solicitud AJAX para marcar/desmarcar
        fetch(`/config/gastos-recurrentes/marcar/${gastoId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `pagado=${checked}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar la apariencia del elemento
                if (checked) {
                    item.classList.add('list-group-item-success');
                    checkbox.checked = true;
                } else {
                    item.classList.remove('list-group-item-success');
                    checkbox.checked = false;
                }
            } else {
                // Manejar errores
                console.error('Error:', data.message);
                // Revertir el estado del checkbox si hay un error
                checkbox.checked = !checked;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Revertir el estado del checkbox si hay un error de red
            checkbox.checked = !checked;
        });
    }

    // Evento de clic en los elementos de la lista
    checklistItems.forEach(item => {
        const checkbox = item.querySelector('.gasto-checkbox');
        console.log(checkbox)
        // Manejar clic en el elemento de la lista
        item.addEventListener('click', function(event) {
            // Evitar que el evento se dispare si se hizo clic directamente en el checkbox
            if (event.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }
            toggleGastoRecurrente(item, checkbox.checked);
        });

        // Manejar cambios en el checkbox
        checkbox.addEventListener('change', function() {
            toggleGastoRecurrente(item, this.checked);
        });
    });
});