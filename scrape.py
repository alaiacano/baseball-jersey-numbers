from BeautifulSoup import BeautifulSoup
import urllib2
import re
import os
import csv
import multiprocessing
import collections
from os.path import join as join_path


class Scraper(object):
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir

        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)

    def _load_from_cache(self, cache_file):
        """
        Loads a file from the cache directory or raises an exception.
        """
        try:
            page = open(cache_file, 'r').read()
            return page
        except:
            # file doesn't exist. make the containing directory
            # and exit with an exception
            file_dir = "/".join(cache_file.split('/')[:-1])
            os.path.mkdir(file_dir)
            raise Exception("No cached file at " % cache_file)

    def _download_url(self, url, cache_file, overwrite=False):
        """
        Pulls a URL and caches it.
        """
        if overwrite == False:
            try:
                page = self._load_from_cache(cache_file)
                return page
            except:
                pass
        print "Loading page from", url

        cache_dir = "/".join(cache_file.split("/")[:-1])
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        page = urllib2.urlopen(url).read()
        open(cache_file, 'wb').write(page)
        return page

    def get_players(self, letter):
        url = "http://www.baseball-reference.com/players/%s/" % letter

        cache_file = join_path(self.cache_dir, 'letters', letter)

        page = self._download_url(url, cache_file)

        soup = BeautifulSoup(page)
        links = soup.findAll('a')

        # just the player links.
        regex = re.compile(r'/players/%s/' % letter)
        links = [l for l in links if regex.search(l['href']) is not None]
        return links

    def parse_player(self, player_url):
        if player_url[:4] != "href":
            player_url = "http://www.baseball-reference.com" + player_url
        player_file = player_url.split("/")[-1]
        cache_file = join_path(self.cache_dir, 'players', player_file)
        page = self._download_url(player_url, cache_file)

        soup = BeautifulSoup(page)

        # Extracting the number is a pain in the ass if they've played for
        # multiple teams with different numbers. Here, I'll get the number they
        # had on the most teams (not necessarily the most years).
        try:
            number_soup = soup.findAll('div', attrs={'class':'uni_circle_white'})
            if len(number_soup) == 1:
                # they only played for one team and had one number. easy.
                number = int(number_soup[0].text)
            else:
                # count how many times they've had each number, return the max
                number_dict = collections.defaultdict(int)
                for team in number_soup:
                    team_number = int(team.text)
                    number_dict[team_number] += 1

                if len(number_dict.keys()) == 1:
                    # They've played for multiple teams, but only had one number
                    number = number_dict.keys()[0]
                else:
                    # multiple teams and/or multiple numbers. Return the one
                    # that appears the most
                    max_val = max(number_dict.values())
                    number = [k for k, v in number_dict.iteritems() if v == max_val][0]
        except:
            number = -1
        try:
            name = soup.findAll('span', attrs={'class': 'bold_text xx_large_text'})[0].text
        except:
            name = ""

        try:
            hitting_table = soup.find('table', attrs={'id': 'batting_standard'})
            stats = hitting_table.find('tr', attrs={'class': ' stat_total'}).findAll('td')
            pa = int(stats[2].text)
            ba = float(stats[14].text)
        except:
            pa = 0
            ba = 0.0

        # flag for if they're a pitcher or not.
        position = self._get_position(soup)
        if re.search('pitcher', position, re.IGNORECASE):
            is_pitcher = 1
        else:
            is_pitcher = 0
        return name, number, pa, ba, is_pitcher

    def _get_position(self, soup):
        """
        Figures out if the player is a pitcher or not. Returns 1 / 0
        """
        try:
            infobox = soup.find('div', attrs={'id': 'info_box'})
            pos = [i.text for i in infobox.findAll('p') if re.search("Position", i.text)][0]
            position = pos.split(':')[1][:pos.split(':')[1].index('Bats')].strip()
            return position
        except:
            return "-1"


def gather_letter(letter):
    """
    Gathers all of the information about players whose last names start with
    the provided letter and writes it to cache/data/[letter]
    """
    S = Scraper()

    output_file = "cache/data/" + letter
    fout = csv.writer(open(output_file, 'wb'))

    players = S.get_players(letter)
    for player in players:
        try:
            name, number, pa, ba, is_pitcher = S.parse_player(player['href'])
            print name, number, pa, ba, is_pitcher
            fout.writerow([name, number, pa, ba, is_pitcher])
        except UnicodeEncodeError:
            continue
    del(fout)

if __name__ == "__main__":

    alphabet = [i for i in "abcdefghijklmnopqrstuvwxyz"]
    if not os.path.exists('cache/data'):
        os.mkdir('cache/data')
    else:
        os.system('rm -f cache/data/*')

    P = multiprocessing.Pool(4)
    P.map(gather_letter, alphabet)

    # write the header to a file and then combine all of them together
    os.system('echo "name,number,plate_appearances,batting_average,is_pitcher" > combined_data.csv')
    os.system('cat cache/data/* >> combined_data.csv')
