document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.sidebar').forEach((sidebar, index) => {
        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'mobile-menu-toggle';
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-controls', `mobile-sidebar-${index}`);
        toggle.innerHTML = '<span></span><span></span><span></span><b>Menu</b>';
        sidebar.id = `mobile-sidebar-${index}`;
        sidebar.prepend(toggle);

        toggle.addEventListener('click', () => {
            const isOpen = sidebar.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', String(isOpen));
        });

        sidebar.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                sidebar.classList.remove('is-open');
                toggle.setAttribute('aria-expanded', 'false');
            });
        });
    });
});
