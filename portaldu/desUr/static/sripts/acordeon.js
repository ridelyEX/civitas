document.addEventListener('DOMContentLoaded', function() {
    const dropdowns = document.querySelectorAll('.simple-dropdown');

    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.simple-toggle');
        const menu = dropdown.querySelector('.simple-menu');

        // Agregar atributos ARIA
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-haspopup', 'true');

        // Click handler
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            toggleDropdown(dropdown);
        });

        // Soporte de teclado
        toggle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleDropdown(dropdown);
            }
            if (e.key === 'Escape') {
                closeDropdown(dropdown);
                toggle.focus();
            }
        });

        // Navegación con teclado dentro del menú
        menu.addEventListener('keydown', function(e) {
            const checkboxes = menu.querySelectorAll('input[type="checkbox"]');
            const currentIndex = Array.from(checkboxes).indexOf(document.activeElement);

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const nextIndex = (currentIndex + 1) % checkboxes.length;
                checkboxes[nextIndex].focus();
            }
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                const prevIndex = currentIndex === 0 ? checkboxes.length - 1 : currentIndex - 1;
                checkboxes[prevIndex].focus();
            }
            if (e.key === 'Escape') {
                closeDropdown(dropdown);
                toggle.focus();
            }
        });
    });

    function toggleDropdown(dropdown) {
        const isOpen = dropdown.classList.contains('open');

        // Cerrar otros dropdowns
        dropdowns.forEach(other => {
            if (other !== dropdown) {
                closeDropdown(other);
            }
        });

        if (isOpen) {
            closeDropdown(dropdown);
        } else {
            openDropdown(dropdown);
        }
    }

    function openDropdown(dropdown) {
        dropdown.classList.add('open');
        dropdown.querySelector('.simple-toggle').setAttribute('aria-expanded', 'true');

        // Focus en el primer checkbox
        const firstCheckbox = dropdown.querySelector('input[type="checkbox"]');
        if (firstCheckbox) {
            firstCheckbox.focus();
        }
    }

    function closeDropdown(dropdown) {
        dropdown.classList.remove('open');
        dropdown.querySelector('.simple-toggle').setAttribute('aria-expanded', 'false');
    }

    // Cerrar al hacer click fuera
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.simple-dropdown')) {
            dropdowns.forEach(dropdown => {
                closeDropdown(dropdown);
            });
        }
    });
});