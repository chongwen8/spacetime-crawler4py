from enum import Flag
from heapq import heapify
import re
import os
from urllib.parse import urlparse
import time
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

# To solve problem 1
all_unique_urls = set()

# To solve problem 2
longest_url = []
longest_url_count = -1

# To solve problem 3
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
        
        # To solve problem 1
        all_unique_urls.add(urldefrag(resp.raw_response.url).url)

        # To solve problem 2
        content = BeautifulSoup(resp.raw_response.content, 'html.parser').get_text()
        with open('_temp_token_list.txt', 'w') as file:
            file.write(content)
        token_list = tokenize('_temp_token_list.txt')
        count = len(token_list)
        if count > longest_url_count:
            longest_url_count = count
            longest_url = [resp.raw_response.url]
        elif count == longest_url_count:
            longest_url.append(resp.raw_response.url)

        # To solve problem 3
        cur_word_freq = computeWordFrequencies(token_list)
        for word, freq in cur_word_freq.items():
            if word not in stopword_list:
                if word in all_word_freq:
                    all_word_freq[word] += freq
                else:
                    all_word_freq[word] = freq

        # To solve problem 4
        all_subdomains = {}

        if bool(re.search(".ics.uci.edu/", resp.raw_response.url)):
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
                i = 0
                for item in sorted(all_word_freq.items(), key=lambda item: item[1], reverse=True)[:50]:
                    output_file.write('{}\t'.format(item))
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
        links = []

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
                    if hyperlink[0] == '/' and hyperlink[1] != '/':
                        hyperlink = resp.raw_response.url + hyperlink

                    if hyperlink[0] == '/' and hyperlink[1] == '/':
                        hyperlink = 'https:' + hyperlink

                    if is_valid(hyperlink):
                        links.append(hyperlink)

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
        pattern = re.compile("(/[\w\d]+).+?\1")
        duplication = re.findall(pattern, url)
        if (len(duplication) > 3):
            return False


        # case 6
        blacklist = ['?replytocom=', '/pdf/']
        for item in blacklist:
            if item in url:
                return False

        return True


    except TypeError:
        print("TypeError for ", parsed)
        raise


def tokenize(TextFilePath):
    '''
        runtime complexity: O(L), linear,
        where L is the length of whole text file
    '''
    token_list = []

    file = open(TextFilePath, encoding='utf-8')
    for line in file:
        line = line.lower()

        n = len(line)
        for i in range(n - 1, -1, -1):
            if not ('a' <= line[i] <= 'z' or 'A' <= line[i] <= 'Z' or '0' <= line[i] <= '9'):
                if line[i] != ' ':
                    line = line[:i] + ' ' + line[i + 1:]

        for word in line.split(' '):
            if word != '\n' and word != ' ' and len(word) > 0:
                token_list.append(word)

    return token_list


def computeWordFrequencies(token_list):
    '''
        runtime complexity: O(n*log(n')),
        where n is the number of words in file, n' is the number of unique words in file
    '''
    map = {}

    for word in token_list:
        if word in map:
            map[word] = map[word] + 1
        else:
            map[word] = 1

    return map


