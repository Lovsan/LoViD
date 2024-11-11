import sys
import json
import requests
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QMessageBox, QMenu,
    QHBoxLayout, QTextEdit
)
from PyQt6.QtGui import QDesktopServices, QAction, QPixmap
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

class MovieItemWidget(QWidget):
    def __init__(self, movie, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        # Poster Image
        self.poster_label = QLabel()
        pixmap = self.get_movie_poster(self.movie.get('poster_path'))
        if pixmap:
            self.poster_label.setPixmap(pixmap.scaled(100, 150, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.poster_label.setText("No Image")
        layout.addWidget(self.poster_label)

        # Movie Information
        info_layout = QVBoxLayout()
        title_label = QLabel(f"<b>{self.movie.get('title', 'No Title')}</b>")
        release_date = self.movie.get('release_date', 'Unknown')
        release_year = release_date.split('-')[0] if release_date else 'Unknown'
        runtime = f"{self.movie.get('runtime', 'N/A')} min"
        overview = self.movie.get('overview', 'No overview available.')
        rating = f"Rating: {self.movie.get('vote_average', 'N/A')}/10"

        info_label = QLabel(f"Year: {release_year}\nRuntime: {runtime}\n{rating}")
        overview_label = QLabel(overview)
        overview_label.setWordWrap(True)

        # Links to IMDb and TMDB
        links_layout = QHBoxLayout()
        imdb_button = QPushButton("IMDb Page")
        tmdb_button = QPushButton("TMDB Page")
        imdb_button.clicked.connect(self.open_imdb_page)
        tmdb_button.clicked.connect(self.open_tmdb_page)
        links_layout.addWidget(imdb_button)
        links_layout.addWidget(tmdb_button)

        # Cast Information
        cast_label = QLabel("<b>Cast:</b> " + self.get_cast_info())

        info_layout.addWidget(title_label)
        info_layout.addWidget(info_label)
        info_layout.addWidget(overview_label)
        info_layout.addLayout(links_layout)
        info_layout.addWidget(cast_label)
        layout.addLayout(info_layout)

        self.setLayout(layout)

    def get_movie_poster(self, poster_path):
        if poster_path:
            base_url = "https://image.tmdb.org/t/p/w500"
            url = base_url + poster_path
            try:
                response = requests.get(url)
                response.raise_for_status()
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                return pixmap
            except requests.RequestException:
                return None
        else:
            return None

    def open_imdb_page(self):
        imdb_id = self.movie.get('imdb_id')
        if imdb_id:
            url = f"https://www.imdb.com/title/{imdb_id}/"
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.warning(self, "IMDb ID Not Available", "IMDb ID is not available for this movie.")

    def open_tmdb_page(self):
        tmdb_id = self.movie.get('id')
        url = f"https://www.themoviedb.org/movie/{tmdb_id}"
        QDesktopServices.openUrl(QUrl(url))

    def get_cast_info(self):
        cast = self.movie.get('cast', [])
        cast_names = [member['name'] for member in cast[:5]]  # Get top 5 cast members
        return ', '.join(cast_names) if cast_names else "No cast information available."

class CustomListWidget(QListWidget):
    def __init__(self, parent=None, item_clicked_callback=None):
        super().__init__(parent)
        self.item_clicked_callback = item_clicked_callback
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        item = self.itemAt(position)
        if item:
            movie = item.data(Qt.ItemDataRole.UserRole)
            menu = QMenu(self)
            play_action = QAction("Play in Embedded Player", self)
            open_browser_action = QAction("Open in Browser", self)
            stream_vlc_action = QAction("Stream with VLC", self)

            play_action.triggered.connect(lambda: self.item_clicked_callback(item, 'embedded'))
            open_browser_action.triggered.connect(lambda: self.item_clicked_callback(item, 'browser'))
            stream_vlc_action.triggered.connect(lambda: self.item_clicked_callback(item, 'vlc'))

            menu.addAction(play_action)
            menu.addAction(open_browser_action)
            menu.addAction(stream_vlc_action)

            menu.exec(self.mapToGlobal(position))

class TMDBApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TMDB App")
        self.setGeometry(100, 100, 800, 600)

        self.bearer_token = ""  # Bearer token for authentication

        self.load_config()

        self.init_ui()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.bearer_token = config.get('bearer_token', '')
        except FileNotFoundError:
            self.save_config()

    def save_config(self):
        config = {
            'bearer_token': self.bearer_token
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.favorites_tab = QWidget()
        self.search_tab = QWidget()
        self.settings_tab = QWidget()
        self.player_tab = QWidget()

        self.tabs.addTab(self.favorites_tab, "Favorites")
        self.tabs.addTab(self.search_tab, "Search")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.player_tab, "Player")

        self.init_favorites_tab()
        self.init_search_tab()
        self.init_settings_tab()
        self.init_player_tab()

    def init_favorites_tab(self):
        layout = QVBoxLayout()
        self.favorites_list = CustomListWidget(item_clicked_callback=self.handle_item_action)
        layout.addWidget(self.favorites_list)
        self.favorites_tab.setLayout(layout)
        self.load_favorites()

    def init_search_tab(self):
        layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for movies...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_movies)
        self.search_results = CustomListWidget(item_clicked_callback=self.handle_item_action)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(self.search_results)
        self.search_tab.setLayout(layout)

    def init_settings_tab(self):
        layout = QVBoxLayout()
        self.bearer_token_input = QLineEdit(self.bearer_token)
        self.bearer_token_input.setPlaceholderText("Enter your Bearer Token")
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(QLabel("TMDB Bearer Token:"))
        layout.addWidget(self.bearer_token_input)
        layout.addWidget(self.save_button)
        self.settings_tab.setLayout(layout)

    def init_player_tab(self):
        layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        # Attempt to adjust settings to fix CORS issues (may not work)
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        layout.addWidget(self.web_view)
        self.player_tab.setLayout(layout)

    def tmdb_api_request(self, endpoint, params=None, method='GET'):
        base_url = "https://api.themoviedb.org/3/"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.bearer_token}"
        }

        url = f"{base_url}{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"TMDB API request failed: {e}")
            return None

    def load_favorites(self):
        if not self.bearer_token:
            QMessageBox.warning(self, "Warning", "Please set your Bearer Token in the Settings tab.")
            return

        account_details = self.tmdb_api_request("account")
        if account_details:
            account_id = account_details['id']
        else:
            QMessageBox.critical(self, "Error", "Failed to retrieve account details.")
            return

        data = self.tmdb_api_request(f"account/{account_id}/favorite/movies", params={
            "language": "en-US",
            "sort_by": "created_at.asc"
        })
        if data:
            self.favorites_list.clear()
            for movie_summary in data['results']:
                # Get detailed movie information
                movie = self.get_movie_details(movie_summary['id'])
                if movie:
                    item = QListWidgetItem()
                    item.setSizeHint(QSize(200, 150))
                    item.setData(Qt.ItemDataRole.UserRole, movie)
                    widget = MovieItemWidget(movie)
                    self.favorites_list.addItem(item)
                    self.favorites_list.setItemWidget(item, widget)
        else:
            QMessageBox.critical(self, "Error", "Failed to load favorite movies.")

    def search_movies(self):
        query = self.search_input.text()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter a search term.")
            return
        data = self.tmdb_api_request("search/movie", params={"query": query})
        if data:
            self.search_results.clear()
            for movie_summary in data['results']:
                # Get detailed movie information
                movie = self.get_movie_details(movie_summary['id'])
                if movie:
                    item = QListWidgetItem()
                    item.setSizeHint(QSize(200, 150))
                    item.setData(Qt.ItemDataRole.UserRole, movie)
                    widget = MovieItemWidget(movie)
                    self.search_results.addItem(item)
                    self.search_results.setItemWidget(item, widget)
        else:
            QMessageBox.critical(self, "Error", "Failed to search movies.")

    def get_movie_details(self, movie_id):
        # Get movie details
        movie = self.tmdb_api_request(f"movie/{movie_id}", params={"language": "en-US"})
        if movie:
            # Get credits to obtain cast information
            credits = self.tmdb_api_request(f"movie/{movie_id}/credits")
            if credits:
                movie['cast'] = credits.get('cast', [])
            else:
                movie['cast'] = []
            return movie
        else:
            return None

    def handle_item_action(self, item, action):
        movie = item.data(Qt.ItemDataRole.UserRole)
        if action == 'embedded':
            self.play_movie_embedded(movie['id'])
        elif action == 'browser':
            self.play_movie_in_browser(movie['id'])
        elif action == 'vlc':
            self.stream_with_vlc(movie['id'])

    def play_movie_embedded(self, movie_id):
        embed_url = f"https://vidbinge.dev/embed/movie/{movie_id}"
        self.web_view.setUrl(QUrl(embed_url))
        self.tabs.setCurrentWidget(self.player_tab)

    def play_movie_in_browser(self, movie_id):
        embed_url = f"https://vidbinge.dev/embed/movie/{movie_id}"
        QDesktopServices.openUrl(QUrl(embed_url))

    def stream_with_vlc(self, movie_id):
        # Attempt to extract HLS link (requires network requests and parsing)
        hls_url = self.get_hls_url(movie_id)
        if hls_url:
            subprocess.Popen(["vlc", hls_url])
        else:
            QMessageBox.warning(self, "Error", "Failed to retrieve HLS stream URL.")

    def get_hls_url(self, movie_id):
        # WARNING: Accessing HLS streams directly may violate terms of service.
        import re
        embed_url = f"https://vidbinge.dev/embed/movie/{movie_id}"
        try:
            response = requests.get(embed_url)
            response.raise_for_status()
            # Simplified regex to find .m3u8 URLs in the page content
            hls_urls = re.findall(r'(https?://[^\s\'"]+\.m3u8)', response.text)
            if hls_urls:
                return hls_urls[0]
        except requests.RequestException as e:
            print(f"Error fetching embed page: {e}")
        return None

    def save_settings(self):
        self.bearer_token = self.bearer_token_input.text().strip()
        self.save_config()
        QMessageBox.information(self, "Settings", "Settings saved successfully.")
        self.load_favorites()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TMDBApp()
    window.show()
    sys.exit(app.exec())
