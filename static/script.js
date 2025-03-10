document.addEventListener("DOMContentLoaded", function () {
    // Auto-hide flash messages
    let flashMessages = document.querySelectorAll(".flash-message");
    flashMessages.forEach((msg) => {
        setTimeout(() => {
            msg.style.transition = "opacity 0.5s";
            msg.style.opacity = "0";
            setTimeout(() => msg.remove(), 500);
        }, 3000);
    });

    // Konfirmasi sebelum menghapus produk dari keranjang
    let removeButtons = document.querySelectorAll(".remove-from-cart");
    removeButtons.forEach((btn) => {
        btn.addEventListener("click", function (event) {
            let confirmDelete = confirm("Apakah Anda yakin ingin menghapus produk ini dari keranjang?");
            if (!confirmDelete) {
                event.preventDefault();
            }
        });
    });

    // Validasi form checkout
    let checkoutForm = document.querySelector("#checkout-form");
    if (checkoutForm) {
        checkoutForm.addEventListener("submit", function (event) {
            let name = document.querySelector("#name").value.trim();
            let address = document.querySelector("#address").value.trim();
            let phone = document.querySelector("#phone").value.trim();

            if (name === "" || address === "" || phone === "") {
                alert("Harap lengkapi semua bidang sebelum melanjutkan checkout.");
                event.preventDefault();
            }
        });
    }
});
