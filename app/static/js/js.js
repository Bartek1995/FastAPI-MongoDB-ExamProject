const close_button = document.querySelector(".btn-close");

if (close_button != null) {
  close_button.addEventListener("click", () => {
    const alert_div = document.querySelector(".alert");
    alert_div.classList.toggle("hide");
  });
}
