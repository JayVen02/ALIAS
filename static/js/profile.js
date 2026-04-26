(function () {
    'use strict';

    window.initProfile = function () {
        const tabs = document.querySelectorAll('.profile-tab');
        const userTableBody = document.getElementById('userTableBody');
        const userModal = document.getElementById('userModal');
        const deleteUserModal = document.getElementById('deleteUserModal');
        
        if (!tabs.length) return;

        // ── Tab Switching ────────────────────────────
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const target = tab.dataset.tab;
                document.getElementById('infoTab').classList.toggle('hidden', target !== 'info');
                document.getElementById('settingsTab').classList.toggle('hidden', target !== 'settings');
                
                if (target === 'settings') {
                    loadUsers();
                }
            });
        });

        // ── User Management Logic ────────────────────
        async function loadUsers() {
            try {
                const res = await fetch('/api/users');
                const data = await res.json();
                renderUsers(data.users);
            } catch (err) {
                console.error('Error loading users:', err);
            }
        }

        function renderUsers(users) {
            userTableBody.innerHTML = '';
            users.forEach(user => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${user.username}</td>
                    <td>${user.email || '—'}</td>
                    <td>
                        <button class="icon-btn edit-user" data-id="${user.id}">Edit</button>
                        <button class="icon-btn delete-user danger" data-id="${user.id}" data-name="${user.username}">Delete</button>
                    </td>
                `;
                
                tr.querySelector('.edit-user').addEventListener('click', () => openUserModal(user));
                tr.querySelector('.delete-user').addEventListener('click', () => openDeleteModal(user.id, user.username));
                
                userTableBody.appendChild(tr);
            });
        }

        // ── Modal Handlers ──────────────────────────
        const btnAddUser = document.getElementById('btnAddUser');
        const userModalCancel = document.getElementById('userModalCancel');
        const userModalSave = document.getElementById('userModalSave');
        const deleteUserCancel = document.getElementById('deleteUserCancel');
        const deleteUserConfirm = document.getElementById('deleteUserConfirm');

        btnAddUser.addEventListener('click', () => openUserModal());
        userModalCancel.addEventListener('click', () => userModal.classList.add('hidden'));
        deleteUserCancel.addEventListener('click', () => deleteUserModal.classList.add('hidden'));

        function openUserModal(user = null) {
            const title = document.getElementById('modalTitle');
            const idField = document.getElementById('userIdField');
            const usernameField = document.getElementById('usernameField');
            const emailField = document.getElementById('emailField');
            const passwordField = document.getElementById('passwordField');
            const error = document.getElementById('userModalError');

            error.textContent = '';
            passwordField.value = '';
            
            if (user) {
                title.textContent = 'Edit User Access';
                idField.value = user.id;
                usernameField.value = user.username;
                emailField.value = user.email || '';
            } else {
                title.textContent = 'Add New User';
                idField.value = '';
                usernameField.value = '';
                emailField.value = '';
            }
            
            userModal.classList.remove('hidden');
        }

        userModalSave.addEventListener('click', async () => {
            const id = document.getElementById('userIdField').value;
            const username = document.getElementById('usernameField').value.trim();
            const email = document.getElementById('emailField').value.trim();
            const password = document.getElementById('passwordField').value.trim();
            const error = document.getElementById('userModalError');

            if (!username) {
                error.textContent = 'Username is required.';
                return;
            }

            const method = id ? 'PUT' : 'POST';
            const url = id ? `/api/users/${id}` : '/api/users';
            
            try {
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });
                
                if (res.ok) {
                    userModal.classList.add('hidden');
                    loadUsers();
                } else {
                    const data = await res.json();
                    error.textContent = data.error || 'Operation failed.';
                }
            } catch (err) {
                error.textContent = 'Network error.';
            }
        });

        let deleteId = null;
        function openDeleteModal(id, name) {
            deleteId = id;
            document.getElementById('deleteTargetName').textContent = name;
            deleteUserModal.classList.remove('hidden');
        }

        deleteUserConfirm.addEventListener('click', async () => {
            if (!deleteId) return;
            try {
                const res = await fetch(`/api/users/${deleteId}`, { method: 'DELETE' });
                if (res.ok) {
                    deleteUserModal.classList.add('hidden');
                    loadUsers();
                }
            } catch (err) {
                console.error('Delete failed:', err);
            }
        });
    }
})();
