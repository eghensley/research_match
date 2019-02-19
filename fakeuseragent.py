#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: eric.hensley@ibm.com
"""

import random

class UserAgent:
    def __init__(self):
        """ Provide random user agent header to allow scraping without provoking an IP block. """

        self.agents = ['Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US);',
         'Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)',
         'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB7.4; InfoPath.2; SV1; .NET CLR 3.3.69573; WOW64; en-US)',
         'Opera/9.80 (X11; Linux i686; U; ru) Presto/2.8.131 Version/11.11',
         'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13',
         'Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11',
         'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1',
         'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1',
         'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25']
        self.secure_random = random.SystemRandom()   
        
        
    def random(self):
        """ Shuffle headers and return random. """
        
        return(self.secure_random.choice(self.agents))