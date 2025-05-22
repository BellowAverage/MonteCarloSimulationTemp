"""
Data fetcher module for baseball statistics from Baseball-Reference.com
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseballDataFetcher:
    """Class to fetch baseball statistics from Baseball-Reference.com"""
    
    def __init__(self):
        self.base_url = "https://www.baseball-reference.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """Make HTTP request with error handling and rate limiting"""
        try:
            # Rate limiting
            time.sleep(3)  # Be polite to the server
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None

    def get_team_stats(self, team: str, year: int) -> Optional[pd.DataFrame]:
        """Fetch team statistics for a given year"""
        url = f"{self.base_url}/teams/{team}/{year}.shtml"
        soup = self._make_request(url)
        if not soup:
            return None
        
        try:
            # Find team stats table
            team_stats = pd.read_html(str(soup.find('table', {'id': 'team_batting'})))[0]
            return team_stats
        except Exception as e:
            logger.error(f"Error parsing team stats: {e}")
            return None

    def get_player_stats(self, player_id: str) -> Optional[pd.DataFrame]:
        """Fetch player statistics"""
        url = f"{self.base_url}/players/{player_id[0]}/{player_id}.shtml"
        soup = self._make_request(url)
        if not soup:
            return None
        
        try:
            # Find player batting stats table
            batting_stats = pd.read_html(str(soup.find('table', {'id': 'batting_standard'})))[0]
            return batting_stats
        except Exception as e:
            logger.error(f"Error parsing player stats: {e}")
            return None

    def get_schedule(self, team: str, year: int) -> Optional[pd.DataFrame]:
        """Fetch team schedule for a given year"""
        url = f"{self.base_url}/teams/{team}/{year}-schedule-scores.shtml"
        soup = self._make_request(url)
        if not soup:
            return None
        
        try:
            # Find schedule table
            schedule = pd.read_html(str(soup.find('table', {'id': 'team_schedule'})))[0]
            return schedule
        except Exception as e:
            logger.error(f"Error parsing schedule: {e}")
            return None

    def get_roster(self, team: str, year: int) -> Optional[pd.DataFrame]:
        """Fetch team roster for a given year"""
        url = f"{self.base_url}/teams/{team}/{year}-roster.shtml"
        soup = self._make_request(url)
        if not soup:
            return None
        
        try:
            # Find roster table
            roster = pd.read_html(str(soup.find('table', {'id': 'roster'})))[0]
            return roster
        except Exception as e:
            logger.error(f"Error parsing roster: {e}")
            return None 