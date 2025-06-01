# 🚀 EzTransfert: Simple Local File Transfer Server

EzTransfert is a lightweight, self-contained HTTP server written in Python, designed for easy file transfers between your phone and your computer on a local network (or more generally between two computers on the same local network). It allows you to both **upload files from your phone to your computer** and **download files from a shared directory** on your computer to your phone.

---

## ✨ Features

* **⚡️ Quick Setup:** Run a single Python script to get started.
* **⬆️ File Uploads:** Upload multiple files simultaneously from your phone's browser to a designated folder on your computer.
* **⬇️ File Downloads:** Share files and folders from a specific directory on your computer, accessible and browsable from your phone's browser.
* **🌐 Local Network Access:** Accessible via your computer's local IP address, making it perfect for home or office use without external dependencies.
* **💻 Cross-Platform:** Works on any operating system with Python 3 installed.

---

## ⚠️ Important Security Note

This server is built for **local, temporary use only**. It has **no authentication or security measures** in place. **Do NOT expose this server to the public internet.** Anyone on your local network will be able to access the upload and shared directories.

---

## 🛠️ How to Use

### Prerequisites

* **Python 3** installed on your computer.

### 1. Setup

1.  **Save the Code:** Save the provided Python code into a file named `ez_transfert.py` (or any other `.py` extension).
2.  **Create Directories:**
    * In the **same directory** as your `ez_transfert.py` script, create a new folder named `share`. This is where you'll put files you want to make accessible for download.
    * The script will automatically create a `transferts` folder in your user's home directory (e.g., `C:\Users\YourUser\transferts` on Windows, `/home/youruser/transferts` on Linux) where uploaded files will be saved.

    Your directory structure should look something like this:

    ```
    your_project_folder/
    ├── ez_transfert.py
    └── share/
        ├── your_photo.jpg
        └── your_document.pdf
    ```

### 2. Run the Server

1.  Open your terminal or command prompt.
2.  Navigate to the directory where you saved `ez_transfert.py`:

    ```bash
    cd path/to/your_project_folder
    ```

3.  Run the script:

    ```bash
    python ez_transfert.py
    ```

    You'll see output similar to this:

    ```
    Les fichiers uploadés seront sauvegardés dans : /home/youruser/transferts
    Les fichiers à partager seront servis depuis : /path/to/your_project_folder/share
    Serveur HTTP démarré sur [http://192.168.1.](http://192.168.1.)XX:8000
    Accédez à [http://192.168.1.](http://192.168.1.)XX:8000/upload depuis votre téléphone pour uploader des fichiers.
    Accédez à [http://192.168.1.](http://192.168.1.)XX:8000/get depuis votre téléphone pour accéder aux fichiers partagés.
    Toutes les autres requêtes GET seront redirigées vers /upload.
    Appuyez sur Ctrl+C pour arrêter le serveur.
    ```

    Take note of the **IP address** (e.g., `192.168.1.XX`) and the **port** (e.g., `8000`).

### 3. Access from Your Phone

1.  **Connect to Same Network:** Ensure your phone is connected to the **same Wi-Fi network** as your computer.
2.  **Open Browser:** On your phone's web browser, enter one of the following URLs:

    * **For Uploads:**
        `http://YOUR_COMPUTER_IP:8000/upload`
        (e.g., `http://192.168.1.XX:8000/upload`)
        Here, you can select one or multiple files and upload them to your computer.

    * **For Downloads/Shared Files:**
        `http://YOUR_COMPUTER_IP:8000/get`
        (e.g., `http://192.168.1.XX:8000/get`)
        This will display a browsable list of files and folders within your `share` directory. Click on files to download them, or click on folders to navigate into them.

### 4. Stop the Server

* In your terminal, press `Ctrl+C` to stop the server.
