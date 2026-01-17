document.addEventListener('DOMContentLoaded', function() {
    const gastosRecurrentesModal = document.getElementById('gastosRecurrentesModal');
    const checklistItems = gastosRecurrentesModal.querySelectorAll('.list-group-item');

    checklistItems.forEach(item => {
        item.addEventListener('click', function() {
            // Toggle visual selection
            this.classList.toggle('active');
            
            // Optional: Implementar lógica de marcado/desmarcado
            const checkbox = this.querySelector('.form-check-input');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
            }
        });
    });

    // Función para marcar todos los gastos como pagados
    const marcarTodosPagadosBtn = document.getElementById('marcarTodosPagados');
    if (marcarTodosPagadosBtn) {
        marcarTodosPagadosBtn.addEventListener('click', function() {
            checklistItems.forEach(item => {
                item.classList.add('list-group-item-success');
                const checkbox = item.querySelector('.form-check-input');
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
        });
    }
});