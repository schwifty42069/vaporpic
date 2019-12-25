import configparser
import json
import os
import sys

import requests
from bs4 import BeautifulSoup as Soup
from tqdm import tqdm

config = configparser.RawConfigParser()
config.read("config/config.properties")


class VidnodeApi(object):
    def __init__(self, media_type, title, **kwargs):
        super().__init__()
        self.root_url = "https://gowatchseries.fm/"
        self.media_type = media_type
        self.title = title
        if self.media_type == "tvod":
            assert "s" in kwargs.keys() and "e" in kwargs.keys()
            self.season = kwargs.get("s")
            self.episode = kwargs.get("e")

    def assemble_search_url(self):
        search_url = self.root_url + "search.html?keyword={}".format(self.title)
        search_soup = Soup(requests.get(search_url).text, 'html.parser')
        words = self.title.split()
        if self.media_type == "tvod":
            for a in search_soup.findAll("a"):
                try:
                    for w in words:
                        if w.lower() == "the" or w.lower() == "and":
                            continue
                        if w.lower() in a['href'] and "season" in a['href'] and self.season in a['href']:
                            return self.root_url + a['href'].split("/info/")[1]
                except KeyError:
                    continue
        elif self.media_type == "movie":
            search_str = ""
            if len(words) > 1:
                for w in words:
                    search_str += w + "-"
            else:
                search_str = words[0]
            for a in search_soup.findAll("a"):
                try:
                    if search_str[len(search_str) - 1] == "-":
                        search_str = search_str[:len(search_str) - 2]
                    if search_str.lower() in a['href']:
                        return self.root_url + a['href'].split("/info/")[1]
                except KeyError:
                    continue

    def assemble_media_url(self, search_url):
        if self.media_type == "tvod":
            return search_url + "-episode-{}".format(self.episode)
        elif self.media_type == "movie":
            if "Page not found" in requests.get(search_url + "-episode-1").text:
                return search_url + "-episode-0"
            else:
                return search_url + "-episode-1"

    @staticmethod
    def scrape_final_links(link, bot_mode):
        browser_link = ''
        hotlink_location = ''
        link_dict = {}
        bsoup = Soup(requests.get(link).text, 'html.parser')
        for iframe in bsoup.findAll("iframe"):
            if "vidnode" in iframe['src']:
                browser_link = "https:" + iframe['src']
        if len(browser_link) == 0:
            return
        bsoup_hll = Soup(requests.get(browser_link).text, 'html.parser')
        for d in bsoup_hll.findAll("script"):
            if "download" in str(d):
                if bot_mode:
                    return str(d).split("window.open(")[1].strip("\n").strip(" ").split(",")[0].strip("\"")
                hotlink_location = str(d).split("window.open(")[1].strip("\n").strip(" ").split(",")[0].strip("\"")
        dl_links = []
        bsoup_d = Soup(requests.get(hotlink_location).text, 'html.parser')
        for a in bsoup_d.findAll("a"):
            if "cdn" in a['href']:
                dl_links.append(a['href'])
        dl_quality_dict = {}
        for link in dl_links:
            if "360P" in link:
                dl_quality_dict.update({"360p": link})
            if "480P" in link:
                dl_quality_dict.update({"480p": link})
            if "720P" in link:
                dl_quality_dict.update({"720p": link})
            if "1080P" in link:
                dl_quality_dict.update({"1080p": link})
            else:
                dl_quality_dict.update({"Original": link})
        link_dict.update({"browser_link": browser_link, "hotlinks": dl_quality_dict})
        return link_dict


class WatchEpisodeApi(object):
    def __init__(self, title, season, episode):
        self.root_url = "https://www.watchepisodes4.com"
        self.season = season
        self.episode = episode
        self.title = title.replace("\'", "-")
        self.title_words = self.title.split()
        self.formatted_title = ''
        for word in self.title_words:
            self.formatted_title += word + "-"
        self.formatted_search = "{}season-{}-episode-{}".format(self.formatted_title, self.season, self.episode)
        self.formatted_url = "{}/{}".format(self.root_url, self.formatted_title)

    def fetch_ref_link(self):
        title = ''
        if self.formatted_title[len(self.formatted_title) - 1] == "-":
            title = self.formatted_title[:len(self.formatted_title) - 1]
        bsoup = Soup(requests.get("{}/{}".format(self.root_url, title)).text, 'html.parser')
        for a in bsoup.findAll("a"):
            try:
                if "person" not in a['href'] and "profile" not in a['href'] and self.formatted_search.lower() in \
                        a['href']:
                    return a['href']
            except KeyError:
                continue

    def build_source_link_list(self, ref_link):
        link_list = []
        bsoup = Soup(requests.get(ref_link).text, 'html.parser')
        for a in bsoup.findAll("a"):
            try:
                if "person" not in a['href'] and "profile" not in a['href'] and self.formatted_search.lower() \
                        in a['href'] and a['href'] not in link_list:
                    link_list.append(a['href'])
            except KeyError:
                continue
        source_links = []
        print("\nFinding source links...\n")
        bar = tqdm(total=len(link_list))
        try:
            for link in link_list:
                bar.update(1)
                bsoup2 = Soup(requests.get(link).text, 'html.parser')
                actual_link = bsoup2.find("a", {"class": "detail-w-button act_watchlink2"})['data-actuallink']
                if "clipwatching" in actual_link and actual_link not in source_links or "videobin" in actual_link \
                        and actual_link not in source_links:
                    source_links.append(actual_link)
                else:
                    continue
            return source_links
        except TypeError:
            return -1

    @staticmethod
    def scrape_hotlinks(source_links):
        hotlinks = []
        print("\nFinding hotlinks...\n")
        bar = tqdm(total=len(source_links))
        for link in source_links:
            bsoup = Soup(requests.get(link).text, 'html.parser')
            if "clipwatching" in link:
                for s in bsoup.findAll("script"):
                    if "#hola" in s.text and "player" in s.text:
                        if s.text.split("sources: [{src: ")[1].split(",")[0].strip("\"") not in hotlinks:
                            hotlinks.append(s.text.split("sources: [{src: ")[1].split(",")[0].strip("\""))
            if "videobin" in link:
                for s in bsoup.findAll("script"):
                    if 'var player = new Clappr.Player({' in s.text:
                        if s.text.split('[')[1].split(',"')[1].split('"]')[0] not in hotlinks:
                            hotlinks.append(s.text.split('[')[1].split(',"')[1].split('"]')[0])
            bar.update(1)
        return hotlinks


class SimpleMovieApi(object):
    def __init__(self, title):
        self.title = title
        self.imdb = ImdbQuery(title)
        self.imdb.scrape_title_codes()
        self.title_code = self.imdb.title_codes[0]
        self.url = "https://api.hdv.fun/l1?imdb={}&ip=128.6.37.19".format(self.title_code)

    def check_for_movie(self):
        movie_json = json.loads(requests.post(self.url).text)
        try:
            return {"src": movie_json[0]['src'][0]['src'], "quality": movie_json[0]['src'][0]['res']}
        except IndexError:
            return -1


class ImdbQuery(object):
    def __init__(self, search):
        self.search = search
        self.search_words = self.search.split()
        self.formatted_search = self.format_search_words()
        self.search_address = "https://www.imdb.com/find?ref_=nv_sr_fn&q={}&s=all".format(self.formatted_search)
        self.titles = []
        self.title_codes = []

    def format_search_words(self):
        formatted_words = ''
        for word in self.search_words:
            formatted_words += word + "+"
        return formatted_words[:len(formatted_words) - 1]

    def scrape_title_codes(self):
        req = requests.get(self.search_address).text
        results = Soup(req, 'html.parser').findAll("td", {"class": "result_text"})
        for result in results:
            self.title_codes.append(str(result.parent).split("href=")[1].split(">")[0].strip("\"").split("/")[2])
        return

    def scrape_media_titles(self):
        req = requests.get(self.search_address).text
        results = Soup(req, 'html.parser').findAll("td", {"class": "result_text"})
        for result in results:
            self.titles.append("{}. {}".format(results.index(result) + 1, str(result.contents[1]).split(">")[1]
                                               .split("</")[0] + result.contents[2]))
        return

    @staticmethod
    def get_series_seasons(title_code):
        series_page = "https://www.imdb.com/title/{}/episodes?season=1&ref_=tt_eps_sn_1".format(title_code)
        bsoup = Soup(requests.get(series_page).text, 'html.parser')
        num = 0
        try:
            for i in bsoup.find("select", id="bySeason").contents:
                if "<option value=" in str(i):
                    if num < int(str(i).split("<option value=")[1].split(">")[0].strip("\"")):
                        num = int(str(i).split("<option value=")[1].split(">")[0].strip("\""))
            return num
        except AttributeError:
            return 0

    @staticmethod
    def get_season_episodes(title_code, season):
        season_series_page = "https://www.imdb.com/title/{}/episodes?season={}&ref_=tt_eps_sn_1" \
            .format(title_code, season)
        bsoup = Soup(requests.get(season_series_page).text, 'html.parser')
        num = 0
        for d in bsoup.findAll("div"):
            if "S" in d.text and "Ep" in d.text and "\n" not in d.text:
                if num < int(d.text.split("Ep")[1]):
                    num = int(d.text.split("Ep")[1])
        return num

    @staticmethod
    def scrape_episode_titles(title_code, season):
        titles = []
        season_series_page = "https://www.imdb.com/title/{}/episodes?season={}&ref_=tt_eps_sn_1" \
            .format(title_code, season)
        bsoup = Soup(requests.get(season_series_page).text, 'html.parser')
        x = 0
        for s in bsoup.findAll("strong"):
            if "title=" in str(s):
                x += 1
                titles.append("{}. {}".format(x, str(s).split("title=\"")[1].split("\">")[0]))
        return titles


class M3UWriter(object):
    def __init__(self, link, title):
        self.link = link
        self.raw_title = title
        self.formatted_title = self.format_title(self.raw_title)
        self.write_dir = config.get('output', 'dir') + "/{}.m3u".format(self.formatted_title)

    @staticmethod
    def format_title(title):
        title_words = title.split()
        formatted_title = ""
        for word in title_words:
            if title_words.index(word) != (len(title_words) - 1):
                formatted_title += "{}_".format(word)
            else:
                formatted_title += word
        return formatted_title

    def initialize_m3u_file(self):
        if os.path.exists(self.write_dir):
            os.remove(self.write_dir)
            with open(self.write_dir, "w") as writer:
                writer.write('')
                writer.close()
        else:
            with open(self.write_dir, "w") as writer:
                writer.write('')
                writer.close()

    def write_m3u_chunk(self):
        print("\nWriting links for {} to m3u...\n".format(self.raw_title))
        with open(self.write_dir, "a") as writer:
            writer.write("#EXTM3U\n")
            writer.write("#EXTINF: -1,{}\n".format(self.formatted_title))
            writer.write("{}\n\n".format(self.link))
            writer.close()


# Main function for demo of API
def main():
    while True:
        try:
            try:
                media_type = input("\nSelect media type:\n\n1. Movie\n\n2. TV\n\n")
                if media_type == "2":
                    title = input("\nTitle:\n\n")
                    media = "tvod"
                    imdb_query = ImdbQuery(title)
                    imdb_query.scrape_title_codes()
                    if len(imdb_query.title_codes) == 0:
                        print("\nNo imdb title found!\n")
                        continue
                    title_code = imdb_query.title_codes[0]
                    seasons = imdb_query.get_series_seasons(title_code)
                    season = (input("\nSeason: (1 - {})\n\n".format(seasons)))
                    episode_titles = imdb_query.scrape_episode_titles(title_code, season)
                    print("\nEpisodes:\n")
                    for e in episode_titles:
                        print("\n{}".format(e))
                    episode = input("\nEpisode:\n\n")
                    api = int(input("\nSelect Primary API:\n\n1. WatchEpisode API (multi-source)\n\n2. Vidnode API\n\n"))
                    if "." in title:
                        words = title.split(".")
                        title = ""
                        for w in words:
                            title += "{} ".format(w)

                    if api == 1:
                        print("\nTrying WatchEpisode API...\n")
                        we = WatchEpisodeApi(title, season, episode)
                        ref_link = we.fetch_ref_link()
                        source_list = we.build_source_link_list(ref_link)
                        hotlinks = we.scrape_hotlinks(source_list)
                        if len(hotlinks) != 0:
                            for link in hotlinks:
                                m3u_writer = M3UWriter(link, "{}_{}_{}".format(title, season, episode))
                                m3u_writer.write_m3u_chunk()
                        else:
                            print("\nTrying Vidnode API...\n")
                            key_list = []
                            va = VidnodeApi(media, title, s=season, e=episode)
                            search = va.assemble_search_url()
                            media_url = va.assemble_media_url(search)
                            link_dict = va.scrape_final_links(media_url, False)
                            if len(link_dict['hotlinks']) != 0:
                                print("\nAvailable Qualities:\n\n")
                                try:
                                    for key in link_dict['hotlinks'].keys():
                                        key_list.append(key)
                                    for key in key_list:
                                        print("{}. {}\n".format(key_list.index(key), key))
                                    q_sel = int(input("\nSelect quality:\n\n"))
                                    link = link_dict['hotlinks'][key_list[q_sel]]
                                    m3u_writer = M3UWriter(link, "{}_{}_{}".format(title, season, episode))
                                    m3u_writer.write_m3u_chunk()
                                except TypeError:
                                    print("\nNo links were found!\n")
                                    continue
                            else:
                                print("\nNo links found!\n")
                                continue
                    elif api == 2:
                        print("\nTrying Vidnode API...\n")
                        key_list = []
                        va = VidnodeApi(media, title, s=season, e=episode)
                        search = va.assemble_search_url()
                        media_url = va.assemble_media_url(search)
                        link_dict = va.scrape_final_links(media_url, False)
                        if len(link_dict['hotlinks']) != 0:
                            print("\nAvailable Qualities:\n\n")
                            try:
                                for key in link_dict['hotlinks'].keys():
                                    key_list.append(key)
                                for key in key_list:
                                    print("{}. {}\n".format(key_list.index(key), key))
                                q_sel = int(input("\nSelect quality:\n\n"))
                                link = link_dict['hotlinks'][key_list[q_sel]]
                                m3u_writer = M3UWriter(link, "{} {} {}".format(title, season, episode))
                                m3u_writer.write_m3u_chunk()
                            except TypeError:
                                print("\nNo links were found!\n")
                                continue
                        else:
                            print("\nNo links found!\n")
                            print("\nTrying WatchEpisode API...\n")
                            we = WatchEpisodeApi(title, season, episode)
                            ref_link = we.fetch_ref_link()
                            source_list = we.build_source_link_list(ref_link)
                            hotlinks = we.scrape_hotlinks(source_list)
                            if len(hotlinks) != 0:
                                for link in hotlinks:
                                    m3u_writer = M3UWriter(link, "{}_{}_{}".format(title, season, episode))
                                    m3u_writer.write_m3u_chunk()
                            else:
                                print("\nNo links found!\n")
                                continue
                elif media_type == "q":
                    print("\nGoodbye!\n")
                    sys.exit()

                elif media_type == "1":
                    title = input("\nTitle:\n\n")
                    if "." in title:
                        words = title.split(".")
                        title = ""
                        for w in words:
                            title += "{} ".format(w)
                    media = "movie"
                    api = int(input("\nSelect Primary API:\n\n1. SimpleMovie API (m3u8)\n\n2. Vidnode API (mp4)\n\n"))
                    if api == 1:
                        print("\nTrying Simple Movie API..\n")
                        sma = SimpleMovieApi(title)
                        result = sma.check_for_movie()
                        if result != -1:
                            m3u_writer = M3UWriter(result['src'], "{}".format(title))
                            m3u_writer.write_m3u_chunk()
                            continue
                        else:
                            print("Simple movie API failed, trying Vidnode API..\n")
                            va = VidnodeApi(media, title)
                            search = va.assemble_search_url()
                            media_url = va.assemble_media_url(search)
                            link_dict = va.scrape_final_links(media_url, False)
                            key_list = []
                            print("\nAvailable Qualities:\n\n")
                            try:
                                for key in link_dict['hotlinks'].keys():
                                    key_list.append(key)
                                for key in key_list:
                                    print("{}. {}\n".format(key_list.index(key), key))
                                q_sel = int(input("\nSelect quality:\n\n"))
                                link = link_dict['hotlinks'][key_list[q_sel]]
                                m3u_writer = M3UWriter(link, "{}".format(title))
                                m3u_writer.write_m3u_chunk()
                            except TypeError:
                                print("\nNo links were found!\n")
                                continue
                    elif api == 2:
                        print("\nTrying Vidnode API..\n")
                        va = VidnodeApi(media, title)
                        search = va.assemble_search_url()
                        media_url = va.assemble_media_url(search)
                        link_dict = va.scrape_final_links(media_url, False)
                        key_list = []
                        print("\nAvailable Qualities:\n\n")
                        try:
                            for key in link_dict['hotlinks'].keys():
                                key_list.append(key)
                            for key in key_list:
                                print("{}. {}\n".format(key_list.index(key), key))
                            q_sel = int(input("\nSelect quality:\n\n"))
                            link = link_dict['hotlinks'][key_list[q_sel]]
                            m3u_writer = M3UWriter(link, "{}".format(title))
                            m3u_writer.write_m3u_chunk()
                        except TypeError:
                            print("\nVidnode API failed, trying Simple Movie API..\n")
                            sma = SimpleMovieApi(title)
                            result = sma.check_for_movie()
                            if result != -1:
                                m3u_writer = M3UWriter(result['src'], title)
                                m3u_writer.write_m3u_chunk()
                                continue
                            else:
                                print("\nNo links were found!\n")

            except TypeError or AttributeError or IndexError:
                print("\nNo links found!\n")
        except KeyboardInterrupt:
            os.system('cls' if os.name == 'nt' else 'clear')
            continue


if __name__ == "__main__":
    main()
