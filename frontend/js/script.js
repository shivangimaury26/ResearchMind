// PDF Upload

const pdfFile = document.getElementById("pdf-file");

if (pdfFile) {

    pdfFile.addEventListener("change", function () {

        const file = this.files[0];

        if (!file) {
            return;
        }

        if (file.type !== "application/pdf") {
            alert("Please select a PDF file.");
            this.value = "";
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            alert("File size must be less than 10 MB.");
            this.value = "";
            return;
        }

        const message = document.createElement("div");

        message.className = "upload-success";

        message.innerHTML = `
            <div class="success-icon">✓</div>
            <h3>PDF Selected Successfully!</h3>
            <p>Your research paper is ready for analysis.</p>
            <button class="success-close">Continue</button>
        `;

        pdfFile.parentElement.appendChild(message);

        message.querySelector(".success-close").addEventListener("click", function () {

    message.remove();

    const fileInfo = document.createElement("div");

    fileInfo.className = "file-info";

    fileInfo.innerHTML = `
        <div class="file-info-icon">📄</div>

        <div class="file-details">
            <strong>${file.name}</strong>
            <span>${(file.size / (1024 * 1024)).toFixed(2)} MB • PDF</span>
        </div>

        <button class="analyze-btn">
            ✦ Analyze Research Paper
        </button>
    `;
        const analyzeBtn = fileInfo.querySelector(".analyze-btn");

    analyzeBtn.addEventListener("click", function () {
    analyzeBtn.classList.add("loading");
    analyzeBtn.innerHTML = "Analyzing Paper...";

    localStorage.setItem("researchPaperName", file.name);

    setTimeout(function () {
        window.location.href = "dashboard.html";
    }, 1500);
});

    pdfFile.parentElement.appendChild(fileInfo);

});

    });

}
const uploadBox = document.querySelector(".upload-box");

if (uploadBox) {

    uploadBox.addEventListener("dragover", function (event) {
        event.preventDefault();
        uploadBox.classList.add("drag-active");
    });

    uploadBox.addEventListener("dragleave", function () {
        uploadBox.classList.remove("drag-active");
    });

    uploadBox.addEventListener("drop", function (event) {
        event.preventDefault();
        uploadBox.classList.remove("drag-active");

        const file = event.dataTransfer.files[0];

        if (!file) return;

        if (file.type !== "application/pdf") {
            alert("Please drop a PDF file.");
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            alert("File size must be less than 10 MB.");
            return;
        }

        pdfFile.files = event.dataTransfer.files;
        pdfFile.dispatchEvent(new Event("change"));
    });

}