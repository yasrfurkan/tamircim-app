// This script handles the dynamic functionality of the application

document.addEventListener('DOMContentLoaded', function() {
    // Toggle tab content for mechanic appointments page
    const tabButtons = document.querySelectorAll('.tab-button');
    
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons and panes
                document.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('active');
                    btn.classList.remove('border-orange-500');
                    btn.classList.remove('text-orange-600');
                    btn.classList.add('border-transparent');
                    btn.classList.add('text-gray-500');
                });
                
                document.querySelectorAll('.tab-pane').forEach(pane => {
                    pane.classList.add('hidden');
                });
                
                // Add active class to current button and pane
                this.classList.add('active');
                this.classList.remove('border-transparent');
                this.classList.remove('text-gray-500');
                this.classList.add('border-orange-500');
                this.classList.add('text-orange-600');
                
                const tabName = this.getAttribute('data-tab');
                document.getElementById(tabName).classList.remove('hidden');
            });
        });
    }
    
    // City-district selector functionality
    const citySelect = document.getElementById('city');
    const districtSelect = document.getElementById('district');
    
    if (citySelect && districtSelect) {
        citySelect.addEventListener('change', function() {
            const cityId = this.value;
            
            // Clear districts
            districtSelect.innerHTML = '<option value="0">Tüm İlçeler</option>';
            
            if (cityId > 0) {
                // Get districts for selected city
                fetch(`/get_districts/${cityId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data && data.districts && Array.isArray(data.districts)) {
                            data.districts.forEach(district => {
                                const option = document.createElement('option');
                                option.value = district.id;
                                option.textContent = district.name;
                                districtSelect.appendChild(option);
                            });
                        }
                    })
                    .catch(error => console.error('Error fetching districts:', error));
            }
        });
    }
    
    // Confirmation dialogs
    window.confirmAction = function(message) {
        return confirm(message);
    };
    
    // Auto-scroll to bottom of message conversation
    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
});