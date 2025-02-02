import re
import warnings
import xml.etree.ElementTree as ET

class ConfigParse:
    @staticmethod
    def id_extraktion(regex_node, text):
        type = regex_node.find('./id-extraktion/type').text
        if type == "None":
            return [text]
        if type == "Regex":
            res = []
            bug_regex = regex_node.find('./id-extraktion/regex').text
            for bud_ID in re.finditer(bug_regex, text):
                res.append(bud_ID.group(0))
            return res
        elif type == 'Cut':
            regex = regex_node.find('./id-extraktion/regex').text
            search = re.search(regex, text)
            if search:
                f = search.group(0)
                return [text.replace(f, '')]
        else:
            warnings.warn("ID Extraktion type {0} not supported".format(regex_node.find('./id-extraktion/type').text))
        return None
