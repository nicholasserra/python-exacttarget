import urllib
import urllib2
import sys

try:
    from lxml import etree
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
        except ImportError:
            try:
                #normal cElementTree install
                import cElementTree as etree
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                except ImportError:
                    print("Failed to import ElementTree from any known place")

__version__ = '0.0.1'

ENDPOINTS = {
    'default': 'https://api.dc1.exacttarget.com/integrate.aspx',
    'S4': 'https://api.s4.exacttarget.com/integrate.aspx',
    'S6': 'https://api.s6.exacttarget.com/integrate.aspx',
}

class ExactTargetError(Exception):
    pass

class ConnectionError(Exception):
    pass

class ExactTargetConnection(object):
    def __init__(self, username, password, timeout=250, endpoint='default'):
        '''
        ExactTarget XML API class
        Default endpoint is used. Use S4 or S6 depending on your account.
        '''

        self.api_url = ENDPOINTS[endpoint]
        self.username = username
        self.password = password
        self.error = ''
        self.timeout = timeout

    def account_info(self):
        '''
        Retrieve account information.
        '''

        data = """
        <system_name>accountinfo</system_name>
        <action>retrieve_attrbs</action>
        <search_type/>
        <search_value/>
        """

        xml_response = self.make_call(data)

        attributes = []
        for attribute in xml_response.findall('.//attribute'):
            a = {}
            for node in attribute:
                if len(node) > 0:
                    c = []
                    for childnode in node:
                        item = {childnode.tag: childnode.text}
                        c.append(item)
                    a[node.tag] = c
                else:
                    a[node.tag] = node.text
            attributes.append(a)
        return attributes

    def subscriber_retrieve(self, subscriber_id):
        '''
        Retrieves a subscriber given subscriber's id
        '''
        data = """
        <system_name>subscriber</system_name>
        <action>retrieve</action>
        <search_type>subid</search_type>
        <search_value>%(subscriber_id)d</search_value>
        <search_value2></search_value2>
        <showChannelID></showChannelID>""" % {'subscriber_id': subscriber_id}

        xml_response = self.make_call(data)

        subscriber = xml_response.find('.//subscriber')
        s = {}
        for node in subscriber:
            s[node.tag] = node.text if node.text else ''

        return s

    def subscriber_add(self, list_id, email_address, full_name='', update=True):
        '''
        Add email address to a list

        Defaults to update True. If false, you cannot add someone already in the list.
        '''

        data = """
        <system_name>subscriber</system_name>
        <action>add</action>
        <search_type>listid</search_type>
        <search_value>%(list_id)d</search_value>
        <search_value2></search_value2>
        <values>
          <Email__Address><![CDATA[%(email_address)s]]></Email__Address>
          <status>active</status>
          <Full__Name><![CDATA[%(full_name)s]]></Full__Name>
          <ChannelMemberID></ChannelMemberID>
        </values>
        <update>%(update)s</update>""" % {'list_id': list_id, 'email_address': email_address, 'full_name': full_name, 'update': 'true' if update else 'false'}

        xml_response = self.make_call(data)
        subscriber_id = xml_response.find('.//subscriber_description')

        return subscriber_id.text if subscriber_id != None else None

    def subscriber_remove(self, list_id, email_address):
        '''
        Remove a subscriber from a list. Does not delete the subscriber globally.
        '''

        data = """
        <system_name>subscriber</system_name>
        <action>delete</action>
        <search_type>listid</search_type>
        <search_value>%(list_id)d</search_value>
        <search_value2><![CDATA[%(email_address)s]]></search_value2>""" % {'list_id': list_id, 'email_address': email_address}

        xml_response = self.make_call(data)

        return True if xml_response.find('.//subscriber_info') != None else False

    def subscriber_delete(self, subscriber_id):
        '''
        Delete a subscriber by subscriber id.
        '''

        data = """"
        <system_name>subscriber</system_name>
        <action>delete</action>
        <search_type>subid</search_type>
        <search_value>%(subscriber_id)d</search_value>
        <search_value2></search_value2>""" % {'subscriber_id': subscriber_id}

        xml_response = self.make_call(data)

        return True if xml_response.find('.//subscriber_info') != None else False

    def subscriber_unsubscribe(self, list_id, email_address, reason=''):
        '''
        Sets a subscriber in a list to not active, but keeps them in the list.
        '''

        data = """
        <system_name>subscriber</system_name>
        <action>edit</action>
        <search_type>listid</search_type>
        <search_value>%(list_id)d</search_value>
        <search_value2><![CDATA[%(email_address)s]]></search_value2>
        <values>
          <Email__Address><![CDATA[%(email_address)s]]></Email__Address>
          <status>unsub</status>
          <reason><![CDATA[%(reason)s]]></reason>
          <ChannelMemberID></ChannelMemberID>
        </values>""" % {'list_id': list_id, 'email_address': email_address, 'reason': reason}

        xml_response = self.make_call(data)

        return True if xml_response.find('.//subscriber_info') != None else False

    def subscriber_reactivate(self, list_id, email_address):
        '''
        Sets a subscriber in a list to active.
        '''

        data = """
        <system_name>subscriber</system_name>
        <action>edit</action>
        <search_type>listid</search_type>
        <search_value>%(list_id)d</search_value>
        <search_value2><![CDATA[%(email_address)s]]></search_value2>
        <values>
          <Email__Address><![CDATA[%(email_address)s]]></Email__Address>
          <status>active</status>
          <ChannelMemberID></ChannelMemberID>
        </values>""" % {'list_id': list_id, 'email_address': email_address}

        xml_response = self.make_call(data)

        return True if xml_response.find('.//subscriber_info') != None else False

    def subscriber_edit(self, subscriber_id, email_address, params=None):
        '''
        Edit a subscriber. Pass extra params form custom field.
        params = {'field': 'value'}
        '''
        
        custom_vals = ''
        if params:
            for k,v in params.items():
                node = '<%(key)s><![CDATA[%(value)s]]></%(key)s>' % {'key': k, 'value': v}
                custom_vals += node

        data = """
        <system_name>subscriber</system_name>
        <action>edit</action>
        <search_type>subid</search_type>
        <search_value>%(subscriber_id)d</search_value>
        <search_value2></search_value2>
        <values>
          <Email__Address><![CDATA[%(email_address)s]]></Email__Address>
          %(custom)s
          <ChannelMemberID></ChannelMemberID>
        </values>""" % {'subscriber_id': subscriber_id, 'email_address': email_address, 'custom': custom_vals}

        xml_response = self.make_call(data)

        return True if xml_response.find('.//subscriber_info') != None else False

    def master_unsub_list(self, start_date=None, end_date=None):
        '''
        grab the data from the master unsubscribed list
        dates are m/d/yyyy (8/1/2008)
        '''

        if start_date and end_date:

            #validate date ranges
            date_nodes = """
            <daterange>
              <startdate>%(startdate)s</startdate>
              <enddate>%(enddate)s</enddate>
            </daterange>""" % {'startdate': start_date, 'enddate': end_date}
        else:
            date_nodes = "<daterange/>"

        data = """
        <system_name>tracking</system_name>
        <action>retrieve</action>
        <sub_action>masterunsub</sub_action>
        <search_type/>
        <search_value/>
        %(daterange)s""" % {'daterange': date_nodes}

        xml_response = self.make_call(data)

        subscribers = []
        for subscriber in xml_response.findall('.//subscriber'):
            s = {
                'email_address': subscriber.find('email_address').text,
                'name': subscriber.find('name').text if subscriber.find('name') else '',
                'reason': subscriber.find('reason').text if subscriber.find('reason').text else '',
                'unsub_date_time': subscriber.find('unsub_date_time').text,
            }
            subscribers.append(s)
        return subscribers

    def list_add(self, name, list_type):
        '''
        Add a new list, returns new list ID
        types can be: ['public', 'private', 'salesforce']
        '''

        ACCEPTED_TYPES = ['public', 'private', 'salesforce']

        if list_type not in ACCEPTED_TYPES:
            raise AttributeError('List type not in accepted types.')

        data = """
        <system_name>list</system_name>
        <action>add</action>
        <search_type></search_type>
        <search_value></search_value>
        <list_type>%(listtype)s</list_type>
        <list_name><![CDATA[%(name)s]]></list_name>""" % {'listtype': list_type, 'name': name}

        xml_response = self.make_call(data)
        list_id = xml_response.find('.//list_description')

        return list_id.text if list_id != None else None

    def list_delete(self, list_id):
        '''
        Delete a list.
        '''
    
        data = """
        <system_name>list</system_name>
        <action>delete</action>
        <search_type>listid</search_type>
        <search_value>%(listid)s</search_value>""" % {'listid': list_id}

        xml_response = self.make_call(data)
        list_id = xml_response.find('.//list_description')

        return True if list_id != None else False

    def list_rename(self, list_id, name):
        '''
        Rename a list
        '''

        data = """
        <system_name>list</system_name>
        <action>edit</action>
        <search_type>listid</search_type>
        <search_value>%(listid)s</search_value>
        <list_name><![CDATA[%(name)s]]></list_name>""" % {'listid': list_id, 'name': name}

        xml_response = self.make_call(data)
        list_id = xml_response.find('.//list_description')

        return True if list_id != None else False

    def list_retrieve_info(self, list_id):
        '''
        Grab all list info
        '''

        data = """
        <system_name>list</system_name>
        <action>retrieve</action>
        <search_type>listid</search_type>    
        <search_value>%(listid)s</search_value>""" % {'listid': list_id}

        xml_response = self.make_call(data)
        list_element = xml_response.find('.//list')

        if list_element != None:
            info = {
                'list_name': xml_response.find('.//list_name').text,
                'list_type': xml_response.find('.//list_type').text,
                'modified': xml_response.find('.//modified').text,
                'subscriber_count': xml_response.find('.//subscriber_count').text,
                'active_total': xml_response.find('.//active_total').text,
                'held_count': xml_response.find('.//held_count').text,
                'bounce_count': xml_response.find('.//bounce_count').text,
                'unsub_count': xml_response.find('.//unsub_count').text,
            }
            return info
        else:
            return None

    def list_retrieve_list_id_by_name(self, name):
        '''
        Grab a list id by name or partial name search.
        '''

        data = """
        <system_name>list</system_name>
        <action>retrieve</action>
        <search_type>listname</search_type>
        <search_value>%(name)s</search_value>""" % {'name': name}

        xml_response = self.make_call(data)
        list_id = xml_response.find('.//listid')

        return list_id.text if list_id != None else None

    def list_retrieve_all_lists(self):
        '''
        Grab ids of all lists on your account. Return array of ids.
        '''

        data = """
        <system_name>list</system_name>\
        <action>retrieve</action>
        <search_type>listname</search_type>
        <search_value></search_value>"""

        xml_response = self.make_call(data)
        list_ids = xml_response.findall('.//listid')

        return [element.text for element in list_ids]

    def list_retrieve_groups(self):
        '''
        Grab all groups on your account.
        '''

        data = """
        <system_name>list</system_name>
        <action>retrievegroups</action>
        <search_type>groups</search_type>"""

        xml_response = self.make_call(data)

        groups = []
        for group in xml_response.findall('.//group'):
            g = {
                'parent_list_id': group.find('parentlistID').text,
                'group_id': group.find('groupID').text,
                'group_name': group.find('groupName').text,
                'description': (group.find('description').text if 
                                group.find('description') else '')
            }
            groups.append(g)

        return groups

    def list_retrieve_subscribers(self, list_id, status=None):
        '''
        Grab all subcribers from list. Status is optional filter.
        Status can be: ['Active', 'Unsubscribed', 'Returned', 'Undeliverable', 'Deleted']
        '''

        ACCEPTED_STATUS = ['Active', 'Unsubscribed', 'Returned', 'Undeliverable', 'Deleted']

        if status and status not in ACCEPTED_STATUS:
            raise AttributeError('Status not in accepted statuses.')

        if not status:
            data = """
            <system_name>list</system_name>
            <action>retrieve_sub</action>
            <search_type>listid</search_type>
            <search_value>%(listid)s</search_value>""" % {'listid': list_id}
        else:
            data = """
            <system_name>list</system_name>
            <action>retrieve_sub</action>
            <search_type>listid</search_type>
            <search_value>%(listid)s</search_value>
            <search_status>%(status)s</search_status>""" % {'listid': list_id, 'status': status}

        xml_response = self.make_call(data)

        subscribers = []
        for subscriber in xml_response.findall('.//subscriber'):
            s = {}
            for node in subscriber:
                s[node.tag] = node.text if node.text else ''
            subscribers.append(s)
        return subscribers

    def email_html_paste(self, email_name, email_subject, email_body):
        '''
        Creates an HTML email message.

        Message should be well formed and adhere to rules set in: http://docs.code.exacttarget.com/040_XML_API/XML_API_Calls_and_Sample_Code/Email_Management/Email_Add_HTML_Paste
        '''

        data = """
        <system_name>email</system_name>
        <action>add</action>
        <sub_action>HTMLPaste</sub_action>
        <category></category>
        <email_name>%(name)s</email_name>
        <email_subject>%(subject)s</email_subject>
        <email_body><![CDATA[%(body)s]]></email_body>""" % {'name': email_name, 'subject': email_subject, 'body': email_body}

        xml_response = self.make_call(data)

        email_id = xml_response.find('.//emailID')

        return email_id.text if email_id != None else None

    def job_send(self, email_id, list_id, from_name='', from_email='', track_links='true', multipart_mime='false', send_date="immediate", test_send="false"):
        '''
        Sends an email to a subscriber list or group.

        Method restricted here to only sending to a specific list. (Actual API supports multiple.)
        '''

        data = """
        <system_name>job</system_name>
        <action>send</action>
        <search_type>emailid</search_type>
        <search_value>%(emailid)d</search_value>
        <from_name>%(from_name)s</from_name>
        <from_email>%(from_email)s</from_email>
        <additional></additional>
        <multipart_mime>%(multipart_mime)s</multipart_mime>
        <track_links>%(track_links)s</track_links>
        <send_date>%(send_date)s</send_date>
        <send_time></send_time>
        <lists>
            <list>%(listid)d</list>
        </lists>
        <suppress></suppress>
        <test_send>true</test_send>""" % {'emailid': email_id, 'from_name': from_name, 'from_email': from_email, 'multipart_mime': multipart_mime, 'track_links': track_links, 'send_date': send_date, 'listid': list_id}

        xml_response = self.make_call(data)
        job_id = xml_response.find('.//job_description')

        return job_id.text if job_id != None else None

    def make_call(self, data):
        xml = """<?xml version="1.0" ?>
        <exacttarget>
            <authorization>
                <username><![CDATA[%(username)s]]></username>
                <password><![CDATA[%(password)s]]></password>
                </authorization>
                <system>
                    %(data)s
                </system>
        </exacttarget>""" % {'username': self.username, 'password':self.password, 'data': data}

        url = self.api_url
        values = {'xml': xml, 'qf':'xml'}
        data = urllib.urlencode(values)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Content-length": len(data), "Connection": "close"}

        req = urllib2.Request(url, data, headers)

        try:
            # add timeout support for Python 2.6 and lower
            if sys.version_info < (2, 7):
                import socket
                socket.setdefaulttimeout(self.timeout)
                response = urllib2.urlopen(req)
            else:
                response = urllib2.urlopen(req, timeout=self.timeout)
        except urllib2.URLError:
            self.error = "Response timed out";
            raise ConnectionError("Error: %s while waiting for response from ExactTarget (maybe a higher value for timeout is required?)" % self.error)
        
        content = response.read()
        
        try:
            xml_result = etree.XML(content)
        except SyntaxError:
            raise ExactTargetError('Error 39: XML Parse Error')

        response.close()

        #check for error
        if xml_result.find('.//error') != None:
            raise ExactTargetError('Error %s: %s' % (xml_result.find('.//error').text, xml_result.find('.//error_description').text))

        return xml_result
