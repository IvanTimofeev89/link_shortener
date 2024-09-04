function checkFile() {
    const fileInput = document.querySelector('input[type="file"]');
    if (!fileInput.files.length) {
        alert("Файл не приложен. Пожалуйста, выберите файл для загрузки.");
        return false;  // Прерывает отправку формы
    }
    return true;  // Разрешает отправку формы
}