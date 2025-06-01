import http.server
import socketserver
import os
import urllib
import cgi # Module pour gérer les données multipart/form-data
import socket

PORT = 8000  # Vous pouvez changer le port si nécessaire

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transferts")
# Définir le répertoire de partage statique
SHARE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "share")


# Crée les dossiers s'ils n'existent pas
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SHARE_DIR, exist_ok=True) # Crée le dossier 'share' si non existant

print(f"Les fichiers uploadés seront sauvegardés dans : {UPLOAD_DIR}")
print(f"Les fichiers à partager seront servis depuis : {SHARE_DIR}")


class MyHandler(http.server.SimpleHTTPRequestHandler):
    """
    Gestionnaire de requêtes HTTP personnalisé pour l'upload de fichiers.
    Gère les requêtes POST pour l'upload de fichiers et les requêtes GET
    pour afficher le formulaire d'upload.
    """

    def do_POST(self):
        """
        Gère les requêtes POST pour l'upload de fichiers.
        Attend des données de type 'multipart/form-data'.
        """
        content_type = self.headers['Content-Type']

        if content_type.startswith('multipart/form-data'):
            # Utilisation de cgi.FieldStorage pour parser les données multipart.
            # Cela nous permet de gérer facilement les champs de formulaire et les fichiers.
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}
            )

            files_received = [] # Liste pour stocker les noms des fichiers reçus avec succès.
            
            # Parcourir tous les champs du formulaire.
            for field_name in form:
                field_item = form[field_name]
                
                # Vérifie si l'élément est un fichier uploadé.
                # Si 'name="files[]"' est utilisé dans le formulaire HTML, field_item peut être une liste.
                if isinstance(field_item, list):
                    for item in field_item:
                        if item.filename:
                            self._save_uploaded_file(item, files_received)
                elif field_item.filename: # Cas d'un seul fichier pour ce champ.
                    self._save_uploaded_file(field_item, files_received)

            if files_received:
                print(f"Total de {len(files_received)} fichier(s) reçu(s).")
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(f"Fichier(s) reçu(s) avec succès : {', '.join(files_received)}".encode('utf-8'))
            else:
                self.send_error(400, "Aucun fichier n'a été envoyé ou le format est incorrect.")

        else:
            # Gérer les requêtes POST qui ne sont pas de type multipart/form-data.
            self.send_error(400, "Type de contenu non supporté. Veuillez utiliser multipart/form-data.")

    def _save_uploaded_file(self, field_item, files_received_list):
        """
        Sauvegarde un fichier uploadé sur le disque.
        Prend des mesures pour sécuriser le nom de fichier.
        """
        # Utilise os.path.basename pour extraire le nom du fichier du chemin complet,
        # prévenant ainsi les attaques de "path traversal" où un utilisateur malveillant
        # pourrait essayer de sauvegarder un fichier en dehors du répertoire d'upload.
        filename = os.path.basename(field_item.filename)
        filepath = os.path.join(UPLOAD_DIR, filename)

        try:
            with open(filepath, 'wb') as f:
                f.write(field_item.file.read())
            print(f"Fichier '{filename}' reçu et sauvegardé.")
            files_received_list.append(filename)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier '{filename}' : {e}")
            # En cas d'erreur lors de la sauvegarde d'un fichier,
            # nous affichons l'erreur mais ne renvoyons pas d'erreur HTTP 500
            # immédiatement, permettant aux autres fichiers d'être traités.

    def _generate_directory_listing(self, current_web_path, current_fs_path):
        """
        Génère une page HTML pour lister le contenu d'un répertoire donné.
        """
        # S'assurer que le chemin web se termine par un slash pour les dossiers
        if not current_web_path.endswith('/'):
            current_web_path += '/'

        html = [
            '<!DOCTYPE html>',
            '<html lang="fr">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <title>Partage de fichiers - ' + current_web_path + '</title>',
            '    <style>',
            '        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }',
            '        h1 { color: #0056b3; text-align: center; margin-bottom: 30px; }',
            '        .container { max-width: 800px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
            '        ul { list-style: none; padding: 0; }',
            '        li { margin-bottom: 8px; }',
            '        li a { text-decoration: none; color: #007bff; font-weight: bold; }',
            '        li a:hover { text-decoration: underline; }',
            '        .folder-icon::before { content: "📁 "; }',
            '        .file-icon::before { content: "📄 "; }',
            '        .back-link { display: block; margin-bottom: 15px; font-weight: bold; }',
            '        .back-link a { color: #dc3545; }',
            '    </style>',
            '</head>',
            '<body>',
            '    <div class="container">',
            '        <h1>Contenu de ' + current_web_path + '</h1>',
        ]

        # Lien "Retour" si ce n'est pas la racine du partage
        if current_web_path != '/':
            parent_web_path = os.path.dirname(os.path.normpath(current_web_path)) # Parent du chemin web
            if parent_web_path == '.': # Cas où le parent est la racine de partage
                parent_web_path = '/'
            parent_url = '/get' + urllib.parse.quote(parent_web_path)
            html.append(f'        <p class="back-link"><a href="{parent_url}">Retour au dossier parent</a></p>')

        html.append('        <ul>')

        # Lister les répertoires d'abord
        for item in sorted(os.listdir(current_fs_path)):
            item_fs_path = os.path.join(current_fs_path, item)
            # Ne pas afficher les fichiers cachés (commençant par un point)
            if item.startswith('.'):
                continue
            
            # Encoder le nom de l'élément pour l'URL
            encoded_item = urllib.parse.quote(item)
            
            if os.path.isdir(item_fs_path):
                # Ajouter un slash à la fin pour les dossiers dans l'URL
                html.append(f'            <li><span class="folder-icon"></span><a href="/get{current_web_path}{encoded_item}/">{item}/</a></li>')

        # Puis lister les fichiers
        for item in sorted(os.listdir(current_fs_path)):
            item_fs_path = os.path.join(current_fs_path, item)
            if item.startswith('.'):
                continue
            
            encoded_item = urllib.parse.quote(item)

            if os.path.isfile(item_fs_path):
                html.append(f'            <li><span class="file-icon"></span><a href="/get{current_web_path}{encoded_item}">{item}</a></li>')
        
        html.append('        </ul>')
        html.append('    </div>')
        html.append('</body>')
        html.append('</html>')

        return "\n".join(html)

    def do_GET(self):
        """
        Gère les requêtes GET.
        Sert le formulaire HTML pour l'upload de fichiers si l'URL est '/upload'.
        Sinon, utilise le comportement par défaut de SimpleHTTPRequestHandler.
        """
        if self.path == '/upload':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_content = f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Uploader des fichiers</title>
                <style>
                    body {{ font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }}
                    h1 {{ color: #0056b3; text-align: center; margin-bottom: 30px; }}
                    form {{
                        background-color: #ffffff;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        max-width: 500px;
                        margin: 0 auto;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }}
                    input[type="file"] {{
                        margin-bottom: 20px;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        width: 100%;
                        box-sizing: border-box;
                    }}
                    input[type="submit"] {{
                        background-color: #28a745;
                        color: white;
                        padding: 12px 25px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 1.1em;
                        transition: background-color 0.3s ease;
                    }}
                    input[type="submit"]:hover {{ background-color: #218838; }}
                    #messages {{ margin-top: 20px; text-align: center; font-size: 1.1em; }}
                    #success {{ color: #28a745; font-weight: bold; }}
                    #error {{ color: #dc3545; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>Uploader des fichiers sur l'ordinateur</h1>
                <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="files[]" id="fileInput" multiple accept="*/*"><br>
                    <input type="submit" value="Envoyer">
                </form>
                <div id="messages">
                    <p id="success"></p>
                    <p id="error"></p>
                </div>

                <script>
                    document.getElementById('uploadForm').onsubmit = function(event) {{
                        event.preventDefault(); // Empêche l'envoi classique du formulaire par le navigateur.

                        const fileInput = document.getElementById('fileInput');
                        const files = fileInput.files; // Récupère la liste des fichiers sélectionnés.
                        const successDiv = document.getElementById('success');
                        const errorDiv = document.getElementById('error');
                        
                        // Réinitialise les messages précédents.
                        successDiv.textContent = '';
                        errorDiv.textContent = '';

                        if (files.length === 0) {{
                            errorDiv.textContent = 'Veuillez sélectionner au moins un fichier.';
                            return;
                        }}

                        const formData = new FormData(); // Crée un objet FormData pour construire les données multipart.
                        for (let i = 0; i < files.length; i++) {{
                            // Ajoute chaque fichier à l'objet FormData sous le nom de champ 'files[]'.
                            // Le serveur Python attend ce nom.
                            formData.append('files[]', files[i]);
                        }}

                        // Utilise l'API Fetch pour envoyer les fichiers via une requête POST asynchrone.
                        fetch('/upload', {{
                            method: 'POST',
                            body: formData, // FormData gère automatiquement le Content-Type (multipart/form-data).
                        }})
                        .then(response => {{
                            if (response.ok) {{
                                return response.text(); // Si la réponse est OK, lit le texte de la réponse.
                            }}
                            // Si la réponse n'est pas OK, lit le texte d'erreur et le rejette.
                            return response.text().then(text => {{ throw new Error(text); }});
                        }})
                        .then(data => {{
                            successDiv.textContent = 'Fichier(s) envoyé(s) avec succès : ' + data;
                            fileInput.value = ''; // Réinitialise le champ de sélection de fichier.
                        }})
                        .catch(error => {{
                            errorDiv.textContent = 'Erreur lors de l\'envoi des fichiers : ' + error.message;
                            console.error('Erreur:', error);
                        }});
                    }};
                </script>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
        elif self.path.startswith('/get'):
            # Décoder le chemin de la requête pour gérer les espaces et caractères spéciaux
            # Exemple: /get/Mes%20Fichiers/ -> /Mes Fichiers/
            requested_path = urllib.parse.unquote(self.path[len('/get')+1:])

            # Normaliser le chemin pour gérer les '../' et autres
            # os.path.normpath('/a/b/../c') -> '/a/c'
            # os.path.join gère l'ajout du '/' si nécessaire
            print(SHARE_DIR)
            print(requested_path)
            full_path_requested = os.path.normpath(os.path.join(SHARE_DIR, requested_path))

            # --- Sécurité cruciale : Empêcher l'accès en dehors du répertoire partagé ---
            # Vérifier que le chemin résolu commence bien par le SHARE_DIR.
            # Convertir les deux en chemins absolus pour une comparaison fiable.
            
            if not os.path.abspath(full_path_requested).startswith(os.path.abspath(SHARE_DIR)):
                self.send_error(403, "Forbidden: Attempt to access outside shared directory.")
                return

            if os.path.isdir(full_path_requested):
                # Si c'est un répertoire, lister son contenu
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()

                # Générer la page HTML de navigation
                html_listing = self._generate_directory_listing(requested_path, full_path_requested)
                self.wfile.write(html_listing.encode('utf-8'))

            elif os.path.isfile(full_path_requested):
                # Si c'est un fichier, le servir (téléchargement)
                try:
                    self.send_response(200)
                    # Deviner le type MIME pour le navigateur (ex: image/png, application/pdf)
                    ctype = self.guess_type(full_path_requested)
                    self.send_header("Content-type", ctype)

                    # Permettre le téléchargement en indiquant le nom de fichier original
                    # Si le navigateur ne gère pas le type MIME, il le proposera au téléchargement.
                    # force_download = 'attachment'
                    # self.send_header("Content-Disposition", f"{force_download}; filename=\"{os.path.basename(full_path_requested)}\"")

                    # Obtenir la taille du fichier pour le Content-Length
                    file_size = os.path.getsize(full_path_requested)
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(full_path_requested)))
                    self.end_headers()

                    with open(full_path_requested, 'rb') as f:
                        self.copyfile(f, self.wfile) # Copie le contenu du fichier vers le flux de sortie HTTP

                except FileNotFoundError:
                    self.send_error(404, "File not found.")
                except Exception as e:
                    print(f"Erreur lors du service de fichier '{full_path_requested}': {e}")
                    self.send_error(500, f"Erreur serveur: {e}")
            else:
                self.send_error(404, "File or directory not found.")
        else:
            # Rediriger vers /upload
            self.send_response(302) # Code de statut 302 pour "Found" (redirection temporaire)
            self.send_header('Location', '/upload') # L'en-tête Location indique la nouvelle URL
            self.end_headers()
            # Il est bon de renvoyer un petit corps de réponse au cas où le navigateur ne suivrait pas la redirection.
            self.wfile.write(b'Redirection vers /upload')

# --- Fonctions utilitaires ---

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Se connecte à une adresse arbitraire pour obtenir l'IP locale sans envoyer de données.
        # Cette adresse est souvent utilisée car elle est censée être routable
        # mais ne mène nulle part, permettant à la socket de trouver l'interface de sortie.
        s.connect(('192.168.1.1', 1)) # Ou une autre IP locale de votre réseau, ou '8.8.8.8' (serveur DNS Google)
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1' # Fallback si l'IP locale ne peut pas être déterminée (ex: pas de connexion réseau).
    finally:
        s.close()
    return IP

# --- Lancement du serveur ---

if __name__ == "__main__":
    Handler = MyHandler

    # Crée et démarre le serveur TCP, qui gérera les requêtes HTTP.
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        local_ip = get_local_ip()
        print(f"Serveur HTTP démarré sur http://{local_ip}:{PORT}")
        print(f"Accédez à http://{local_ip}:{PORT}/upload depuis votre téléphone pour uploader des fichiers.")
        print("Appuyez sur Ctrl+C pour arrêter le serveur.")
        
        # Garde le serveur en fonctionnement indéfiniment jusqu'à une interruption (Ctrl+C).
        httpd.serve_forever()