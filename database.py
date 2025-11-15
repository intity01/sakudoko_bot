"""
Database module for Sakudoko Music Bot
Handles SQLite database operations for song history, playlists, and settings
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

logger = logging.getLogger('discord_bot')

class Database:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize()
    
    def initialize(self):
        """Initialize database connection and create tables"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.create_tables()
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def create_tables(self):
        """Create all necessary tables"""
        # Song history table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS song_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            song_title TEXT NOT NULL,
            song_url TEXT NOT NULL,
            song_duration INTEGER,
            requested_by INTEGER NOT NULL,
            requested_by_name TEXT,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # User playlists table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            playlist_name TEXT NOT NULL,
            songs TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(guild_id, user_id, playlist_name)
        )
        ''')
        
        # Guild settings table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            default_volume INTEGER DEFAULT 100,
            default_filter TEXT DEFAULT NULL,
            auto_disconnect INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()
    
    # Song History Methods
    def add_song_history(self, guild_id: int, song_title: str, song_url: str, 
                        song_duration: int, requested_by: int, requested_by_name: str):
        """Add a song to history"""
        try:
            self.cursor.execute('''
            INSERT INTO song_history (guild_id, song_title, song_url, song_duration, requested_by, requested_by_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (guild_id, song_title, song_url, song_duration, requested_by, requested_by_name))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to add song history: {e}")
    
    def get_song_history(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Get recent song history for a guild"""
        try:
            self.cursor.execute('''
            SELECT song_title, song_url, requested_by_name, played_at
            FROM song_history
            WHERE guild_id = ?
            ORDER BY played_at DESC
            LIMIT ?
            ''', (guild_id, limit))
            
            rows = self.cursor.fetchall()
            return [
                {
                    'title': row[0],
                    'url': row[1],
                    'requested_by': row[2],
                    'played_at': row[3]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Failed to get song history: {e}")
            return []
    
    def get_top_songs(self, guild_id: int, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most played songs for a guild"""
        try:
            self.cursor.execute('''
            SELECT song_title, COUNT(*) as play_count
            FROM song_history
            WHERE guild_id = ?
            GROUP BY song_title
            ORDER BY play_count DESC
            LIMIT ?
            ''', (guild_id, limit))
            
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to get top songs: {e}")
            return []
    
    # Playlist Methods
    def save_playlist(self, guild_id: int, user_id: int, playlist_name: str, songs: List[Dict]) -> bool:
        """Save or update a user playlist"""
        try:
            songs_json = json.dumps(songs)
            self.cursor.execute('''
            INSERT INTO user_playlists (guild_id, user_id, playlist_name, songs, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id, playlist_name) 
            DO UPDATE SET songs = excluded.songs, updated_at = CURRENT_TIMESTAMP
            ''', (guild_id, user_id, playlist_name, songs_json))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save playlist: {e}")
            return False
    
    def get_playlist(self, guild_id: int, user_id: int, playlist_name: str) -> Optional[List[Dict]]:
        """Get a user playlist"""
        try:
            self.cursor.execute('''
            SELECT songs FROM user_playlists
            WHERE guild_id = ? AND user_id = ? AND playlist_name = ?
            ''', (guild_id, user_id, playlist_name))
            
            row = self.cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get playlist: {e}")
            return None
    
    def get_user_playlists(self, guild_id: int, user_id: int) -> List[str]:
        """Get all playlist names for a user"""
        try:
            self.cursor.execute('''
            SELECT playlist_name FROM user_playlists
            WHERE guild_id = ? AND user_id = ?
            ORDER BY updated_at DESC
            ''', (guild_id, user_id))
            
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get user playlists: {e}")
            return []
    
    def delete_playlist(self, guild_id: int, user_id: int, playlist_name: str) -> bool:
        """Delete a user playlist"""
        try:
            self.cursor.execute('''
            DELETE FROM user_playlists
            WHERE guild_id = ? AND user_id = ? AND playlist_name = ?
            ''', (guild_id, user_id, playlist_name))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete playlist: {e}")
            return False
    
    # Guild Settings Methods
    def get_guild_settings(self, guild_id: int) -> Dict:
        """Get guild settings"""
        try:
            self.cursor.execute('''
            SELECT default_volume, default_filter, auto_disconnect
            FROM guild_settings
            WHERE guild_id = ?
            ''', (guild_id,))
            
            row = self.cursor.fetchone()
            if row:
                return {
                    'default_volume': row[0],
                    'default_filter': row[1],
                    'auto_disconnect': bool(row[2])
                }
            else:
                # Return defaults
                return {
                    'default_volume': 100,
                    'default_filter': None,
                    'auto_disconnect': True
                }
        except Exception as e:
            logger.error(f"Failed to get guild settings: {e}")
            return {'default_volume': 100, 'default_filter': None, 'auto_disconnect': True}
    
    def update_guild_settings(self, guild_id: int, **kwargs):
        """Update guild settings"""
        try:
            # Insert or update
            self.cursor.execute('''
            INSERT INTO guild_settings (guild_id, default_volume, default_filter, auto_disconnect, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id) 
            DO UPDATE SET 
                default_volume = COALESCE(excluded.default_volume, guild_settings.default_volume),
                default_filter = COALESCE(excluded.default_filter, guild_settings.default_filter),
                auto_disconnect = COALESCE(excluded.auto_disconnect, guild_settings.auto_disconnect),
                updated_at = CURRENT_TIMESTAMP
            ''', (
                guild_id,
                kwargs.get('default_volume'),
                kwargs.get('default_filter'),
                kwargs.get('auto_disconnect')
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to update guild settings: {e}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
