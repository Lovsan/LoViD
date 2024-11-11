import sys
import json
import requests
import subprocess
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QMessageBox, QMenu,
    QHBoxLayout, QStyle, QGridLayout, QTextEdit, QSizePolicy, QScrollArea
)
from PyQt6.QtGui import QDesktopServices, QPixmap, QIcon, QAction
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

class MovieItemWidget(QWidget):
    def __init__(self, movie, parent=None, add_watch_later_callback=None):
        super().__init__(parent)
        self.movie = movie
        self.add_watch_later_callback = add_watch_later_callback
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        # Poster Image
        self.poster_label = QLabel()
        pixmap = self.get_image(self.movie.get('poster_path'))
        if pixmap:
            self.poster_label.setPixmap(pixmap.scaled(150, 225, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.poster_label.setText("No Image")
        content_layout.addWidget(self.poster_label)

        # Movie Information
        info_layout = QVBoxLayout()
        title_label = QLabel(f"<h2><b>{self.movie.get('title', 'No Title')}</b></h2>")
        release_date = self.movie.get('release_date', 'Unknown')
        release_year = release_date.split('-')[0] if release_date else 'Unknown'
        runtime = f"{self.movie.get('runtime', 'N/A')} min"
        rating = f"Rating: {self.movie.get('vote_average', 'N/A')}/10"

        # Additional Information
        genres = ', '.join([genre['name'] for genre in self.movie.get('genres', [])])
        languages = ', '.join([lang['english_name'] for lang in self.movie.get('spoken_languages', [])])
        production_companies = ', '.join([company['name'] for company in self.movie.get('production_companies', [])])

        info_text = f"""
        <b>Year:</b> {release_year}<br>
        <b>Runtime:</b> {runtime}<br>
        <b>{rating}</b><br>
        <b>Genres:</b> {genres}<br>
        <b>Languages:</b> {languages}<br>
        <b>Production Companies:</b> {production_companies}
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)

        # Overview
        overview_label = QLabel(f"<b>Overview:</b> {self.movie.get('overview', 'No overview available.')}")
        overview_label.setWordWrap(True)

        # Links to IMDb and TMDB
        links_layout = QHBoxLayout()
        imdb_button = QPushButton("IMDb Page")
        tmdb_button = QPushButton("TMDB Page")
        watch_later_button = QPushButton("Watch Later")
        trailer_button = QPushButton("Play Trailer")
        imdb_button.clicked.connect(self.open_imdb_page)
        tmdb_button.clicked.connect(self.open_tmdb_page)
        watch_later_button.clicked.connect(self.add_to_watch_later)
        trailer_button.clicked.connect(self.play_trailer)
        links_layout.addWidget(imdb_button)
        links_layout.addWidget(tmdb_button)
        links_layout.addWidget(trailer_button)
        links_layout.addWidget(watch_later_button)

        info_layout.addWidget(title_label)
        info_layout.addWidget(info_label)
        info_layout.addWidget(overview_label)
        info_layout.addLayout(links_layout)

        content_layout.addLayout(info_layout)

        # Cast Information with Images
        cast_widget = self.create_cast_widget()
        content_layout.addWidget(cast_widget)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def get_image(self, path, size='w500'):
        if path:
            base_url = f"https://image.tmdb.org/t/p/{size}"
            url = base_url + path
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

    def create_cast_widget(self):
        cast_layout = QVBoxLayout()
        cast_label = QLabel("<b>Cast:</b>")
        cast_layout.addWidget(cast_label)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        cast_content = QWidget()
        cast_grid = QGridLayout()
        cast_members = self.movie.get('cast', [])[:10]  # Get top 10 cast members

        for index, member in enumerate(cast_members):
            actor_layout = QVBoxLayout()
            actor_image_label = QLabel()
            profile_pixmap = self.get_image(member.get('profile_path'), size='w185')
            if profile_pixmap:
                actor_image_label.setPixmap(profile_pixmap.scaled(80, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                actor_image_label.setText("No Image")
            actor_name_label = QLabel(member.get('name', 'Unknown'))
            actor_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            actor_layout.addWidget(actor_image_label)
            actor_layout.addWidget(actor_name_label)
            actor_widget = QWidget()
            actor_widget.setLayout(actor_layout)
            cast_grid.addWidget(actor_widget, index // 5, index % 5)

        cast_content.setLayout(cast_grid)
        scroll_area.setWidget(cast_content)
        cast_layout.addWidget(scroll_area)
        cast_widget = QWidget()
        cast_widget.setLayout(cast_layout)
        return cast_widget

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

    def add_to_watch_later(self):
        if self.add_watch_later_callback:
            self.add_watch_later_callback(self.movie)
            QMessageBox.information(self, "Watch Later", f"'{self.movie.get('title', 'Movie')}' added to Watch Later.")

    def play_trailer(self):
        trailer_url = self.movie.get('trailer_url')
        if trailer_url:
            trailer_dialog = TrailerDialog(trailer_url)
            trailer_dialog.exec()
        else:
            QMessageBox.warning(self, "Trailer Not Available", "Trailer is not available for this movie.")


class TrailerDialog(QMessageBox):
    def __init__(self, trailer_url):
        super().__init__()
        self.setWindowTitle("Trailer")
        self.setStandardButtons(QMessageBox.StandardButton.Close)
        self.layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(trailer_url))
        self.layout.addWidget(self.web_view)
        self.setLayout(self.layout)
        self.setStyleSheet("QMessageBox { background-color: #2E2E2E; }")

    def exec(self):
        super().exec()

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
            play_action.triggered.connect(lambda: self.item_clicked_callback(item, 'embedded'))
            open_browser_action.triggered.connect(lambda: self.item_clicked_callback(item, 'browser'))
            menu.addAction(play_action)
            menu.addAction(open_browser_action)
            menu.exec(self.mapToGlobal(position))

class TMDBApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TMDB App")
        self.setGeometry(100, 100, 1000, 800)

        self.bearer_token = ""  # Bearer token for authentication
        self.watch_later_list = []

        self.load_config()

        self.init_ui()
        self.apply_stylesheet()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.bearer_token = config.get('bearer_token', '')
        except FileNotFoundError:
            self.save_config()

        # Load Watch Later list
        if os.path.exists('watch_later.json'):
            try:
                with open('watch_later.json', 'r') as f:
                    self.watch_later_list = json.load(f)
            except json.JSONDecodeError:
                self.watch_later_list = []
        else:
            self.watch_later_list = []

    def save_config(self):
        config = {
            'bearer_token': self.bearer_token
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)

        # Save Watch Later list
        with open('watch_later.json', 'w') as f:
            json.dump(self.watch_later_list, f)

    def init_ui(self):
        self.create_menu_bar()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.favorites_tab = QWidget()
        self.search_tab = QWidget()
        self.settings_tab = QWidget()
        self.player_tab = QWidget()
        self.now_playing_tab = QWidget()
        self.top_rated_tab = QWidget()
        self.tv_shows_tab = QWidget()
        self.watch_later_tab = QWidget()

        self.init_favorites_tab()
        self.init_search_tab()
        self.init_settings_tab()
        self.init_player_tab()
        self.init_now_playing_tab()
        self.init_top_rated_tab()
        self.init_tv_shows_tab()
        self.init_watch_later_tab()

        # Add initial tabs
        self.tabs.addTab(self.favorites_tab, "Favorites")
        self.tabs.addTab(self.search_tab, "Search")

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # Home Menu
        home_menu = menu_bar.addMenu("Home")

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_tab)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)

        home_menu.addAction(settings_action)
        home_menu.addAction(exit_action)

        # My Videos Menu
        my_videos_menu = menu_bar.addMenu("My Videos")

        favorites_action = QAction("TMDB Favorites", self)
        favorites_action.triggered.connect(self.open_favorites_tab)
        watch_later_action = QAction("Watch Later", self)
        watch_later_action.triggered.connect(self.open_watch_later_tab)

        my_videos_menu.addAction(favorites_action)
        my_videos_menu.addAction(watch_later_action)

        # Movies Menu
        movies_menu = menu_bar.addMenu("Movies")

        now_playing_action = QAction("Now Playing", self)
        now_playing_action.triggered.connect(self.open_now_playing_tab)
        top_rated_action = QAction("Top Rated", self)
        top_rated_action.triggered.connect(self.open_top_rated_tab)

        movies_menu.addAction(now_playing_action)
        movies_menu.addAction(top_rated_action)

        # TV Shows Menu
        tv_shows_menu = menu_bar.addMenu("TV Shows")
        tv_shows_action = QAction("Popular TV Shows", self)
        tv_shows_action.triggered.connect(self.open_tv_shows_tab)

        tv_shows_menu.addAction(tv_shows_action)

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
        # Adjust settings to attempt to fix CORS issues (may not be effective)
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        layout.addWidget(self.web_view)
        self.player_tab.setLayout(layout)

    def init_now_playing_tab(self):
        layout = QVBoxLayout()
        self.now_playing_list = CustomListWidget(item_clicked_callback=self.handle_item_action)
        layout.addWidget(self.now_playing_list)
        self.now_playing_tab.setLayout(layout)

    def init_top_rated_tab(self):
        layout = QVBoxLayout()
        self.top_rated_list = CustomListWidget(item_clicked_callback=self.handle_item_action)
        layout.addWidget(self.top_rated_list)
        self.top_rated_tab.setLayout(layout)

    def init_tv_shows_tab(self):
        layout = QVBoxLayout()
        self.tv_shows_list = CustomListWidget(item_clicked_callback=self.handle_tv_show_action)
        layout.addWidget(self.tv_shows_list)
        self.tv_shows_tab.setLayout(layout)

    def init_watch_later_tab(self):
        layout = QVBoxLayout()
        self.watch_later_list_widget = CustomListWidget(item_clicked_callback=self.handle_item_action)
        layout.addWidget(self.watch_later_list_widget)
        self.watch_later_tab.setLayout(layout)
        self.load_watch_later()

    def close_tab(self, index):
        widget = self.tabs.widget(index)
        if widget:
            self.tabs.removeTab(index)

    def open_settings_tab(self):
        if self.tabs.indexOf(self.settings_tab) == -1:
            self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.setCurrentWidget(self.settings_tab)

    def open_favorites_tab(self):
        if self.tabs.indexOf(self.favorites_tab) == -1:
            self.tabs.addTab(self.favorites_tab, "Favorites")
            self.load_favorites()
        self.tabs.setCurrentWidget(self.favorites_tab)

    def open_now_playing_tab(self):
        if self.tabs.indexOf(self.now_playing_tab) == -1:
            self.tabs.addTab(self.now_playing_tab, "Now Playing")
            self.load_now_playing()
        self.tabs.setCurrentWidget(self.now_playing_tab)

    def open_top_rated_tab(self):
        if self.tabs.indexOf(self.top_rated_tab) == -1:
            self.tabs.addTab(self.top_rated_tab, "Top Rated")
            self.load_top_rated()
        self.tabs.setCurrentWidget(self.top_rated_tab)

    def open_tv_shows_tab(self):
        if self.tabs.indexOf(self.tv_shows_tab) == -1:
            self.tabs.addTab(self.tv_shows_tab, "TV Shows")
            self.load_tv_shows()
        self.tabs.setCurrentWidget(self.tv_shows_tab)

    def open_watch_later_tab(self):
        if self.tabs.indexOf(self.watch_later_tab) == -1:
            self.tabs.addTab(self.watch_later_tab, "Watch Later")
            self.load_watch_later()
        self.tabs.setCurrentWidget(self.watch_later_tab)

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
                    item.setSizeHint(QSize(300, 250))
                    item.setData(Qt.ItemDataRole.UserRole, movie)
                    widget = MovieItemWidget(movie, add_watch_later_callback=self.add_to_watch_later)
                    self.favorites_list.addItem(item)
                    self.favorites_list.setItemWidget(item, widget)
        else:
            QMessageBox.critical(self, "Error", "Failed to load favorite movies.")

    def load_now_playing(self):
        data = self.tmdb_api_request("movie/now_playing", params={"language": "en-US"})
        if data:
            self.now_playing_list.clear()
            for movie_summary in data['results']:
                movie = self.get_movie_details(movie_summary['id'])
                if movie:
                    item = QListWidgetItem()
                    item.setSizeHint(QSize(300, 250))
                    item.setData(Qt.ItemDataRole.UserRole, movie)
                    widget = MovieItemWidget(movie, add_watch_later_callback=self.add_to_watch_later)
                    self.now_playing_list.addItem(item)
                    self.now_playing_list.setItemWidget(item, widget)
        else:
            QMessageBox.critical(self, "Error", "Failed to load Now Playing movies.")

    def load_top_rated(self):
        data = self.tmdb_api_request("movie/top_rated", params={"language": "en-US"})
        if data:
            self.top_rated_list.clear()
            for movie_summary in data['results']:
                movie = self.get_movie_details(movie_summary['id'])
                if movie:
                    item = QListWidgetItem()
                    item.setSizeHint(QSize(300, 250))
                    item.setData(Qt.ItemDataRole.UserRole, movie)
                    widget = MovieItemWidget(movie, add_watch_later_callback=self.add_to_watch_later)
                    self.top_rated_list.addItem(item)
                    self.top_rated_list.setItemWidget(item, widget)
        else:
            QMessageBox.critical(self, "Error", "Failed to load Top Rated movies.")

    def load_tv_shows(self):
        data = self.tmdb_api_request("tv/popular", params={"language": "en-US"})
        if data:
            self.tv_shows_list.clear()
            for tv_show_summary in data['results']:
                tv_show = self.get_tv_show_details(tv_show_summary['id'])
                if tv_show:
                    item = QListWidgetItem()
                    item.setSizeHint(QSize(300, 250))
                    item.setData(Qt.ItemDataRole.UserRole, tv_show)
                    widget = TVShowItemWidget(tv_show, add_watch_later_callback=self.add_to_watch_later)
                    self.tv_shows_list.addItem(item)
                    self.tv_shows_list.setItemWidget(item, widget)
        else:
            QMessageBox.critical(self, "Error", "Failed to load TV Shows.")

    def load_watch_later(self):
        self.watch_later_list_widget.clear()
        for movie_id in self.watch_later_list:
            movie = self.get_movie_details(movie_id)
            if movie:
                item = QListWidgetItem()
                item.setSizeHint(QSize(300, 250))
                item.setData(Qt.ItemDataRole.UserRole, movie)
                widget = MovieItemWidget(movie, add_watch_later_callback=self.add_to_watch_later)
                self.watch_later_list_widget.addItem(item)
                self.watch_later_list_widget.setItemWidget(item, widget)

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
                    item.setSizeHint(QSize(300, 250))
                    item.setData(Qt.ItemDataRole.UserRole, movie)
                    widget = MovieItemWidget(movie, add_watch_later_callback=self.add_to_watch_later)
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
            # Get IMDb ID
            external_ids = self.tmdb_api_request(f"movie/{movie_id}/external_ids")
            if external_ids:
                movie['imdb_id'] = external_ids.get('imdb_id')
            else:
                movie['imdb_id'] = None
            # Get Trailer URL
            videos = self.tmdb_api_request(f"movie/{movie_id}/videos", params={"language": "en-US"})
            if videos:
                trailer_url = self.get_trailer_url(videos.get('results', []))
                movie['trailer_url'] = trailer_url
            else:
                movie['trailer_url'] = None
            return movie
        else:
            return None

    def get_trailer_url(self, videos):
        for video in videos:
            if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                key = video['key']
                return f"https://www.youtube.com/embed/{key}"
        return None

    def get_tv_show_details(self, tv_id):
        tv_show = self.tmdb_api_request(f"tv/{tv_id}", params={"language": "en-US"})
        if tv_show:
            # Get credits to obtain cast information
            credits = self.tmdb_api_request(f"tv/{tv_id}/credits")
            if credits:
                tv_show['cast'] = credits.get('cast', [])
            else:
                tv_show['cast'] = []
            # Get IMDb ID
            external_ids = self.tmdb_api_request(f"tv/{tv_id}/external_ids")
            if external_ids:
                tv_show['imdb_id'] = external_ids.get('imdb_id')
            else:
                tv_show['imdb_id'] = None
            # Get Trailer URL
            videos = self.tmdb_api_request(f"tv/{tv_id}/videos", params={"language": "en-US"})
            if videos:
                trailer_url = self.get_trailer_url(videos.get('results', []))
                tv_show['trailer_url'] = trailer_url
            else:
                tv_show['trailer_url'] = None
            return tv_show
        else:
            return None

    def handle_item_action(self, item, action):
        movie = item.data(Qt.ItemDataRole.UserRole)
        if action == 'embedded':
            self.play_movie_embedded(movie['id'])
        elif action == 'browser':
            self.play_movie_in_browser(movie['id'])

    def handle_tv_show_action(self, item, action):
        tv_show = item.data(Qt.ItemDataRole.UserRole)
        QMessageBox.information(self, "TV Show Selected", f"You selected TV Show: {tv_show.get('name', 'Unknown')}")

    def play_movie_embedded(self, movie_id):
        embed_url = f"https://vidbinge.dev/embed/movie/{movie_id}"
        self.web_view.setUrl(QUrl(embed_url))
        if self.tabs.indexOf(self.player_tab) == -1:
            self.tabs.addTab(self.player_tab, "Player")
        self.tabs.setCurrentWidget(self.player_tab)

    def play_movie_in_browser(self, movie_id):
        embed_url = f"https://vidbinge.dev/embed/movie/{movie_id}"
        QDesktopServices.openUrl(QUrl(embed_url))

    def add_to_watch_later(self, movie):
        movie_id = movie.get('id')
        if movie_id not in self.watch_later_list:
            self.watch_later_list.append(movie_id)
            self.save_config()
            self.load_watch_later()

    def save_settings(self):
        self.bearer_token = self.bearer_token_input.text().strip()
        self.save_config()
        QMessageBox.information(self, "Settings", "Settings saved successfully.")
        self.load_favorites()

    def apply_stylesheet(self):
        # Apply the provided stylesheet
        updated_stylesheet = """
        /* General app styling */
        QWidget {
            background-color: #2E2E2E; /* Dark grey background */
            color: #D3D3D3; /* Light grey text */
            font-family: Arial, sans-serif;
            font-size: 14px; /* Default font size */
        }

        /* Button styling */
        QPushButton {
            background-color: #4D4D4D; /* Darker grey for button background */
            color: #FFFFFF; /* White text */
            border: 1px solid #3C3C3C;
            border-radius: 8px; /* More rounded borders */
            padding: 8px 12px; /* Increased padding for larger buttons */
            font-size: 14px; /* Larger font size for buttons */
        }

        QPushButton:hover {
            background-color: #666666; /* Lighter grey for hover */
        }

        QPushButton:pressed {
            background-color: #5E5E5E; /* Slightly lighter grey for pressed state */
        }

        /* Tab styling */
        QTabBar::tab {
            background: #4D4D4D; /* Dark grey for tabs */
            color: #D3D3D3; /* Light grey text */
            padding: 10px;
            border: 1px solid #3C3C3C;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-size: 14px;
        }

        QTabBar::tab:selected {
            background: orange; /* Orange for selected tab */
            color: #FFFFFF;
        }

        QTabBar::tab:hover {
            background: #666666; /* Lighter grey on hover */
        }

        /* Input fields */
        QLineEdit, QComboBox {
            background-color: #3E3E3E; /* Darker grey for input background */
            color: #FFFFFF; /* White text */
            border: 1px solid #666666;
            border-radius: 5px; /* More rounded borders */
            padding: 6px;
            font-size: 14px;
        }

        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #4CAF50; /* Green border when focused */
        }

        /* Checkbox styling */
        QCheckBox {
            color: #D3D3D3; /* Light grey text */
            font-size: 14px;
        }

        /* Header styling */
        QHeaderView::section {
            background-color: #4D4D4D; /* Dark grey background for headers */
            color: #D3D3D3; /* Light grey text */
            padding: 8px;
            border: 1px solid #3C3C3C;
            font-size: 14px;
        }

        /* Progress bar styling */
        QProgressBar {
            background-color: #3C3C3C; /* Dark grey background */
            border: 1px solid #5E5E5E;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
        }

        QProgressBar::chunk {
            background-color: #4CAF50; /* Green progress indicator */
        }

        /* Scrollbar styling */
        QScrollBar:vertical {
            background: #3C3C3C;
            width: 12px; /* Slightly wider for easier use */
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #5E5E5E;
            min-height: 20px;
            border-radius: 6px; /* Rounded scrollbar handle */
        }

        QScrollBar::handle:vertical:hover {
            background: #707070;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
        }

        /* Tooltips */
        QToolTip {
            background-color: #4D4D4D;
            color: #FFFFFF;
            border: 1px solid #707070;
            padding: 6px;
            border-radius: 5px;
            font-size: 14px;
        }
        """
        self.setStyleSheet(updated_stylesheet)

class TVShowItemWidget(MovieItemWidget):
    def __init__(self, tv_show, parent=None, add_watch_later_callback=None):
        self.tv_show = tv_show
        super().__init__(tv_show, parent, add_watch_later_callback)

    def init_ui(self):
        main_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        # Poster Image
        self.poster_label = QLabel()
        pixmap = self.get_image(self.tv_show.get('poster_path'))
        if pixmap:
            self.poster_label.setPixmap(pixmap.scaled(150, 225, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.poster_label.setText("No Image")
        content_layout.addWidget(self.poster_label)

        # TV Show Information
        info_layout = QVBoxLayout()
        title_label = QLabel(f"<h2><b>{self.tv_show.get('name', 'No Title')}</b></h2>")
        first_air_date = self.tv_show.get('first_air_date', 'Unknown')
        release_year = first_air_date.split('-')[0] if first_air_date else 'Unknown'
        rating = f"Rating: {self.tv_show.get('vote_average', 'N/A')}/10"

        # Additional Information
        genres = ', '.join([genre['name'] for genre in self.tv_show.get('genres', [])])
        languages = ', '.join([lang['english_name'] for lang in self.tv_show.get('spoken_languages', [])])
        production_companies = ', '.join([company['name'] for company in self.tv_show.get('production_companies', [])])

        info_text = f"""
        <b>Year:</b> {release_year}<br>
        <b>{rating}</b><br>
        <b>Genres:</b> {genres}<br>
        <b>Languages:</b> {languages}<br>
        <b>Production Companies:</b> {production_companies}
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)

        # Overview
        overview_label = QLabel(f"<b>Overview:</b> {self.tv_show.get('overview', 'No overview available.')}")
        overview_label.setWordWrap(True)

        # Links to IMDb and TMDB
        links_layout = QHBoxLayout()
        imdb_button = QPushButton("IMDb Page")
        tmdb_button = QPushButton("TMDB Page")
        watch_later_button = QPushButton("Watch Later")
        trailer_button = QPushButton("Play Trailer")
        imdb_button.clicked.connect(self.open_imdb_page)
        tmdb_button.clicked.connect(self.open_tmdb_page)
        watch_later_button.clicked.connect(self.add_to_watch_later)
        trailer_button.clicked.connect(self.play_trailer)
        links_layout.addWidget(imdb_button)
        links_layout.addWidget(tmdb_button)
        links_layout.addWidget(trailer_button)
        links_layout.addWidget(watch_later_button)

        info_layout.addWidget(title_label)
        info_layout.addWidget(info_label)
        info_layout.addWidget(overview_label)
        info_layout.addLayout(links_layout)

        content_layout.addLayout(info_layout)

        # Cast Information with Images
        cast_widget = self.create_cast_widget()
        content_layout.addWidget(cast_widget)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def open_imdb_page(self):
        imdb_id = self.tv_show.get('imdb_id')
        if imdb_id:
            url = f"https://www.imdb.com/title/{imdb_id}/"
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.warning(self, "IMDb ID Not Available", "IMDb ID is not available for this TV show.")

    def open_tmdb_page(self):
        tmdb_id = self.tv_show.get('id')
        url = f"https://www.themoviedb.org/tv/{tmdb_id}"
        QDesktopServices.openUrl(QUrl(url))

    def play_trailer(self):
        trailer_url = self.tv_show.get('trailer_url')
        if trailer_url:
            trailer_dialog = TrailerDialog(trailer_url)
            trailer_dialog.exec()
        else:
            QMessageBox.warning(self, "Trailer Not Available", "Trailer is not available for this TV show.")

    def add_to_watch_later(self):
        if self.add_watch_later_callback:
            self.add_watch_later_callback(self.tv_show)
            QMessageBox.information(self, "Watch Later", f"'{self.tv_show.get('name', 'TV Show')}' added to Watch Later.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TMDBApp()
    window.show()
    sys.exit(app.exec())
