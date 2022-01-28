from enum import Flag
from heapq import heapify
import re
import os
from urllib.parse import urlparse
import time
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
from collections import Counter

# To solve problem 1
all_unique_urls = set()

# To solve problem 2
longest_url = []
longest_url_count = -1

# To solve problem 3
common_words = []
all_word_freq = {}
stopword_list = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as",
             "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
             "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
             "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
             "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself",
             "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
             "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off",
             "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
             "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that",
             "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they",
             "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up",
             "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
             "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
             "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
             "yourselves"]

# To solve problem 4
sub_urls = set()
all_subdomains = {}


def scraper(url, resp):
    links = extract_next_links(url, resp)

    res = [link for link in links if is_valid(link)]

    return res


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    global longest_url, longest_url_count, all_unique_urls, all_word_freq, sub_urls
    hyperlinks = []

    # ------------------ 1. update the report -------------------------------------------------------

    if 200 <= resp.status < 300 and resp.status != 204:  # since status code 204 is No Content
        if resp.raw_response is None:
            return hyperlinks
        if not is_valid(resp.raw_response.url):
            return hyperlinks
        if resp.raw_response.url in all_unique_urls:
            return hyperlinks
        if resp.raw_response.content == None or len(resp.raw_response.content) < 1:
            return hyperlinks
        if "Apache/2.4.6" in resp.raw_response.text:
            return hyperlinks
        
        raw = BeautifulSoup(resp.raw_response.content, 'html.parser').get_text()
        content = raw.lower()
        token_list = tokenize(content)
        cur_word_freq = computeWordFrequencies(token_list)
        count = len(token_list)
        if lowInformation(cur_word_freq, count):
            return hyperlinks
        # To solve problem 1
        all_unique_urls.add(urldefrag(resp.raw_response.url).url)

        # To solve problem 2
        if count > longest_url_count:
            longest_url_count = count
            longest_url = [resp.raw_response.url]
        elif count == longest_url_count:
            longest_url.append(resp.raw_response.url)

        # To solve problem 3
        all_word_freq.update(cur_word_freq)


        # To solve problem 4
        all_subdomains = {}

        if '.ics.uci.edu/' in resp.raw_response.url:
            sub_urls.add(urldefrag(resp.raw_response.url).url)

            for cur_url in sub_urls:
                index = cur_url.find('.ics.uci.edu/')

                subdomain_name = cur_url[:index + 13]

                if 'https://' in subdomain_name:
                    subdomain_name.replace('https://', '')
                if 'http://' in subdomain_name:
                    subdomain_name.replace('http://', '')

                if subdomain_name in all_subdomains:
                    all_subdomains[subdomain_name] = all_subdomains[subdomain_name] + 1
                else:
                    all_subdomains[subdomain_name] = 1

        # Refresh the report file
        if len(all_unique_urls) % 10 == 0:
            with open('report.txt', 'w') as output_file:
                # p1
                output_file.write('The number of unique url: {}\n\n'.format(len(all_unique_urls)))
                
                # p2
                output_file.write('Longest url: {}, with the number of words: {}\n\n'.format(longest_url, longest_url_count))

                # p3
                output_file.write('50 most common words:\n')
                common_words = Counter(all_word_freq)
                top_50_words = common_words.most_common(50)
                for i in range(50):
                    output_file.write('{}\t'.format(top_50_words[i][0]))
                    if i != 0 and i % 5 == 0:
                        output_file.write('\n')
                    i = i + 1
                output_file.write('\n\n')

                # p4
                output_file.write('Sub-domains and number of pages:\n')
                for subdomain, pages in all_subdomains.items():
                    output_file.write('{}, {}\n'.format(subdomain, pages))

        # ------------------ 2. find all hyperlinks -----------------------------------------------------

        full_text = resp.raw_response.text

        i = 0
        while (i + 9 < len(full_text)):
            # print('i = ', i)
            if full_text[i: i + 9] == "<a href=\"":
                hyperlink = ""
                j = i + 9
                while full_text[j] != '\"':
                    hyperlink = hyperlink + full_text[j]
                    j = j + 1

                if len(hyperlink) > 1:

                    if hyperlink[0] == '/' and hyperlink[1] == '/':
                        hyperlink = 'https:' + hyperlink
                    elif hyperlink[0] == '/' and hyperlink[1] == '~':
                        hyperlink = getdomain(resp.raw_response.url) + hyperlink
                    elif hyperlink[0] == '/':
                        hyperlink = resp.raw_response.url + hyperlink


                    if is_valid(hyperlink):
                        hyperlinks.append(hyperlink)

                i = j

            i = i + 1

    return hyperlinks


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        # case 1
        if url == None or len(url) < 1 or url == '#':
            return False

        pattern = re.compile("(/[\w\d]+).+?\\1")
        not_matched = not re.search(pattern, url)
        if not not_matched:
            return False

        # case 2
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # case 3
        flag = not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        if flag == False:
            return False

        # case 4
        sub_strings = ['ics.uci.edu', 'cs.uci.edu', 'informatics.uci.edu', 'stat.uci.edu',
                       'today.uci.edu/department/information_computer_sciences']
        flag = False
        for sub_str in sub_strings:
            if sub_str in url:
                flag = True
                break
        if flag == False:
            return False

        # case 5: avoid infinite loop use regex to analyze


        # case 6
        blacklist = ['?replytocom=', '/pdf/', "#comment-"]
        for item in blacklist:
            if item in url:
                return False

        return True


    except TypeError:
        print("TypeError for ", parsed)
        raise

def lowInformation(dic, length):
    if (len(dic) < 50):
        return True
    else:
        top15 = 0
        counter = Counter(dic)
        most_common_words = counter.most_common(15)
        for i in range(5):
            top15 += most_common_words[i][1]
        if ((top15 / length) > 0.6):
            return True
        else:
            return False

# use nltk tokenize content only considering more than 2 characters
def tokenize(content):
    Tokenizer = RegexpTokenizer('[a-z\']{2,}')
    tokens = Tokenizer.tokenize(content)
    return tokens


def computeWordFrequencies(token_list):
    freq = {}
    for word in token_list:
        if word not in stopword_list:
            if word in freq:
                freq[word] = freq[word] + 1
            else:
                freq[word] = 1

    return freq

def getdomain(url):
    cot = 0
    for i in range(len(url)):
        if url[i] == "/":
            cot += 1
        if cot == 3:
            return url[:i]







