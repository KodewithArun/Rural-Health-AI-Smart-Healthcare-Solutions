/**
 * Modern Modal Alert System
 * Replaces browser's native alert(), confirm(), and custom notifications
 * with beautiful, accessible modals
 * 
 * USAGE EXAMPLES:
 * 
 * 1. Simple Alert:
 *    modalAlert.alert({
 *        title: 'Success',
 *        message: 'Your action was completed successfully!',
 *        icon: 'checkbox-circle',
 *        iconColor: 'green'
 *    });
 * 
 * 2. Confirmation Dialog:
 *    const confirmed = await modalAlert.confirm({
 *        title: 'Delete Item?',
 *        message: 'Are you sure you want to delete this item?',
 *        confirmText: 'Delete',
 *        cancelText: 'Cancel'
 *    });
 *    if (confirmed) { // user clicked confirm }
 * 
 * 3. Emergency Alert:
 *    const confirmed = await modalAlert.emergencyAlert({
 *        title: '🚨 Emergency Alert',
 *        message: 'This will notify emergency services.',
 *        confirmText: 'Confirm Emergency'
 *    });
 * 
 * 4. Success Notification:
 *    modalAlert.success({
 *        title: 'Success!',
 *        message: 'Your changes have been saved.',
 *        autoClose: true,
 *        duration: 3000
 *    });
 * 
 * 5. Error Notification:
 *    modalAlert.error({
 *        title: 'Error',
 *        message: 'Something went wrong. Please try again.'
 *    });
 * 
 * 6. Loading Modal:
 *    const loader = modalAlert.loading('Processing your request...');
 *    // ... do async work ...
 *    loader.close();
 * 
 * AVAILABLE ICONS:
 * - information, checkbox-circle, error-warning, alarm-warning
 * - question, delete-bin, links, robot, heart-pulse
 * - Any Remix Icon name (ri-icon-name)
 * 
 * ICON COLORS:
 * - blue, green, red, yellow, purple
 */

class ModalAlert {
    constructor() {
        this.modalContainer = null;
        this.init();
    }

    init() {
        // Create modal container if it doesn't exist
        if (!document.getElementById('modal-alert-container')) {
            this.createModalContainer();
        }
    }

    createModalContainer() {
        const container = document.createElement('div');
        container.id = 'modal-alert-container';
        container.className = 'fixed inset-0 z-[9999] hidden';
        document.body.appendChild(container);
        this.modalContainer = container;
    }

    /**
     * Show a simple alert modal
     */
    alert(options) {
        const {
            title = 'Notification',
            message = '',
            icon = 'information',
            iconColor = 'blue',
            confirmText = 'OK',
            onConfirm = () => {}
        } = options;

        return new Promise((resolve) => {
            const modal = this.createModal({
                title,
                message,
                icon,
                iconColor,
                buttons: [
                    {
                        text: confirmText,
                        style: 'primary',
                        onClick: () => {
                            onConfirm();
                            this.closeModal();
                            resolve(true);
                        }
                    }
                ]
            });

            this.showModal(modal);
        });
    }

    /**
     * Show a confirmation modal
     */
    confirm(options) {
        const {
            title = 'Confirm Action',
            message = '',
            icon = 'question',
            iconColor = 'yellow',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            onConfirm = () => {},
            onCancel = () => {}
        } = options;

        return new Promise((resolve) => {
            const modal = this.createModal({
                title,
                message,
                icon,
                iconColor,
                buttons: [
                    {
                        text: cancelText,
                        style: 'secondary',
                        onClick: () => {
                            onCancel();
                            this.closeModal();
                            resolve(false);
                        }
                    },
                    {
                        text: confirmText,
                        style: 'primary',
                        onClick: () => {
                            onConfirm();
                            this.closeModal();
                            resolve(true);
                        }
                    }
                ]
            });

            this.showModal(modal);
        });
    }

    /**
     * Show emergency alert modal
     */
    emergencyAlert(options) {
        const {
            title = '🚨 Emergency Alert',
            message = '',
            confirmText = 'Confirm Emergency',
            cancelText = 'Cancel',
            onConfirm = () => {},
            onCancel = () => {}
        } = options;

        return new Promise((resolve) => {
            const modal = this.createModal({
                title,
                message,
                icon: 'alarm-warning',
                iconColor: 'red',
                buttons: [
                    {
                        text: cancelText,
                        style: 'secondary',
                        onClick: () => {
                            onCancel();
                            this.closeModal();
                            resolve(false);
                        }
                    },
                    {
                        text: confirmText,
                        style: 'danger',
                        onClick: () => {
                            onConfirm();
                            this.closeModal();
                            resolve(true);
                        }
                    }
                ]
            });

            this.showModal(modal);
        });
    }

    /**
     * Show success notification
     */
    success(options) {
        const {
            title = 'Success!',
            message = '',
            confirmText = 'OK',
            autoClose = false,
            duration = 3000,
            onConfirm = () => {}
        } = options;

        return this.alert({
            title,
            message,
            icon: 'checkbox-circle',
            iconColor: 'green',
            confirmText,
            onConfirm
        }).then(() => {
            if (autoClose) {
                setTimeout(() => this.closeModal(), duration);
            }
        });
    }

    /**
     * Show error notification
     */
    error(options) {
        const {
            title = 'Error',
            message = '',
            confirmText = 'OK',
            onConfirm = () => {}
        } = options;

        return this.alert({
            title,
            message,
            icon: 'error-warning',
            iconColor: 'red',
            confirmText,
            onConfirm
        });
    }

    /**
     * Show loading modal
     */
    loading(message = 'Please wait...') {
        const modal = document.createElement('div');
        modal.className = 'modal-backdrop';
        modal.innerHTML = `
            <div class="modal-content loading-modal animate-fadeIn">
                <div class="flex flex-col items-center justify-center p-8">
                    <div class="relative">
                        <div class="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                    </div>
                    <p class="mt-6 text-lg font-medium text-gray-700">${message}</p>
                </div>
            </div>
        `;

        this.showModal(modal);
        return {
            close: () => this.closeModal()
        };
    }

    /**
     * Create modal element
     */
    createModal({ title, message, icon, iconColor, buttons }) {
        const iconColors = {
            blue: 'bg-blue-100 text-blue-600',
            green: 'bg-green-100 text-green-600',
            red: 'bg-red-100 text-red-600',
            yellow: 'bg-yellow-100 text-yellow-600',
            purple: 'bg-purple-100 text-purple-600'
        };

        const buttonStyles = {
            primary: 'bg-blue-600 hover:bg-blue-700 text-white',
            secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
            danger: 'bg-red-600 hover:bg-red-700 text-white',
            success: 'bg-green-600 hover:bg-green-700 text-white'
        };

        const modal = document.createElement('div');
        modal.className = 'modal-backdrop';
        modal.innerHTML = `
            <div class="modal-content animate-fadeIn">
                <div class="flex flex-col items-center p-6">
                    <!-- Icon -->
                    <div class="w-16 h-16 ${iconColors[iconColor] || iconColors.blue} rounded-full flex items-center justify-center mb-4">
                        <i class="ri-${icon}-line text-3xl"></i>
                    </div>
                    
                    <!-- Title -->
                    <h3 class="text-2xl font-bold text-gray-900 mb-3 text-center">${title}</h3>
                    
                    <!-- Message -->
                    <div class="text-gray-600 text-center mb-6 max-w-md leading-relaxed">
                        ${message}
                    </div>
                    
                    <!-- Buttons -->
                    <div class="flex gap-3 w-full max-w-sm">
                        ${buttons.map(btn => `
                            <button 
                                class="modal-btn flex-1 px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 ${buttonStyles[btn.style] || buttonStyles.primary}"
                                data-action="${btn.text}">
                                ${btn.text}
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        // Attach button event listeners
        buttons.forEach((btn, index) => {
            const btnElement = modal.querySelectorAll('.modal-btn')[index];
            btnElement.addEventListener('click', btn.onClick);
        });

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal();
            }
        });

        return modal;
    }

    /**
     * Show modal
     */
    showModal(modal) {
        this.modalContainer.innerHTML = '';
        this.modalContainer.appendChild(modal);
        this.modalContainer.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Close modal
     */
    closeModal() {
        if (this.modalContainer) {
            this.modalContainer.classList.add('hidden');
            this.modalContainer.innerHTML = '';
            document.body.style.overflow = '';
        }
    }
}

// Create global instance
window.modalAlert = new ModalAlert();

// Add CSS styles
const style = document.createElement('style');
style.textContent = `
    .modal-backdrop {
        position: fixed;
        inset: 0;
        background-color: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        animation: fadeIn 0.2s ease-out;
    }

    .modal-content {
        background: white;
        border-radius: 1rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        max-width: 500px;
        width: 100%;
        transform: scale(0.9);
        animation: scaleIn 0.3s ease-out forwards;
    }

    .loading-modal {
        max-width: 300px;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    @keyframes scaleIn {
        from {
            transform: scale(0.9);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }

    .animate-fadeIn {
        animation: fadeIn 0.2s ease-out;
    }

    /* Pulse animation for emergency alerts */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
`;
document.head.appendChild(style);
